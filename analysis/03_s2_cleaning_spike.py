"""Spike #3: can we clean the Sentinel-2 mangrove series enough to trust it?

Fixes tested (problems found in spike #2):
  a) duplicate scenes per date (reprocessed items)  -> keep one per date (newest processing baseline)
  b) processing-baseline offset artefact            -> compare both baselines on the SAME dates
  c) tide / flooded pixels                          -> MNDWI-based flooded fraction, drop scenes above a threshold
  d) outliers                                       -> robust stats (percentiles) + rolling median

Per-scene statistics are saved to analysis/data/ so nobody has to re-download imagery.
Requires: pystac-client, planetary-computer, rasterio, scipy, numpy, pandas, matplotlib
"""
import os, time, concurrent.futures as cf
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.merge import merge
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import Window, from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, shape
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AOI = [54.45, 24.53, 54.48, 24.56]           # densest Abu Dhabi mangrove cell found in spike #2
TILE = "40RBN"
PERIOD = "2020-01-01/2026-09-19"
ALT_WINDOW = ("2021-07-01", "2022-06-30")    # duplicates around the baseline change, used for the artefact test
TIME_BUDGET_S = 480
CSV = "analysis/data/s2_abudhabi_cell_stats.csv"
OUT_PNG = "analysis/03_s2_cleaning_spike.png"
os.makedirs("analysis/data", exist_ok=True)

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)

# ---- WorldCover mangrove mask ---------------------------------------------------------------------------
wc_items = list(cat.search(collections=["esa-worldcover"], bbox=AOI, datetime="2021-01-01/2021-12-31").items())
wc_arr, wc_tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=AOI)
wc_mang = (wc_arr[0] == 95).astype("uint8")

# ---- scenes: one per date, plus the "other" duplicates for the artefact test ---------------------------------
found = list(cat.search(collections=["sentinel-2-l2a"], bbox=AOI, datetime=PERIOD,
                        query={"eo:cloud_cover": {"lt": 40}}).items())
found = [i for i in found if i.properties["s2:mgrs_tile"] == TILE and shape(i.geometry).contains(box(*AOI))]
bl = lambda i: float(i.properties.get("s2:processing_baseline", "4.0"))
by_date = {}
for i in found:
    by_date.setdefault(i.datetime.date(), []).append(i)
primary, alt = [], []
for d, lst in by_date.items():
    lst.sort(key=bl, reverse=True)
    primary.append(lst[0])
    if ALT_WINDOW[0] <= str(d) <= ALT_WINDOW[1]:
        alt += lst[1:]
print(f"{len(found)} scenes -> {len(primary)} distinct dates; {len(alt)} duplicate scenes kept for the offset test")

with rasterio.open(primary[0].assets["B04"].href) as ds:
    crs = ds.crs
    w = from_bounds(*transform_bounds("EPSG:4326", crs, *AOI), ds.transform)
    WIN = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height)))
    win_tr = ds.window_transform(WIN)
H, W = int(WIN.height), int(WIN.width)
mask = np.zeros((H, W), "uint8")
reproject(wc_mang, mask, src_transform=wc_tr, src_crs="EPSG:4326", dst_transform=win_tr, dst_crs=crs,
          resampling=Resampling.nearest)
mask = ndi.binary_erosion(mask.astype(bool), iterations=1)          # interior mangrove pixels only
print("interior mangrove pixels:", int(mask.sum()))


def read_band(href):
    with rasterio.open(href) as ds:
        win = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *AOI), ds.transform)
        win = Window(int(round(win.col_off)), int(round(win.row_off)),
                     max(int(round(win.width)), 1), max(int(round(win.height)), 1))
        return ds.read(1, window=win, out_shape=(H, W), resampling=Resampling.nearest).astype("float32")


def stats(prefix, x):
    p = np.percentile(x, [10, 25, 50, 75, 90])
    return {f"{prefix}_p{q}": v for q, v in zip([10, 25, 50, 75, 90], p)}


def process(item, is_alt=False):
    base = dict(date=str(item.datetime.date()), id=item.id, baseline=bl(item), alt=is_alt,
                scene_cloud=item.properties.get("eo:cloud_cover"))
    try:
        a = item.assets
        off = 1000.0 if bl(item) >= 4.0 else 0.0                     # baseline >= 04.00 adds +1000 to the DN
        rd = lambda k: np.clip((read_band(a[k].href) - off) / 10000.0, 0, None)
        green, red, re1, nir, nir2, swir = (rd(k) for k in ("B03", "B04", "B05", "B08", "B8A", "B11"))
        scl = read_band(a["SCL"].href)
        ok = mask & ~np.isin(scl, [0, 1, 3, 8, 9, 10, 11])
        base["valid_frac"] = ok.sum() / max(mask.sum(), 1)
        if ok.sum() < 30:
            return base
        idx = {"ndvi": (nir - red) / (nir + red + 1e-6),
               "ndre": (nir2 - re1) / (nir2 + re1 + 1e-6),
               "ndmi": (nir2 - swir) / (nir2 + swir + 1e-6),          # canopy/soil moisture proxy
               "mndwi": (green - swir) / (green + swir + 1e-6)}       # water (tide) proxy
        for k, v in idx.items():
            base.update(stats(k, v[ok]))
        base["flooded_frac"] = float((idx["mndwi"][ok] > 0).mean())
    except Exception as e:
        base["error"] = repr(e)[:80]
    return base


t0, rows = time.time(), []
jobs = [(i, False) for i in primary] + [(i, True) for i in alt]
with cf.ThreadPoolExecutor(16) as ex:
    futs = [ex.submit(process, i, a) for i, a in jobs]
    for f in cf.as_completed(futs):
        rows.append(f.result())
        if time.time() - t0 > TIME_BUDGET_S:
            for g in futs: g.cancel()
            break
df = pd.DataFrame(rows).sort_values(["date", "baseline"]).reset_index(drop=True)
df.to_csv(CSV, index=False)
print(f"read {len(df)}/{len(jobs)} scenes in {time.time() - t0:.0f} s -> {CSV}")

# ---- (b) offset artefact test: same date, both baselines -------------------------------------------------
d_alt = df[df.alt].dropna(subset=["ndvi_p50"])
pairs = []
for d, g in df.dropna(subset=["ndvi_p50"]).groupby("date"):
    if g.alt.any() and (~g.alt).any():
        old, new = g[g.baseline < 4].iloc[0:1], g[g.baseline >= 4].iloc[0:1]
        if len(old) and len(new):
            pairs.append((new.ndvi_p50.iloc[0] - old.ndvi_p50.iloc[0], new.ndre_p50.iloc[0] - old.ndre_p50.iloc[0]))
if pairs:
    p = np.array(pairs)
    print(f"\nOFFSET TEST on {len(p)} dates with both baselines: median (new - old) NDVI p50 = {np.median(p[:, 0]):+.4f}, "
          f"NDRE p50 = {np.median(p[:, 1]):+.4f}   (0 means the +1000 offset handling is right)")
else:
    print("\nOFFSET TEST: no dates with both baselines found")

# ---- (a,c,d) noise before / after cleaning ----------------------------------------------------------------------
d = df[~df.alt].copy()
d["date"] = pd.to_datetime(d["date"])
d = d.dropna(subset=["ndvi_p50"]).sort_values("date").reset_index(drop=True)
d["month"] = d.date.dt.month


def noise(frame, col):
    f = frame.copy()
    clim = f.groupby("month")[col].transform("median")
    a = (f[col] - clim).to_numpy()
    single = 1.4826 * np.median(np.abs(a - np.median(a)))
    smooth = pd.Series(a, index=f.date).rolling("45D", min_periods=3).median().dropna().to_numpy()
    sm = 1.4826 * np.median(np.abs(smooth - np.median(smooth)))
    rng = f.groupby("month")[col].median().agg(lambda s: s.max() - s.min())
    return single, sm, rng, len(f)


print(f"\n{'filter':34s} {'n':>4s} | " + " | ".join(f"{c:>26s}" for c in ["ndvi_p50", "ndre_p50", "ndmi_p50"]))
print(f"{'':34s} {'':>4s} | " + " | ".join(f"{'sd single/45d-smooth, range':>26s}" for _ in range(3)))
variants = {"raw (>=50% valid px)": d[d.valid_frac >= .5]}
for t in (0.20, 0.10, 0.05):
    variants[f"+ flooded_frac < {t}"] = d[(d.valid_frac >= .5) & (d.flooded_frac < t)]
for name, f in variants.items():
    cells = []
    for c in ["ndvi_p50", "ndre_p50", "ndmi_p50"]:
        s, sm, rng, n = noise(f, c)
        cells.append(f"{s:6.3f} / {sm:6.3f}, {rng:6.3f}")
    print(f"{name:34s} {len(f):4d} | " + " | ".join(f"{c:>26s}" for c in cells))

# ---- drift check on the cleaned series ---------------------------------------------------------------------------
clean = variants["+ flooded_frac < 0.1"]
print("\nannual median (cleaned):")
print(clean.groupby(clean.date.dt.year)[["ndvi_p50", "ndre_p50", "ndmi_p50", "flooded_frac"]].median().round(3))

fig, ax = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
for c, col in zip(["ndvi_p50", "ndre_p50", "ndmi_p50"], ["tab:green", "tab:orange", "tab:blue"]):
    ax[0].plot(d.date, d[c], ".", color="lightgray", ms=3)
    ax[0].plot(clean.date, clean[c], ".", color=col, ms=4, label=c)
ax[0].legend(); ax[0].set_title("Abu Dhabi mangrove cell: grey = all scenes, colour = after flooded-scene filter")
ax[1].plot(d.date, d.flooded_frac, ".", ms=3); ax[1].axhline(0.1, color="r", lw=.7); ax[1].set_ylabel("flooded fraction (tide proxy)")
ax[2].plot(clean.date, clean.ndre_p50 - clean.groupby("month").ndre_p50.transform("median"), ".", ms=4)
ax[2].axhline(0, color="k", lw=.6); ax[2].set_ylabel("NDRE p50 anomaly (cleaned)")
plt.tight_layout(); plt.savefig(OUT_PNG, dpi=110); print("saved", OUT_PNG)
