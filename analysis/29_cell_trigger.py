"""Calibrated cell-level trigger: alert a stand when k ADJACENT 200 m cells are below the alert level at the same time.

Why: stand averages dilute partial losses (stand 18 converted in 2025 and the stand-level alert never fired). Raw per-cell alerts would multiply false alarms,
so the rule must be calibrated to the same budget as the stand-level alert (<= 1 alert episode per stand-year, on the REAL series).
Detectors compared at that equal budget, on the same data:
  STAND  : the stand-level monitor run on the pixel-weighted mean of the stand's cell medians (a proxy of the stand median, so that injected losses reach
           both detectors the same way)
  CELL-k : k = 1, 2, 3 adjacent cells (8-neighbourhood of 200 m blocks, same stand) whose median-of-5 composite z is <= -thr on the same date
Monitor = analysis/23 unchanged (tide-aware robust model, monthly rolling refit, composite of NDVI / NDRE / NDMI z, median of the last 5 observations).
Tests: (1) calibration on the real 2022-2026 series (real events stay in: conservative); (2) the four conversions seen on imagery (stands 5, 9, 12, 18);
(3) semi-synthetic PARTIAL loss on the 20 stands WITHOUT a known change (5, 6, 9, 12, 18 excluded), detection = a NEW alert episode starting after the loss
begins (an episode already running at the start does not count), with a null scenario (no loss) that measures detection by chance: a connected patch of cells covering ~10 % or ~25 % of a stand loses 50 % or 100 % of its canopy cover (linear mixing with bare
values, 60-day ramp, as in analysis/07), random start dates 2022-07 .. end-180 d, detection within 180 days.
Outputs: analysis/data/substand/cell_trigger_results.json, cell_trigger_trials.csv, analysis/29_cell_trigger.md, analysis/29_cell_trigger.png
"""
import json, os, pickle, time, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

src = open("analysis/23_scaleout_monitor.py", encoding="utf-8").read().split("# ---- step 0")[0]; ns = {}; exec(src, ns)
monitor, roll, IDX, T0 = ns["monitor"], ns["roll"], ns["IDX"], ns["T0"]
BARE = {"ndvi": 0.05, "ndre": 0.03, "ndmi": 0.00}; RAMP_D, HORIZON_D, CARRY_D = 60, 180, 20
D = "analysis/data/substand/"; rng = np.random.default_rng(11); t_start = time.time()
meta = pd.read_csv(D + "cells.csv").set_index("cell")
meta["br"], meta["bc"] = (meta.row // 20).astype(int), (meta.col // 20).astype(int)

# ---- series per cell and per stand proxy ------------------------------------------------------------------------------------------------
S = pd.read_csv(D + "cell_stats.csv"); S = S[S["error"].isna()] if "error" in S else S
S = S[S.valid_frac >= 0.5].dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"]); S["date"] = pd.to_datetime(S["date"])
S["stand"] = S.cell.map(meta.stand)
CELL = {}
for c, g in S.groupby("cell"):
    g = g.sort_values("date")
    CELL[c] = dict(t=(g.date - T0).dt.days.values.astype(float), w=g.mndwi_p50.values, ff=g.flooded_frac.values, n=g.n_valid.values,
                   y={i: g[f"{i}_p50"].values for i in IDX}, stand=int(meta.loc[c, "stand"]))


def proxy(stand, override=None):
    """Pixel-weighted mean of the stand's cell medians per date (cells with valid data that date). override: {cell: {idx: injected y}}."""
    rows = []
    for c, s in CELL.items():
        if s["stand"] != stand: continue
        y = {i: (override[c][i] if override and c in override else s["y"][i]) for i in IDX}
        rows.append(pd.DataFrame(dict(t=s["t"], n=s["n"], w=s["w"], ff=s["ff"], **y)))
    d = pd.concat(rows); wsum = d.groupby("t").n.sum()
    m = d[["w", "ff"] + IDX].mul(d.n, axis=0).groupby(d.t).sum().div(wsum, axis=0)
    m = m[wsum.reindex(m.index) >= 0.5 * sum(meta[meta.stand == stand].n_px)]        # enough valid pixels that date
    return dict(t=m.index.values.astype(float), w=m.w.values, ff=m.ff.values, y={i: m[i].values for i in IDX})


def comp_state(s, d_from="2022-01-01", d_to="2026-12-31", y=None):
    """Median-of-5 composite z (the alert state) of one series."""
    y = y or s["y"]; zs = {i: monitor(s, y[i], d_from, d_to) for i in IDX}; t = zs["ndvi"][0]
    if len(t) == 0: return t, t
    return t, roll(np.mean([zs[i][1] for i in IDX], axis=0))


cache = D + "cell_trigger_states.pkl"
if os.path.exists(cache):
    ST_CELL, ST_STAND, PROXY = pickle.load(open(cache, "rb"))
else:
    ST_CELL = {c: comp_state(s) for c, s in CELL.items()}
    PROXY = {k: proxy(k) for k in sorted(meta.stand.unique())}
    ST_STAND = {k: comp_state(p) for k, p in PROXY.items()}
    pickle.dump((ST_CELL, ST_STAND, PROXY), open(cache, "wb"))
print(f"states ready ({time.time() - t_start:.0f}s): {len(ST_CELL)} cells, {len(ST_STAND)} stands")

# ---- per-stand date grid, cell state matrix, adjacency -------------------------------------------------------------------------------------
GRID = {}
for k, (ts, _) in ST_STAND.items():
    cells = [c for c in ST_CELL if CELL[c]["stand"] == k]
    dates = np.unique(np.concatenate([ST_CELL[c][0] for c in cells] + [ts]))
    M = np.full((len(cells), len(dates)), np.nan)
    for r, c in enumerate(cells):
        t, z = ST_CELL[c]
        if len(t) == 0: continue
        j = np.searchsorted(t, dates, side="right") - 1; ok = (j >= 0) & (dates - t[np.clip(j, 0, None)] <= CARRY_D)
        M[r, ok] = z[j[ok]]
    b = meta.loc[cells, ["br", "bc"]].values
    A = ((np.abs(b[:, None, 0] - b[None, :, 0]) <= 1) & (np.abs(b[:, None, 1] - b[None, :, 1]) <= 1)).astype(int); np.fill_diagonal(A, 0)
    GRID[k] = dict(cells=cells, dates=dates, M=M, A=A)


def cell_trigger(M, A, thr, k):
    """Bool per date: a connected group of >= k alerting cells exists (k<=3: a component of size >= 3 always has a node with >= 2 alerting neighbours)."""
    al = np.nan_to_num(M, nan=0.0) <= -thr
    if k == 1: return al.any(0)
    deg = A @ al.astype(int)
    return (al & (deg >= k - 1)).any(0)


def stand_trigger(k, thr, state=None):
    t, z = state or ST_STAND[k]
    return t, (np.nan_to_num(z, nan=0.0) <= -thr)


def n_episodes(t, on):
    n, last = 0, -1e9
    for j in np.nonzero(on)[0]:
        if t[j] - last > 30: n += 1
        last = t[j]
    return n


YEARS = sum((ST_STAND[k][0].max() - ST_STAND[k][0].min()) / 365.25 for k in ST_STAND)
THR = {}
for name in ["STAND", "CELL-1", "CELL-2", "CELL-3"]:
    for thr in np.arange(1.0, 10.01, 0.1):
        if name == "STAND": n = sum(n_episodes(*stand_trigger(k, thr)) for k in ST_STAND)
        else: n = sum(n_episodes(GRID[k]["dates"], cell_trigger(GRID[k]["M"], GRID[k]["A"], thr, int(name[-1]))) for k in GRID)
        if n / YEARS <= 1.0: THR[name] = round(float(thr), 1); break


def union(k, st_state=None, M=None):
    """(t, on) of 'stand alert OR any cell alert' at the UNION thresholds (HALF), on the merged date axis."""
    ts, ons = stand_trigger(k, HALF["STAND"], st_state); G = GRID[k]; oc = cell_trigger(G["M"] if M is None else M, G["A"], HALF["CELL-1"], 1)
    t = np.concatenate([ts, G["dates"]]); on = np.concatenate([ons, oc]); o = np.argsort(t, kind="stable"); return t[o], on[o]



def calib(name, budget):
    for thr in np.arange(1.0, 10.01, 0.1):
        if name == "STAND": n = sum(n_episodes(*stand_trigger(k, thr)) for k in ST_STAND)
        else: n = sum(n_episodes(GRID[k]["dates"], cell_trigger(GRID[k]["M"], GRID[k]["A"], thr, 1)) for k in GRID)
        if n / YEARS <= budget: return round(float(thr), 1)


# UNION = STAND or CELL-1. Both parts get the SAME individual budget b; b is raised until the union itself reaches <= 1 episode per stand-year.
# This uses only the no-injection (false-alarm) side of the data, never the detection results.
for b_ in np.arange(0.50, 1.001, 0.05):
    cand = {"STAND": calib("STAND", b_), "CELL-1": calib("CELL-1", b_)}; HALF = cand
    rate = sum(n_episodes(*union(k)) for k in GRID) / YEARS
    if rate > 1.0: break
    BEST = (dict(cand), round(float(b_), 2), rate)
HALF = BEST[0]


UNION_RATE = sum(n_episodes(*union(k)) for k in GRID) / YEARS
THR["UNION"] = f"stand {HALF['STAND']} or cell {HALF['CELL-1']} (each part calibrated to {BEST[1]} per stand-year)"
print(f"calibrated thresholds (sigma) for <= 1 episode per stand-year over {YEARS:.0f} stand-years:", THR, f"| realised union rate {UNION_RATE:.2f} per stand-year")

# ---- real events ------------------------------------------------------------------------------------------------------------------------------
EVENTS = {5: "2023-02-14", 9: "2023-06-14", 12: "2022-09-01", 18: "2025-02-03"}   # change start: 5, 9 from analysis/21; 12 = after last intact image (4 Aug 2022); 18 from analysis/28
real = {}
for k, d0 in EVENTS.items():
    t0 = (pd.Timestamp(d0) - T0).days; row = {"change_start": d0}
    for name, thr in THR.items():
        if name == "STAND": t, on = stand_trigger(k, thr)
        elif name == "UNION": t, on = union(k)
        else: t, on = GRID[k]["dates"], cell_trigger(GRID[k]["M"], GRID[k]["A"], thr, int(name[-1]))
        hit = np.nonzero(on & (t >= t0) & (t <= t0 + 365))[0]; pre = np.nonzero(on & (t >= t0 - 120) & (t < t0))[0]
        row[name] = (str((T0 + pd.Timedelta(days=float(t[hit[0]]))).date()) + f" (+{int(t[hit[0]] - t0)} d)") if len(hit) else "none within 1 yr"
        row[name + " pre-start"] = "yes" if len(pre) else "no"
    real[k] = row
print("real events (first trigger from the change start, within 1 year; 'pre-start' = any trigger in the 120 days before):"); print(pd.DataFrame(real).T.to_string())

# ---- semi-synthetic partial-loss backtest --------------------------------------------------------------------------------------------------
SCEN = [("null: no loss", 0.10, 0.0), ("patch 10 %, cover -50 %", 0.10, 0.5), ("patch 10 %, cover -100 %", 0.10, 1.0), ("patch 25 %, cover -50 %", 0.25, 0.5),
        ("whole stand, cover -10 %", 1.01, 0.10), ("whole stand, cover -20 %", 1.01, 0.20)]     # uniform loss: every cell
N_T0 = 8; trials = []
EXCLUDE = {5, 6, 9, 12, 18}          # stands with changes seen on imagery: their real alerts would count as chance 'detections'


def onsets(t, on):
    """Dates where a NEW alert episode starts (alerting, and no alerting in the previous 30 days)."""
    j = np.nonzero(on)[0]; keep = [a for n, a in enumerate(j) if n == 0 or t[a] - t[j[n - 1]] > 30]
    return np.array(keep, int)


for k, G in GRID.items():
    if k in EXCLUDE: continue
    cells, A = G["cells"], G["A"]; npx = meta.loc[cells, "n_px"].values; tot = npx.sum()
    t_min, t_max = (pd.Timestamp("2022-07-01") - T0).days, ST_STAND[k][0].max() - HORIZON_D
    for t0 in rng.uniform(t_min, t_max, N_T0):
        seed = rng.integers(len(cells))
        for sname, frac, f in SCEN:
            patch, frontier = [seed], [seed]                                       # grow a connected patch until it covers ~frac of the stand
            while npx[patch].sum() < frac * tot and frontier:
                nb = [j for i in frontier for j in np.nonzero(A[i])[0] if j not in patch]; frontier = []
                for j in rng.permutation(np.unique(nb)) if nb else []:
                    if npx[patch].sum() >= frac * tot: break
                    patch.append(int(j)); frontier.append(int(j))
            d_from = str((T0 + pd.Timedelta(days=t0 - 100)).date()); d_to = str((T0 + pd.Timedelta(days=t0 + HORIZON_D)).date())
            inj = {}
            for r in patch:
                s = CELL[cells[r]]; ramp = np.clip((s["t"] - t0) / RAMP_D, 0, 1)
                inj[cells[r]] = {i: s["y"][i] * (1 - f * ramp) + f * ramp * BARE[i] for i in IDX}
            # cell detector: injected cells re-monitored inside the window, other cells keep their real states
            M = G["M"].copy(); win = (G["dates"] >= t0 - 100) & (G["dates"] <= t0 + HORIZON_D)
            for r in patch:
                t, z = comp_state(CELL[cells[r]], d_from, d_to, y=inj[cells[r]]); M[r, win] = np.nan
                if len(t):
                    j = np.searchsorted(t, G["dates"], side="right") - 1; ok = win & (j >= 0) & (G["dates"] - t[np.clip(j, 0, None)] <= CARRY_D)
                    M[r, ok] = z[j[ok]]
            # stand detector: proxy rebuilt from the injected cells, re-monitored inside the window
            ps = proxy(k, override=inj); st_state = comp_state(ps, d_from, d_to)
            res = dict(stand=k, t0=t0, scenario=sname, patch_cells=len(patch), patch_frac=round(float(npx[patch].sum() / tot), 3))
            for name, thr in THR.items():
                if name == "STAND": t, on = stand_trigger(k, thr, st_state)
                elif name == "UNION": t, on = union(k, st_state, M)
                else: t, on = G["dates"], cell_trigger(M, A, thr, int(name[-1]))
                o = onsets(t, on); o = o[(t[o] >= t0) & (t[o] <= t0 + HORIZON_D)]      # detection = a NEW episode starting after the loss begins
                res[name + "_delay"] = float(t[o[0]] - t0) if len(o) else np.nan
            trials.append(res)
    print(f"  stand {k} done ({time.time() - t_start:.0f}s)", flush=True)
tr = pd.DataFrame(trials); tr.to_csv(D + "cell_trigger_trials.csv", index=False)
summ = {}
for sname, g in tr.groupby("scenario", sort=False):
    summ[sname] = {"n": int(len(g)), "mean_patch_frac": round(float(g.patch_frac.mean()), 3)}
    for name in THR:
        d = g[name + "_delay"]
        summ[sname][name] = dict(within_60d=round(100 * float((d <= 60).mean()), 1), within_180d=round(100 * float(d.notna().mean()), 1),
                                 median_delay_d=None if d.notna().sum() == 0 else round(float(d.median()), 0))
print(json.dumps(summ, indent=1))
json.dump(dict(thresholds=THR, union_rate_per_stand_year=round(UNION_RATE, 2), stand_years=round(YEARS, 1), real_events=real, backtest=summ), open(D + "cell_trigger_results.json", "w"), indent=1)

# ---- figure ------------------------------------------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(15, 4.6)); names = list(THR); x = np.arange(len(SCEN)); wb = 0.8 / len(names)
cols = {"STAND": "#888", "CELL-1": "#9ccfb9", "CELL-2": "#2E8B78", "CELL-3": "#0F2B29", "UNION": "#C8384F"}
for j, n in enumerate(names):
    ax[0].bar(x + j * wb, [summ[s[0]][n]["within_60d"] for s in SCEN], wb, color=cols[n], label=f"{n} ({THR[n]} sigma)")
    ax[1].bar(x + j * wb, [summ[s[0]][n]["within_180d"] for s in SCEN], wb, color=cols[n])
for a, ttl in zip(ax, ("Detected within 60 days (%)", "Detected within 180 days (%)")):
    a.set_xticks(x + 0.4 - wb / 2); a.set_xticklabels([s[0] for s in SCEN], fontsize=9); a.set_title(ttl + " - equal false-alarm budget (<= 1 per stand-year)"); a.set_ylim(0, 100)
ax[0].legend(fontsize=8); plt.tight_layout(); plt.savefig("analysis/29_cell_trigger.png", dpi=90)
print(f"done in {time.time() - t_start:.0f}s")
