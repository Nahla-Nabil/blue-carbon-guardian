"""Scale-out, step 2: run the SAME monitor, unchanged, on stands it has never seen.

The alert thresholds (composite 1.3 sigma etc.) were calibrated on the 25 pilot stands (analysis/07, 08). Here they are applied without re-tuning to
  ADN, ADW : Abu Dhabi blocks north / west of the pilot region (analysis/22)
  TRT      : Saudi Arabia, Tarut Bay (Gulf coast; different Sentinel-2 tile)
Outputs analysis/data/scaleout/scaleout_status.csv, scaleout_episodes.csv, scaleout_summary.json.
Step 0 re-implements the 'condition vs 2020-21 baseline' rule (it existed only inline before) and CHECKS it against the saved pilot table, so the numbers
of the new stands are produced by a verified copy of the pilot logic.
Carbon: only for Abu Dhabi stands (field density measured there: 108 t C/ha, 90 % CI of mean 79-138). NOT computed for Tarut Bay (no field data used).
"""
import glob, json, numpy as np, pandas as pd

IDX = ["ndvi", "ndre", "ndmi"]; THR = {"comp": 1.3}
K_MED, TRAIN_MONTHS, GUARD_D = 5, 36, 90
NOW_DAYS = 365          # 'current condition' = median of the tide-corrected index over the LAST 12 MONTHS (a full seasonal cycle, like the 2-year baseline).
                        # Was 180 d until 2026-09-27: summer is lower than winter (baseline summer-minus-winter NDVI -0.07), so a 6-month, summer-heavy window
                        # biased every stand downwards (median NDVI change -7.5 % vs -0.5 % with 365 d; test: analysis/23b_condition_window_test.py).
T0 = pd.Timestamp("2020-01-01"); DATA_END = pd.Timestamp("2026-09-19"); CO2E = 44 / 12
C = json.load(open("analysis/data/carbon_density_summary.json")); D_LO, D_MID, D_HI = C["ci90_lo"], C["local_mean"], C["ci90_hi"]


def design(t, w=None, ff=None):
    a = 2 * np.pi * t / 365.25
    cols = [np.ones_like(t), t / 365.25, np.sin(a), np.cos(a), np.sin(2 * a), np.cos(2 * a)]
    if w is not None: cols += [w, w ** 2, ff]
    return np.column_stack(cols)


def rfit(X, y, iters=10):
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    for _ in range(iters):
        r = y - X @ beta; s = 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9
        u = np.abs(r) / (1.345 * s); wt = np.sqrt(np.where(u <= 1, 1.0, 1.0 / u))
        beta = np.linalg.lstsq(X * wt[:, None], y * wt, rcond=None)[0]
    r = y - X @ beta
    return beta, 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-9


def monitor(s, y, d_from="2022-01-01", d_to="2026-12-31"):
    t, w = s["t"], s["w"]; ot, oz = [], []
    tf, tt = (pd.Timestamp(d_from) - T0).days, (pd.Timestamp(d_to) - T0).days
    for m in pd.period_range(pd.Timestamp(d_from).to_period("M"), pd.Timestamp(d_to).to_period("M"), freq="M"):
        ms = (m.start_time - T0).days; me = (m.end_time - T0).days
        tr = (t >= ms - TRAIN_MONTHS * 30.44) & (t <= ms - GUARD_D); te = (t >= max(ms, tf)) & (t <= min(me, tt))
        if tr.sum() < 80 or not te.any(): continue
        beta, sig = rfit(design(t[tr], w[tr], s["ff"][tr]), y[tr])
        ot.append(t[te]); oz.append((y[te] - design(t[te], w[te], s["ff"][te]) @ beta) / sig)
    return (np.concatenate(ot), np.concatenate(oz)) if ot else (np.array([]), np.array([]))


def roll(z): return pd.Series(z).rolling(K_MED, min_periods=K_MED).median().values


def analyse(sid, g, area_ha, now_days=NOW_DAYS):
    """Alert episodes + condition vs 2020-21 baseline for one stand."""
    g = g.dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"]); g = g[g.valid_frac >= 0.5].sort_values("date")
    s = dict(t=(g.date - T0).dt.days.values.astype(float), w=g.mndwi_p50.values, ff=g.flooded_frac.values, y={i: g[f"{i}_p50"].values for i in IDX})
    if len(g) < 200: return None, []
    zs = {i: monitor(s, s["y"][i]) for i in IDX}; t = zs["ndvi"][0]
    if len(t) < 50: return None, []
    zc = np.mean([zs[i][1] for i in IDX], axis=0); st = roll(zc); on = st <= -THR["comp"]
    groups = []
    for a in np.nonzero(on)[0]:
        if groups and t[a] - t[groups[-1][-1]] <= 30: groups[-1].append(a)
        else: groups.append([a])
    eps = [dict(stand=sid, start=(T0 + pd.Timedelta(days=t[gi[0]])).date(), end=(T0 + pd.Timedelta(days=t[gi[-1]])).date(), days=int(t[gi[-1]] - t[gi[0]]),
                min_z_comp=round(float(np.nanmin(st[gi])), 2)) for gi in groups]
    row = dict(stand=sid, area_ha=area_ha, n_obs=len(g), last_obs=(T0 + pd.Timedelta(days=t[-1])).date(), alert_now=bool(on[-1]), alerts_2022_2026=len(groups),
               years_monitored=round((t.max() - t.min()) / 365.25, 2))
    raw = {}                                                              # unrounded values: the rule must not act on display rounding
    for i in ("ndvi", "ndmi"):                                            # condition: tide-corrected index now vs 2020-21 baseline
        beta, sig = rfit(design(s["t"], s["w"], s["ff"]), s["y"][i]); X = design(s["t"], s["w"], s["ff"])
        tide = X[:, 6:] @ beta[6:]; ser = s["y"][i] - tide + float(np.mean(tide))
        base = float(np.median(ser[s["t"] < 731])); now = float(np.median(ser[s["t"] >= s["t"][-1] - now_days]))
        raw[i] = (100 * (now - base) / abs(base), (now - base) / sig)
        row.update({f"{i}_base": round(base, 3), f"{i}_now": round(now, 3), f"{i}_change_pct": round(100 * (now - base) / abs(base), 1),
                    f"{i}_change_sigma": round((now - base) / sig, 1)})
    b = lambda i: raw[i]
    if all(b(i)[0] <= -50 for i in ("ndvi", "ndmi")): row["condition"] = "severe decline"
    elif all(b(i)[0] <= -15 and b(i)[1] <= -3 for i in ("ndvi", "ndmi")): row["condition"] = "decline"
    elif all(b(i)[0] >= 15 and b(i)[1] >= 3 for i in ("ndvi", "ndmi")): row["condition"] = "improving"
    else: row["condition"] = "stable"
    return row, eps


# ---- step 0: verify the re-implementation on the pilot ---------------------------------------------------------------
pil = pd.read_csv("analysis/data/s2_stands_stats.csv"); pil["date"] = pd.to_datetime(pil["date"])
ref = pd.read_csv("analysis/data/stand_status.csv").set_index("stand"); ref_ep = pd.read_csv("analysis/data/stand_alert_episodes.csv")
FRESH = "condition" not in ref           # a fresh table from analysis/08 has no condition columns yet: skip the check, write them in step 0b
ref_win = int(ref["condition_window_days"].iloc[0]) if "condition_window_days" in ref else (0 if FRESH else 180)   # window the saved table was built with
chk = []
for k, g in ([] if FRESH else pil.groupby("stand")):
    r, e = analyse(f"P{k}", g, float(ref.loc[k, "area_ha"]), now_days=ref_win)
    chk.append(dict(stand=k, cond_new=r["condition"], cond_ref=ref.loc[k, "condition"], ep_new=r["alerts_2022_2026"], ep_ref=int(ref.loc[k, "alerts_2022_2026"]),
                    d_ndvi_now=round(r["ndvi_now"] - ref.loc[k, "ndvi_now"], 3), d_ndvi_base=round(r["ndvi_base"] - ref.loc[k, "ndvi_base"], 3),
                    d_sigma=round(r["ndvi_change_sigma"] - ref.loc[k, "ndvi_change_sigma"], 1)))
chk = pd.DataFrame(chk, columns=["stand", "cond_new", "cond_ref", "ep_new", "ep_ref", "d_ndvi_now", "d_ndvi_base", "d_sigma"])
if FRESH: print("STEP 0 skipped: stand_status.csv has no condition columns yet (fresh run of analysis/08); step 0b adds them")
else: print("STEP 0 verification on the 25 pilot stands: condition equal", int((chk.cond_new == chk.cond_ref).sum()), "/ 25 | episode counts equal", int((chk.ep_new == chk.ep_ref).sum()),
      "/ 25 | max |d ndvi_now|", chk.d_ndvi_now.abs().max(), "| max |d ndvi_base|", chk.d_ndvi_base.abs().max(), "| max |d sigma|", chk.d_sigma.abs().max())

print(chk[chk.cond_new != chk.cond_ref].to_string(index=False))

# ---- step 0b: bring the pilot table to the current NOW_DAYS definition (condition columns only; alerts/carbon untouched) -----------------------
if ref_win != NOW_DAYS:
    import os, shutil
    if not FRESH and not os.path.exists("analysis/data/stand_status_before_365d.csv"): shutil.copy("analysis/data/stand_status.csv", "analysis/data/stand_status_before_365d.csv")
    upd = ref.copy()
    for k, g in pil.groupby("stand"):
        r, _ = analyse(f"P{k}", g, float(ref.loc[k, "area_ha"]))
        for c in ("ndvi_base", "ndvi_now", "ndvi_change_pct", "ndvi_change_sigma", "ndmi_base", "ndmi_now", "ndmi_change_pct", "ndmi_change_sigma", "condition"):
            upd.loc[k, c] = r[c]
    upd["condition_window_days"] = NOW_DAYS
    upd.reset_index().to_csv("analysis/data/stand_status.csv", index=False)
    print(f"pilot table updated to a {NOW_DAYS}-day 'now' window:", upd.condition.value_counts().to_dict(), "| old copy: analysis/data/stand_status_before_365d.csv")

# ---- new stands ------------------------------------------------------------------------------------------------------
rows, eps_all = [], []
for stats_path in sorted(glob.glob("analysis/data/scaleout/*_stats.csv")):
    grp = stats_path.split("\\")[-1].split("/")[-1].replace("_stats.csv", "")
    st_meta = pd.read_csv(f"analysis/data/scaleout/{grp}_stands.csv").set_index("stand")
    df = pd.read_csv(stats_path); df["date"] = pd.to_datetime(df["date"])
    for sid, g in df.dropna(subset=["stand"]).groupby("stand"):
        r, e = analyse(sid, g, float(st_meta.loc[sid, "area_ha"]))
        if r is None: continue
        r["group"] = grp; r["lon"] = float(st_meta.loc[sid, "lon"]); r["lat"] = float(st_meta.loc[sid, "lat"])
        if grp.startswith("AD"):
            r["stock_tC_p10"], r["stock_tC_p50"], r["stock_tC_p90"] = (round(r["area_ha"] * d) for d in (D_LO, D_MID, D_HI))
        rows.append(r); eps_all += e
res = pd.DataFrame(rows); eps = pd.DataFrame(eps_all)
res.to_csv("analysis/data/scaleout/scaleout_status.csv", index=False); eps.to_csv("analysis/data/scaleout/scaleout_episodes.csv", index=False)
summ = {}
for grp, g in res.groupby("group"):
    yrs = g.years_monitored.sum()
    summ[grp] = dict(stands=int(len(g)), area_ha=round(float(g.area_ha.sum()), 1), stand_years=round(float(yrs), 1), alert_episodes=int(g.alerts_2022_2026.sum()),
                     episodes_per_stand_year=round(float(g.alerts_2022_2026.sum() / yrs), 2), active_alerts=int(g.alert_now.sum()),
                     conditions=g.condition.value_counts().to_dict())
pil_yrs = 25 * 4.7
summ["pilot_reference"] = dict(stands=25, episodes_per_stand_year=round(len(ref_ep) / pil_yrs, 2))
json.dump(summ, open("analysis/data/scaleout/scaleout_summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
pd.set_option("display.width", 250)
print(res[res.condition != "stable"][["stand", "group", "area_ha", "condition", "ndvi_change_pct", "ndvi_change_sigma", "ndmi_change_pct", "alerts_2022_2026"]].to_string(index=False))
print("top by alert episodes:"); print(res.sort_values("alerts_2022_2026", ascending=False).head(8)[["stand", "group", "area_ha", "alerts_2022_2026", "condition", "ndvi_change_pct"]].to_string(index=False))
