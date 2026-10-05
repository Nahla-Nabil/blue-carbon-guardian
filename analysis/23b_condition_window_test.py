# Seasonal-bias test of the CONDITION layer: 'now' = last 180 d (current) vs last 365 d (a full seasonal cycle), baseline = 2020-21 (two full cycles)
import glob, numpy as np, pandas as pd
src = open("analysis/23_scaleout_monitor.py", encoding="utf-8").read().split("# ---- step 0")[0]; ns = {}; exec(src, ns)
design, rfit, T0, IDX = ns["design"], ns["rfit"], ns["T0"], ns["IDX"]
frames = []
p = pd.read_csv("analysis/data/s2_stands_stats.csv"); p["stand"] = "P" + p["stand"].astype(str); frames.append(p)
for f in glob.glob("analysis/data/scaleout/*_stats.csv"): frames.append(pd.read_csv(f))
df = pd.concat(frames); df["date"] = pd.to_datetime(df["date"])
rows = []
for sid, g in df.dropna(subset=["stand"]).groupby("stand"):
    g = g.dropna(subset=[f"{i}_p50" for i in IDX] + ["mndwi_p50", "flooded_frac"]); g = g[g.valid_frac >= 0.5].sort_values("date")
    if len(g) < 200: continue
    t = (g.date - T0).dt.days.values.astype(float); w = g.mndwi_p50.values; ff = g.flooded_frac.values
    row = dict(stand=sid)
    for i in ("ndvi", "ndmi"):
        y = g[f"{i}_p50"].values; beta, sig = rfit(design(t, w, ff), y); X = design(t, w, ff); tide = X[:, 6:] @ beta[6:]; ser = y - tide + tide.mean()
        base = np.median(ser[t < 731])
        for win in (180, 365):
            now = np.median(ser[t >= t[-1] - win]); row[f"{i}_pct_{win}"] = 100 * (now - base) / abs(base); row[f"{i}_sig_{win}"] = (now - base) / sig
        # seasonal amplitude check: median of May-Sep minus median of Oct-Apr in the baseline years
        m = g.date.dt.month.values; b = t < 731
        row[f"{i}_summer_minus_winter"] = np.median(ser[b & (m >= 5) & (m <= 9)]) - np.median(ser[b & ((m >= 10) | (m <= 4))])
    def cls(w):
        c = lambda i: (row[f"{i}_pct_{w}"], row[f"{i}_sig_{w}"])
        if all(c(i)[0] <= -50 for i in ("ndvi", "ndmi")): return "severe decline"
        if all(c(i)[0] <= -15 and c(i)[1] <= -3 for i in ("ndvi", "ndmi")): return "decline"
        if all(c(i)[0] >= 15 and c(i)[1] >= 3 for i in ("ndvi", "ndmi")): return "improving"
        return "stable"
    row["cond_180"], row["cond_365"] = cls(180), cls(365); rows.append(row)
r = pd.DataFrame(rows)
print("stands:", len(r))
print("median NDVI change % (all stands): 180 d", round(r.ndvi_pct_180.median(), 1), "| 365 d", round(r.ndvi_pct_365.median(), 1))
print("median NDMI change % (all stands): 180 d", round(r.ndmi_pct_180.median(), 1), "| 365 d", round(r.ndmi_pct_365.median(), 1))
print("baseline summer minus winter (tide-corrected), median: NDVI", round(r.ndvi_summer_minus_winter.median(), 3), "NDMI", round(r.ndmi_summer_minus_winter.median(), 3))
print(pd.crosstab(r.cond_180, r.cond_365))
print(r[(r.cond_180 != "stable") | (r.cond_365 != "stable")][["stand", "cond_180", "cond_365", "ndvi_pct_180", "ndvi_pct_365", "ndvi_sig_365", "ndmi_pct_365", "ndmi_sig_365"]].round(1).to_string(index=False))
r.to_csv("analysis/data/condition_window_test.csv", index=False)
