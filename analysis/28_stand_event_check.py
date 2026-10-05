"""Check a candidate event inside one stand: is the partial decline flagged by the 200 m cells real, and when did it start?

Usage: python analysis/28_stand_event_check.py <stand>          e.g.  python analysis/28_stand_event_check.py 12
1. IMAGERY: same-season (May-Sep), low-tide Sentinel-2 true colour in 2020, 2023 and 2026 (identical reflectance stretch); the stand's cells are outlined,
   flagged cells (decline / severe decline) in red, the others in white.
2. ONSET: paired series 'flagged cells minus stable cells of the same stand' (pixel-weighted median per date, NDVI and NDMI, from analysis/25 cell stats);
   shared tide / season / sensor effects cancel. Constant-ramp-constant fit as in analysis/21 (90 % interval from a 300-draw residual bootstrap, approximate).
3. ALERTS: first cell alert and first stand-level alert from 90 days before the fitted start.
Outputs: analysis/figures/stand<k>_event_check.png, analysis/data/stand<k>_event_check.json
"""
import sys, json, numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.warp import transform_bounds, Resampling
from rasterio.windows import Window, from_bounds
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

K = int(sys.argv[1]); rng = np.random.default_rng(7); T0 = pd.Timestamp("2020-01-01")
g = json.load(open("analysis/data/grid.json")); H, W, REGION = g["H"], g["W"], g["region"]
cells = np.load("analysis/data/substand/cells.npy"); cst = pd.read_csv("analysis/data/substand/cell_status.csv")
mine = cst[cst.stand == K]; bad = mine[mine.condition.isin(["decline", "severe decline"])].cell.tolist(); good = mine[mine.condition == "stable"].cell.tolist()
print(f"stand {K}: {len(mine)} cells, flagged {len(bad)} ({mine[mine.cell.isin(bad)].area_ha.sum():.1f} ha), stable {len(good)}")

# ---- 2. onset from the cell series ------------------------------------------------------------------------------------------------------
S = pd.read_csv("analysis/data/substand/cell_stats.csv", usecols=["date", "cell", "valid_frac", "n_valid", "ndvi_p50", "ndmi_p50"])
S = S[S.cell.isin(bad + good) & (S.valid_frac >= 0.5)].dropna(subset=["ndvi_p50", "ndmi_p50"]); S["date"] = pd.to_datetime(S["date"])
S["grp"] = np.where(S.cell.isin(bad), "flagged", "stable")


def wmed(x, idx):                                              # pixel-weighted median of cell medians
    o = np.argsort(x[idx].values); v = x[idx].values[o]; w = x["n_valid"].values[o]; c = np.cumsum(w); return v[np.searchsorted(c, c[-1] / 2)]


def ramp_fit(t, y, grid, boot=0):
    def best(yv):
        b = (np.inf,)
        for i, t1 in enumerate(grid):
            for t2 in grid[i + 1:]:
                r = np.clip((t - t1) / (t2 - t1), 0, 1); B = np.stack([1 - r, r], 1); coef = np.linalg.lstsq(B, yv, rcond=None)[0]
                sse = float(((B @ coef - yv) ** 2).sum())
                if sse < b[0]: b = (sse, t1, t2, coef[0], coef[1])
        return b
    sse, t1, t2, a, bb = best(y); r = np.clip((t - t1) / (t2 - t1), 0, 1); fit = a * (1 - r) + bb * r; res = y - fit
    draws = np.array([best(fit + rng.choice(res, len(res)))[1] for _ in range(boot)]) if boot else np.array([])
    return t1, t2, a, bb, draws


day = lambda x: T0 + pd.Timedelta(days=float(x))
out = dict(stand=K, flagged_cells=bad, flagged_ha=round(float(mine[mine.cell.isin(bad)].area_ha.sum()), 1), onset={})
fig = plt.figure(figsize=(15, 9.5)); gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 1])
for j, idx in enumerate(("ndvi", "ndmi")):
    p = {gname: gg.groupby("date").apply(lambda x: wmed(x, idx + "_p50")) for gname, gg in S.groupby("grp")}
    d = (p["flagged"] - p["stable"]).dropna().sort_index(); t = (d.index - T0).days.values.astype(float)
    t1, t2, a, bb, draws = ramp_fit(t, d.values, np.arange(0, t.max() - 60, 30.0), boot=300); lo, hi = np.percentile(draws, [5, 95])
    out["onset"][idx] = dict(level_before=round(a, 3), level_after=round(bb, 3), start=str(day(t1).date()), start_90ci=[str(day(lo).date()), str(day(hi).date())], ramp_end=str(day(t2).date()))
    ax = fig.add_subplot(gs[1, j]); ax.plot(d.index, d.values, ".", ms=3, color="#557"); r = np.clip((t - t1) / (t2 - t1), 0, 1); ax.plot(d.index, a * (1 - r) + bb * r, "r-", lw=2)
    ax.axvspan(day(lo), day(hi), color="orange", alpha=.25); ax.set_title(f"Stand {K}: {idx.upper()} flagged cells minus stable cells (ramp fit; orange = 90 % CI of start)", fontsize=9)

# ---- 3. alerts ---------------------------------------------------------------------------------------------------------------------------
ce = pd.read_csv("analysis/data/substand/cell_episodes.csv", parse_dates=["start"]); se = pd.read_csv("analysis/data/stand_alert_episodes.csv", parse_dates=["start"])
t1 = pd.Timestamp(out["onset"]["ndmi"]["start"]); win = t1 - pd.Timedelta(days=90)
fc = ce[ce.cell.isin(bad) & (ce.start >= win)].sort_values("start"); fs = se[(se.stand == K) & (se.start >= win)].sort_values("start")
out["first_cell_alert"] = str(fc.start.iloc[0].date()) if len(fc) else None; out["first_stand_alert"] = str(fs.start.iloc[0].date()) if len(fs) else None
out["cell_alerts_before_window"] = sorted({str(x.date()) for x in ce[ce.cell.isin(bad) & (ce.start < win)].start})
ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
ax.text(0, 1, "\n".join([f"Stand {K}: {len(bad)} of {len(mine)} cells flagged ({out['flagged_ha']} ha)",
                         f"Change start (NDMI): {out['onset']['ndmi']['start']}  [{out['onset']['ndmi']['start_90ci'][0]} .. {out['onset']['ndmi']['start_90ci'][1]}]",
                         f"Change start (NDVI): {out['onset']['ndvi']['start']}  [{out['onset']['ndvi']['start_90ci'][0]} .. {out['onset']['ndvi']['start_90ci'][1]}]",
                         f"Ramp ends (NDMI): {out['onset']['ndmi']['ramp_end']}",
                         f"First cell alert from start-90 d: {out['first_cell_alert']}", f"First stand alert from start-90 d: {out['first_stand_alert']}"]),
        va="top", fontsize=10, family="monospace")

# ---- 1. imagery ------------------------------------------------------------------------------------------------------------------------
s = pd.read_csv("analysis/data/s2_stands_stats.csv"); s = s[s.valid_frac >= 0.95].dropna(subset=["mndwi_p50"])
dd = s.groupby(["date", "id"]).agg(w=("mndwi_p50", "median"), n=("stand", "nunique")).reset_index(); dd = dd[(dd.n >= 20) & dd.date.str[5:7].isin(["05", "06", "07", "08", "09"])]
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
ys, xs = np.nonzero(np.isin(cells, mine.cell.values)); y0, y1, x0, x1 = max(ys.min() - 25, 0), min(ys.max() + 26, H), max(xs.min() - 25, 0), min(xs.max() + 26, W)
for c, yr in enumerate((2020, 2023, 2026)):
    item = pc.sign(cat.get_collection("sentinel-2-l2a").get_item(dd[dd.date.str[:4] == str(yr)].sort_values("w").iloc[0]["id"]))
    off = 1000.0 if float(item.properties.get("s2:processing_baseline", "4")) >= 4 else 0.0; bands = []
    for b in ("B04", "B03", "B02"):
        with rasterio.open(item.assets[b].href) as ds:
            w = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
            w = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height)))
            bands.append((ds.read(1, window=w, out_shape=(H, W), resampling=Resampling.nearest).astype("float32") - off) / 10000.0)
    img = np.clip(np.stack(bands, -1)[y0:y1, x0:x1] / 0.25, 0, 1) ** 0.8; cc = cells[y0:y1, x0:x1]
    ax = fig.add_subplot(gs[0, c]); ax.imshow(img); ax.axis("off")
    ax.contour(np.isin(cc, good).astype(float), levels=[.5], colors="white", linewidths=.8); ax.contour(np.isin(cc, bad).astype(float), levels=[.5], colors="red", linewidths=1.4)
    ax.set_title(f"Stand {K}, {item.datetime.date()} (red = flagged cells)", fontsize=10)
plt.tight_layout(); plt.savefig(f"analysis/figures/stand{K}_event_check.png", dpi=85)
json.dump(out, open(f"analysis/data/stand{K}_event_check.json", "w"), indent=1); print(json.dumps(out, indent=1))

# ---- 4. yearly sequence zoomed on the flagged cells (one driest May-Sep date per year) --------------------------------------------------
ys, xs = np.nonzero(np.isin(cells, bad)); y0, y1, x0, x1 = max(ys.min() - 30, 0), min(ys.max() + 31, H), max(xs.min() - 30, 0), min(xs.max() + 31, W)
KEY = [int(y) for y in sys.argv[2].split(",")] if len(sys.argv) > 2 else [2020, 2023, 2026]     # key years for the large panel figure
fig, axs = plt.subplots(1, 7, figsize=(24, 4.2)); crops = {}
for a, yr in zip(axs, range(2020, 2027)):
    item = pc.sign(cat.get_collection("sentinel-2-l2a").get_item(dd[dd.date.str[:4] == str(yr)].sort_values("w").iloc[0]["id"]))
    off = 1000.0 if float(item.properties.get("s2:processing_baseline", "4")) >= 4 else 0.0; bands = []
    for b in ("B04", "B03", "B02"):
        with rasterio.open(item.assets[b].href) as ds:
            w = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
            w = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height)))
            bands.append((ds.read(1, window=w, out_shape=(H, W), resampling=Resampling.nearest).astype("float32") - off) / 10000.0)
    crops[yr] = (np.clip(np.stack(bands, -1)[y0:y1, x0:x1] / 0.25, 0, 1) ** 0.8, str(item.datetime.date())); a.imshow(crops[yr][0]); a.axis("off")
    a.contour(np.isin(cells[y0:y1, x0:x1], bad).astype(float), levels=[.5], colors="red", linewidths=1.2); a.set_title(str(item.datetime.date()), fontsize=10)
plt.tight_layout(); plt.savefig(f"analysis/figures/stand{K}_yearly.png", dpi=80); print("saved yearly sequence")

fig, axs = plt.subplots(1, len(KEY), figsize=(5.2 * len(KEY), 4.6))
for a, yr in zip(axs, KEY):
    a.imshow(crops[yr][0]); a.axis("off"); a.contour(np.isin(cells[y0:y1, x0:x1], bad).astype(float), levels=[.5], colors="red", linewidths=1.6)
    a.set_title(crops[yr][1], fontsize=13)
plt.tight_layout(); plt.savefig(f"analysis/figures/stand{K}_key_years.png", dpi=90); print("saved key-years figure", KEY)
