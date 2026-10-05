"""Sub-stand monitoring, step 2: the same monitor and condition rule per 200 m cell, then three checks.

Monitor and rule are imported unchanged from analysis/23_scaleout_monitor.py (tide-aware robust model, monthly rolling refit, median-of-5 composite alert
at 1.3 sigma, condition = last 365 days vs 2020-21 with unrounded thresholds).
Checks
  1. AGREEMENT with the independent epoch-difference indicator (analysis/12: 2021 vs 2025 low-tide composites). Per cell: share of its pixels flagged 'loss'.
     'changed' reference cell = >= 50 % flagged, 'unchanged' = < 5 %. NOT ground truth: both use Sentinel-2, but different methods (time series vs two composites).
  2. TIMING on the two confirmed events: first alert of the changed cells of stands 5 and 9 vs the stand-level alert and the dated onset (analysis/21).
  3. COST: alert episodes per cell-year, and how many stands would carry at least one 'decline' cell with no support from the epoch-difference indicator.
Outputs: analysis/data/substand/cell_status.csv, cell_episodes.csv, substand_summary.json, analysis/26_substand.png
"""
import json, numpy as np, pandas as pd, rasterio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

src = open("analysis/23_scaleout_monitor.py", encoding="utf-8").read().split("# ---- step 0")[0]; ns = {}; exec(src, ns)
analyse, NOW_DAYS = ns["analyse"], ns["NOW_DAYS"]
D = "analysis/data/substand/"
meta = pd.read_csv(D + "cells.csv").set_index("cell"); cells = np.load(D + "cells.npy")
S = pd.read_csv(D + "cell_stats.csv"); S = S[S["error"].isna()] if "error" in S else S; S["date"] = pd.to_datetime(S["date"])

# ---- per-cell monitor + condition -----------------------------------------------------------------------------------------------
rows, eps = [], []
for c, g in S.groupby("cell"):
    r, e = analyse(int(c), g, float(meta.loc[c, "n_px"]) * 0.01)
    if r is None: continue
    r["cell"] = int(c); r["stand"] = int(meta.loc[c, "stand"])           # analyse() stores the id it was given in 'stand': keep it as 'cell'
    rows.append(r); eps += e
st = pd.DataFrame(rows)
ep = pd.DataFrame(eps).rename(columns={"stand": "cell"})

# ---- 1. agreement with the epoch-difference indicator ------------------------------------------------------------------------------
chg = rasterio.open("analysis/data/change_indicator_2021_2025.tif").read(1)
loss_frac = pd.Series(np.bincount(cells.ravel(), weights=(chg == 1).ravel(), minlength=cells.max() + 1) /
                      np.maximum(np.bincount(cells.ravel(), minlength=cells.max() + 1), 1))
st["loss_frac_epoch"] = st.cell.map(loss_frac)
flagged = st.condition.isin(["severe decline", "decline"])
ref_chg, ref_unc = st.loss_frac_epoch >= 0.5, st.loss_frac_epoch < 0.05
tp = int((flagged & ref_chg).sum()); fn = int((~flagged & ref_chg).sum()); fp = int((flagged & ref_unc).sum()); tn = int((~flagged & ref_unc).sum())
agree = dict(changed_cells=int(ref_chg.sum()), unchanged_cells=int(ref_unc.sum()), grey_cells=int((~ref_chg & ~ref_unc).sum()),
             flagged_of_changed=f"{tp}/{tp + fn}", flagged_of_unchanged=f"{fp}/{fp + tn}",
             flagged_cells_total=int(flagged.sum()), flagged_by_stand=st[flagged].groupby("stand").size().to_dict())
print("CHECK 1 - agreement with epoch-difference indicator:", json.dumps(agree))

# ---- 2. timing on stands 5 and 9 ---------------------------------------------------------------------------------------------------
onset = pd.read_csv("analysis/data/onset_results.csv")
stand_ep = pd.read_csv("analysis/data/stand_alert_episodes.csv", parse_dates=["start"])
timing = {}
ep["start"] = pd.to_datetime(ep["start"])
for k in (5, 9):
    ch = st[(st.stand == k) & (st.loss_frac_epoch >= 0.5)].cell
    o = onset[(onset.stand == k) & (onset["index"] == "ndmi")].iloc[0]
    t1 = pd.Timestamp(o.onset_t1)
    e = ep[ep.cell.isin(ch) & (ep.start >= t1 - pd.Timedelta(days=120))].sort_values("start")
    se = stand_ep[(stand_ep.stand == k) & (stand_ep.start >= t1 - pd.Timedelta(days=120))].sort_values("start")
    first_cell = e.start.iloc[0] if len(e) else pd.NaT
    timing[k] = dict(changed_cells=int(len(ch)), onset_ndmi=str(t1.date()), first_cell_alert=str(first_cell.date()) if pd.notna(first_cell) else None,
                     cells_alerting_within_180d=int(e[e.start <= t1 + pd.Timedelta(days=180)].cell.nunique()),
                     stand_level_alert=str(se.start.iloc[0].date()) if len(se) else None,
                     cell_condition_counts=st[st.cell.isin(ch)].condition.value_counts().to_dict(),
                     stand_cells_condition=st[st.stand == k].condition.value_counts().to_dict())
print("CHECK 2 - timing:", json.dumps(timing, indent=1))

# ---- 3. cost -----------------------------------------------------------------------------------------------------------------------------
yrs = st.years_monitored.sum()
unsupported = st[flagged & (st.loss_frac_epoch < 0.05)]
cost = dict(cells=int(len(st)), cell_years=round(float(yrs), 1), alert_episodes_per_cell_year=round(float(st.alerts_2022_2026.sum() / yrs), 2),
            flagged_cells_without_epoch_support=int(len(unsupported)), stands_with_unsupported_flag=sorted(unsupported.stand.unique().tolist()),
            unsupported_area_ha=round(float(unsupported.area_ha.sum()), 1))
print("CHECK 3 - cost:", json.dumps(cost))

st.to_csv(D + "cell_status.csv", index=False); ep.to_csv(D + "cell_episodes.csv", index=False)
json.dump(dict(agreement=agree, timing=timing, cost=cost, now_days=NOW_DAYS), open(D + "substand_summary.json", "w"), indent=1, default=str)

# ---- figure: cell condition map + stands 5/9 zoom ------------------------------------------------------------------------------------
code = {"stable": 1, "improving": 2, "decline": 3, "severe decline": 4}
img = np.zeros(cells.shape, "int8"); lut = np.zeros(cells.max() + 1, "int8"); lut[st.cell.values] = st.condition.map(code).values; img = lut[cells]
cmap = ListedColormap(["#ffffff", "#9ccfb9", "#4f8fd1", "#f2a33a", "#c8384f"])
fig, ax = plt.subplots(1, 3, figsize=(18, 6.2))
ax[0].imshow(img, cmap=cmap, vmin=0, vmax=4, interpolation="nearest"); ax[0].set_title("Cell condition (200 m): green stable, orange decline, red severe")
ax[1].imshow(np.where(cells > 0, chg == 1, np.nan), cmap="Reds", interpolation="nearest"); ax[1].set_title("Independent epoch-difference loss pixels (2021 vs 2025)")
for a in ax[:2]: a.axis("off")
m = st.loss_frac_epoch
for lab, sel, col in (("flagged by cell monitor", flagged, "#c8384f"), ("not flagged", ~flagged, "#9ccfb9")):
    ax[2].hist(m[sel], bins=np.linspace(0, 1, 21), alpha=.8, color=col, label=lab)
ax[2].set_yscale("log"); ax[2].set_xlabel("share of the cell flagged by the epoch-difference indicator"); ax[2].set_ylabel("cells (log)"); ax[2].legend()
ax[2].set_title("Do the two independent methods agree?")
plt.tight_layout(); plt.savefig("analysis/26_substand.png", dpi=85); print("saved analysis/26_substand.png")
