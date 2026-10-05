"""Feasibility spike #2: is the Sentinel-2 red-edge time series over Abu Dhabi mangroves clean enough
to build an early-warning signal on?

Steps
 1. Find the densest ~3 km cell of ESA WorldCover-2021 mangrove (class 95) inside the Abu Dhabi box.
 2. Pull Sentinel-2 L2A (one MGRS tile, 2020-2026) for that cell straight from the cloud (no downloads).
 3. Per date: cloud-mask with SCL, keep interior mangrove pixels, compute NDVI and NDRE statistics.
 4. Remove the seasonal cycle (monthly medians) and report the noise left over, i.e. the smallest
    decline we could hope to detect.

Requires: pystac-client, planetary-computer, rasterio, scipy, numpy, matplotlib
"""
import time, concurrent.futures as cf
import numpy as np, pystac_client, planetary_computer as pc, rasterio
from rasterio.merge import merge
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import Window, from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, shape
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BOX = [54.30, 24.35, 54.70, 24.65]          # Abu Dhabi mangrove box (same as spike #1)
CELL = 0.03                                  # ~3 km analysis cell
PERIOD = "2020-01-01/2026-09-19"
TIME_BUDGET_S = 420                          # stop reading after this many seconds, use what we have
OUT_PNG = "analysis/02_s2_timeseries_spike.png"

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)

# ---- 1. densest mangrove cell -------------------------------------------------------------------------
wc_items = list(cat.search(collections=["esa-worldcover"], bbox=BOX, datetime="2021-01-01/2021-12-31").items())
arr, tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=BOX)
mang = arr[0] == 95
best, best_n = None, -1
lon = BOX[0]
while lon < BOX[2] - 1e-9:
    lat = BOX[1]
    while lat < BOX[3] - 1e-9:
        r0, c0 = rasterio.transform.rowcol(tr, lon, lat + CELL)      # top-left pixel
        r1, c1 = rasterio.transform.rowcol(tr, lon + CELL, lat)      # bottom-right pixel
        n = int(mang[max(r0, 0):r1, max(c0, 0):c1].sum())
        if n > best_n:
            best, best_n = [lon, lat, lon + CELL, lat + CELL], n
        lat += CELL
    lon += CELL
aoi = best
print(f"AOI cell {np.round(aoi, 3)} -> {best_n * 0.01:.0f} ha of WorldCover mangrove")

wc_arr, wc_tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=aoi)
wc_mang = (wc_arr[0] == 95).astype("uint8")

# ---- 2. Sentinel-2 scenes (one tile only, so one observation per date) ------------------------------------
found = list(cat.search(collections=["sentinel-2-l2a"], bbox=aoi, datetime=PERIOD,
                        query={"eo:cloud_cover": {"lt": 40}}).items())
full = [i for i in found if shape(i.geometry).contains(box(*aoi))]
tiles = {}
for i in full:
    tiles.setdefault(i.properties["s2:mgrs_tile"], []).append(i)
tile, items = max(tiles.items(), key=lambda kv: len(kv[1]))
items.sort(key=lambda i: i.datetime)
print(f"{len(found)} scenes intersect, using tile {tile}: {len(items)} scenes with <40% scene cloud")

# grid definition from the first scene (all scenes of one tile share the same grid)
with rasterio.open(items[0].assets["B04"].href) as ds:
    crs = ds.crs
    w = from_bounds(*transform_bounds("EPSG:4326", crs, *aoi), ds.transform)
    WIN = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height)))
    win_tr = ds.window_transform(WIN)
H, W = int(WIN.height), int(WIN.width)

# WorldCover mask on the Sentinel-2 grid, shrunk by 1 px so edge (mixed) pixels are dropped
mask = np.zeros((H, W), "uint8")
reproject(wc_mang, mask, src_transform=wc_tr, src_crs="EPSG:4326", dst_transform=win_tr, dst_crs=crs,
          resampling=Resampling.nearest)
mask = ndi.binary_erosion(mask.astype(bool), iterations=1)
print(f"interior mangrove pixels on the 10 m grid: {mask.sum()} ({mask.sum() * 0.01:.0f} ha)")


def read_band(href, native_window_from_bounds=True):
    """read the AOI window of one band, resampled (nearest) to the 10 m grid"""
    with rasterio.open(href) as ds:
        b = transform_bounds("EPSG:4326", ds.crs, *aoi)
        win = from_bounds(*b, ds.transform)
        win = Window(int(round(win.col_off)), int(round(win.row_off)),
                     max(int(round(win.width)), 1), max(int(round(win.height)), 1))
        return ds.read(1, window=win, out_shape=(H, W), resampling=Resampling.nearest).astype("float32")


def process(item):
    """-> (date, valid fraction, NDVI median, NDVI p75, NDRE median, NDRE p75) over interior mangrove pixels"""
    try:
        a = item.assets
        b04, b08, b05, b8a = (read_band(a[k].href) for k in ("B04", "B08", "B05", "B8A"))
        scl = read_band(a["SCL"].href)
        # processing baseline >= 04.00 (since Jan 2022) adds a +1000 offset to the digital numbers
        off = 1000.0 if float(item.properties.get("s2:processing_baseline", "4.0")) >= 4.0 else 0.0
        r = lambda x: np.clip((x - off) / 10000.0, 0, None)
        red, nir, re1, nir2 = r(b04), r(b08), r(b05), r(b8a)
        ok = mask & ~np.isin(scl, [0, 1, 3, 8, 9, 10, 11])          # no nodata/saturated/shadow/cloud/cirrus/snow
        vf = ok.sum() / max(mask.sum(), 1)
        if ok.sum() < 30:
            return item.datetime.date(), vf, *([np.nan] * 4)
        ndvi = (nir - red) / (nir + red + 1e-6)
        ndre = (nir2 - re1) / (nir2 + re1 + 1e-6)
        return (item.datetime.date(), vf, np.median(ndvi[ok]), np.percentile(ndvi[ok], 75),
                np.median(ndre[ok]), np.percentile(ndre[ok], 75))
    except Exception as e:                                          # one bad scene must not stop the run
        return item.datetime.date(), 0.0, *([np.nan] * 4)


# ---- 3. read all scenes in parallel (bounded by a time budget) ---------------------------------------------
t0, rows = time.time(), []
with cf.ThreadPoolExecutor(12) as ex:
    futs = [ex.submit(process, it) for it in items]
    for f in cf.as_completed(futs, timeout=None):
        rows.append(f.result())
        if time.time() - t0 > TIME_BUDGET_S:
            for g in futs: g.cancel()
            break
rows.sort(key=lambda r: r[0])
print(f"read {len(rows)}/{len(items)} scenes in {time.time() - t0:.0f} s")

dates = np.array([r[0] for r in rows]); vf = np.array([r[1] for r in rows])
vals = np.array([r[2:] for r in rows], dtype=float)                 # ndvi_med, ndvi_p75, ndre_med, ndre_p75
good = (vf >= 0.5) & np.isfinite(vals).all(axis=1)
print(f"scenes with >=50% clean mangrove pixels: {good.sum()}  (per year: " +
      str({y: int(sum(1 for d, g in zip(dates, good) if g and d.year == y)) for y in range(2020, 2027)}) + ")")

# ---- 4. seasonal cycle and residual noise -------------------------------------------------------------------
names = ["NDVI median", "NDVI p75", "NDRE median", "NDRE p75"]
months = np.array([d.month for d in dates])
fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
print(f"\n{'series':12s} {'seasonal range':>15s} {'noise (robust sd)':>18s} {'range/noise':>12s}")
for k, name in enumerate(names):
    v = vals[:, k]
    clim = {m: np.nanmedian(v[good & (months == m)]) for m in range(1, 13) if (good & (months == m)).sum() >= 3}
    anom = np.array([v[j] - clim[months[j]] if (good[j] and months[j] in clim) else np.nan for j in range(len(v))])
    a = anom[np.isfinite(anom)]
    noise = 1.4826 * np.median(np.abs(a - np.median(a)))
    rng = max(clim.values()) - min(clim.values())
    print(f"{name:12s} {rng:15.3f} {noise:18.3f} {rng / noise:12.1f}")
    if name in ("NDVI p75", "NDRE p75"):
        axes[0].plot(np.array(dates)[good], v[good], ".", ms=4, label=name)
        axes[1].plot(np.array(dates), anom, ".", ms=4, label=f"{name} anomaly (noise sd {noise:.3f})")
axes[0].set_title(f"Abu Dhabi mangroves, interior pixels ({mask.sum() * 0.01:.0f} ha) - Sentinel-2, tile {tile}")
axes[1].axhline(0, color="k", lw=.6)
axes[0].legend(); axes[1].legend(); axes[1].set_xlabel("date")
axes[0].set_ylabel("index value"); axes[1].set_ylabel("value minus monthly median")
plt.tight_layout(); plt.savefig(OUT_PNG, dpi=110)
print("saved", OUT_PNG)
