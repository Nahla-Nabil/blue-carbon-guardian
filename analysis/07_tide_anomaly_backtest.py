"""Module 2: tide-aware anomaly detection + semi-synthetic backtest on the 25 Abu Dhabi mangrove stands.

1. TIDE CORRECTION: per stand and index, robust regression on trend + 2 seasonal harmonics + tide terms (MNDWI, MNDWI^2, flooded fraction).
2. MONITORING (CCDC-like): every month, refit on a rolling window [t-36 months, t-3 months] (3-month guard so a fresh decline is not
   absorbed); z = (observed - predicted) / robust sigma; alert when the median z of the last 5 observations <= -threshold.
3. FALSE ALARMS: threshold calibrated on the REAL series (no injection) to <= 1 alert episode per stand-year.
4. SEMI-SYNTHETIC BACKTEST: inject a canopy-COVER loss of f = 5/10/20 % (linear mixing with a bare-ground value, ramped over 60 days) at random
   dates and measure how often / how fast each detector (NDVI, NDRE, NDMI, composite) raises the alert.
ASSUMPTIONS (state them in the report): bare-ground index values NDVI 0.05, NDRE 0.03, NDMI 0.00; this is a cover-loss scenario, NOT a
physiological (chlorophyll) stress scenario, so it cannot show any red-edge advantage for leaf stress.
Three configurations are compared: A linear tide term (all scenes), B quadratic tide + flooded fraction (all scenes), C = B + causal dry-scene rule.
Outputs: analysis/data/backtest_trials_<config>.csv, analysis/07_summary.md, analysis/07_backtest.png
"""
import time, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

t_start = time.time()
IDX = ["ndvi", "ndre", "ndmi"]; BARE = {"ndvi": 0.05, "ndre": 0.03, "ndmi": 0.00}
K_MED, TRAIN_MONTHS, GUARD_D, MONITOR_FROM = 5, 36, 90, "2022-01-01"
FRACS, N_INJ, RAMP_D, HORIZON_D = [0.05, 0.10, 0.20], 12, 60, 180
NL = chr(10)

df = pd.read_csv("analysis/data/s2_stands_stats.csv"); df["date"] = pd.to_datetime(df["date"])
df = df.dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"]); df = df[df.valid_frac >= 0.5].sort_values(["stand", "date"])
T0 = pd.Timestamp("2020-01-01")
S = {}
for k, g in df.groupby("stand"):
    S[k] = dict(t=(g.date - T0).dt.days.values.astype(float), w=g.mndwi_p50.values, ff=g.flooded_frac.values, y={i: g[f"{i}_p50"].values for i in IDX})
print(f"{len(S)} stands, {len(df)} observations")

CFG = dict(tide="quad_ff", dry=False)          # overwritten per configuration below


def design(t, w=None, ff=None, tide=None):
    tide = tide or CFG["tide"]
    yrs = t / 365.25; a = 2 * np.pi * t / 365.25
    cols = [np.ones_like(t), yrs, np.sin(a), np.cos(a), np.sin(2 * a), np.cos(2 * a)]
    if w is not None and tide in ("linear", "quad", "quad_ff"): cols.append(w)
    if w is not None and tide in ("quad", "quad_ff"): cols.append(w ** 2)
    if w is not None and tide == "quad_ff": cols.append(ff)
    return np.column_stack(cols)


def rfit(X, y, iters=10):
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    for _ in range(iters):
        r = y - X @ beta; s = 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9
        u = np.abs(r) / (1.345 * s); wt = np.sqrt(np.where(u <= 1, 1.0, 1.0 / u))
        beta = np.linalg.lstsq(X * wt[:, None], y * wt, rcond=None)[0]
    r = y - X @ beta
    return beta, 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9


# ---- 1. in-sample noise with / without the tide terms --------------------------------------------------------------
noise = {i: [] for i in IDX}
for k, s in S.items():
    for i in IDX:
        _, s0 = rfit(design(s["t"], tide="none"), s["y"][i]); _, s1 = rfit(design(s["t"], s["w"], s["ff"], tide="quad_ff"), s["y"][i])
        noise[i].append((s0, s1))
noise_tab = pd.DataFrame({i: {"without_tide_term": np.mean([a for a, _ in v]), "with_tide_terms": np.mean([b for _, b in v])} for i, v in noise.items()}).T
noise_tab["reduction_%"] = 100 * (1 - noise_tab.with_tide_terms / noise_tab.without_tide_term)
print(NL + "Robust residual sd (mean over 25 stands):" + NL, noise_tab.round(4))


# ---- 2. monitoring -----------------------------------------------------------------------------------------------------
def monitor(s, y, d_from, d_to):
    """z-scores for observations with d_from <= t <= d_to, using monthly refits on a rolling window."""
    t, w = s["t"], s["w"]; out_t, out_z = [], []
    tf, tt = (pd.Timestamp(d_from) - T0).days, (pd.Timestamp(d_to) - T0).days
    for m in pd.period_range(pd.Timestamp(d_from).to_period("M"), pd.Timestamp(d_to).to_period("M"), freq="M"):
        ms = (m.start_time - T0).days; me = (m.end_time - T0).days
        tr = (t >= ms - TRAIN_MONTHS * 30.44) & (t <= ms - GUARD_D)
        te = (t >= max(ms, tf)) & (t <= min(me, tt))
        if CFG["dry"] and tr.sum() >= 80:                              # causal dry-scene rule: 60th percentile of the TRAINING window
            q = np.quantile(w[tr], 0.6); tr = tr & (w <= q); te = te & (w <= q)
        if tr.sum() < 80 or not te.any(): continue
        beta, sig = rfit(design(t[tr], w[tr], s["ff"][tr]), y[tr])
        out_t.append(t[te]); out_z.append((y[te] - design(t[te], w[te], s["ff"][te]) @ beta) / sig)
    return (np.concatenate(out_t), np.concatenate(out_z)) if out_t else (np.array([]), np.array([]))


def alert_state(z):
    return pd.Series(z).rolling(K_MED, min_periods=K_MED).median().values


def episodes(t, st, thr):
    on = (st <= -thr); n, last = 0, -1e9
    for j in np.nonzero(on)[0]:
        if t[j] - last > 30: n += 1
        last = t[j]
    return n


CONFIGS = {"A_linear_tide_all": dict(tide="linear", dry=False), "B_quad+flooded_all": dict(tide="quad_ff", dry=False),
           "C_quad+flooded_dry60": dict(tide="quad_ff", dry=True)}
ALL = {}
for cname, cfg in CONFIGS.items():
    CFG.update(cfg); rng = np.random.default_rng(7)
    print(NL + f"######## CONFIG {cname}")
    real_z = {}; years = 0.0
    for k, s in S.items():
        zs = {i: monitor(s, s["y"][i], MONITOR_FROM, "2026-12-31") for i in IDX}
        t = zs["ndvi"][0]; real_z[k] = (t, {**{i: zs[i][1] for i in IDX}, "comp": np.mean([zs[i][1] for i in IDX], axis=0)}); years += (t.max() - t.min()) / 365.25
    print(f"monitored {years:.0f} stand-years on real series ({time.time() - t_start:.0f}s)")
    THR = {}
    for name in IDX + ["comp"]:
        for thr in np.arange(1.0, 8.01, 0.1):
            n = sum(episodes(real_z[k][0], alert_state(real_z[k][1][name]), thr) for k in S)
            if n / years <= 1.0: THR[name] = round(float(thr), 1); break
    print("  thresholds (sigma) for <=1 alert episode per stand-year:", THR)

    trials = []
    for k, s in S.items():
        t_min, t_max = (pd.Timestamp("2022-07-01") - T0).days, (s["t"].max() - HORIZON_D)
        for t0 in np.sort(rng.uniform(t_min, t_max, N_INJ)):
            d_from = T0 + pd.Timedelta(days=t0 - 100); d_to = T0 + pd.Timedelta(days=t0 + HORIZON_D)
            for f in FRACS:
                ramp = np.clip((s["t"] - t0) / RAMP_D, 0, 1)
                zs = {i: monitor(s, s["y"][i] * (1 - f * ramp) + f * ramp * BARE[i], d_from, d_to) for i in IDX}
                t = zs["ndvi"][0]
                if len(t) < K_MED + 3: continue
                zz = {**{i: zs[i][1] for i in IDX}, "comp": np.mean([zs[i][1] for i in IDX], axis=0)}
                for name, z in zz.items():
                    st = alert_state(z); hit = np.nonzero((st <= -THR[name]) & (t >= t0))[0]
                    trials.append(dict(stand=k, t0=t0, frac=f, detector=name, detected=len(hit) > 0, delay_d=(t[hit[0]] - t0) if len(hit) else np.nan))
    tr = pd.DataFrame(trials); tr.to_csv(f"analysis/data/backtest_trials_{cname}.csv", index=False)
    summ = tr.groupby(["frac", "detector"]).agg(n=("detected", "size"), detected_pct=("detected", lambda x: 100 * x.mean()),
                                                  median_delay_days=("delay_d", "median"),
                                                  p90_delay_days=("delay_d", lambda x: np.nanpercentile(x, 90) if x.notna().any() else np.nan)).round(1)
    d60 = tr.assign(within60=tr.detected & (tr.delay_d <= 60)).groupby(["frac", "detector"]).within60.mean().mul(100).round(1).rename("detected_within_60d_pct")
    summ = summ.join(d60); ALL[cname] = (summ, dict(THR), years)
    print(summ.to_string()); print(f"({time.time() - t_start:.0f}s)")

cmp = pd.concat([v[0].assign(config=c).reset_index() for c, v in ALL.items()])
print(NL + "=== COMPARISON: detected within 60 days (%) ===")
print(cmp.pivot_table(index=["frac", "detector"], columns="config", values="detected_within_60d_pct").round(1).to_string())
print(NL + "=== COMPARISON: median detection delay (days) ===")
print(cmp.pivot_table(index=["frac", "detector"], columns="config", values="median_delay_days").round(1).to_string())

with open("analysis/07_summary.md", "w", encoding="utf-8") as fh:
    fh.write("# Module 2 results (semi-synthetic backtest)" + NL + NL + "## Noise (robust residual sd, mean of 25 stands)" + NL + noise_tab.round(4).to_markdown() + NL + NL)
    for cname, (sm, th, yrs) in ALL.items():
        fh.write(f"## {cname}  (thresholds, sigma: {th}; {yrs:.0f} stand-years)" + NL + sm.to_markdown() + NL + NL)
    fh.write("Assumptions: bare values NDVI .05 / NDRE .03 / NDMI .00; canopy-COVER-loss scenario only (not leaf-chlorophyll stress)." + NL)

fig, ax = plt.subplots(1, 3, figsize=(15, 4.3))
noise_tab[["without_tide_term", "with_tide_terms"]].plot.bar(ax=ax[0], rot=0); ax[0].set_title("Residual noise: tide terms off vs on"); ax[0].set_ylabel("robust sd")
best = max(ALL, key=lambda c: ALL[c][0].xs(0.10, level="frac").detected_within_60d_pct.mean())
for d, c in zip(IDX + ["comp"], ["tab:green", "tab:orange", "tab:blue", "k"]):
    x = ALL[best][0].xs(d, level="detector"); ax[1].plot(x.index * 100, x.detected_within_60d_pct, "o-", color=c, label=d); ax[2].plot(x.index * 100, x.median_delay_days, "o-", color=c, label=d)
ax[1].set_title(f"Detected within 60 days (%) - {best}"); ax[1].set_xlabel("canopy-cover loss (%)"); ax[1].legend(); ax[2].set_title("Median detection delay (days)"); ax[2].set_xlabel("canopy-cover loss (%)")
plt.tight_layout(); plt.savefig("analysis/07_backtest.png", dpi=110)
print(f"best config by mean detection within 60 d at 10 %: {best}; done in {time.time() - t_start:.0f}s")
