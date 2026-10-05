"""Module 2 data build: per-STAND Sentinel-2 time series for the densest Abu Dhabi mangrove region.

What it does
  1. finds the densest ~13 x 10 km block of WorldCover-2021 mangrove inside the Abu Dhabi box
  2. turns mangrove patches (>= 3 ha) into "stands" (connected components), keeps the interior pixels only
  3. for every Sentinel-2 date (tile 40RBN, 2020-2026, one scene per date) reads 7 bands straight from the cloud,
     masks clouds with SCL, and stores robust per-stand statistics of NDVI, NDRE, NDMI and MNDWI (tide/wetness proxy)
  4. saves everything to CSV so the tide correction, anomaly detection and dashboard never need to re-download imagery

Run time is long (tens of minutes); results are written incrementally. Requires: pystac-client, planetary-computer,
rasterio, scipy, numpy, pandas, shapely
"""
import os, time, concurrent.futures as cf
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.merge import merge
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import Window, from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, shape

BOX = [54.30, 24.35, 54.70, 24.65]
BLOCK = (0.12, 0.09)                      # region size in degrees (lon, lat) ~ 13 km x 10 km
MIN_STAND_HA, MAX_STANDS = 3.0, 25
PERIOD, TILE = "2020-01-01/2026-09-19", "40RBN"
TIME_BUDGET_S = 50 * 60
OUT_DIR = "analysis/data"; os.makedirs(OUT_DIR, exist_ok=True)
STATS_CSV, STANDS_CSV = f"{OUT_DIR}/s2_stands_stats.csv", f"{OUT_DIR}/stands.csv"

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)

# ---- 1. densest region ------------------------------------------------------------------------------------
wc_items = list(cat.search(collections=["esa-worldcover"], bbox=BOX, datetime="2021-01-01/2021-12-31").items())
arr, tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=BOX)
mang_all = arr[0] == 95
best, best_n = None, -1
for lon in np.arange(BOX[0], BOX[2] - BLOCK[0] + 1e-9, 0.03):
    for lat in np.arange(BOX[1], BOX[3] - BLOCK[1] + 1e-9, 0.03):
        r0, c0 = rasterio.transform.rowcol(tr, lon, lat + BLOCK[1]); r1, c1 = rasterio.transform.rowcol(tr, lon + BLOCK[0], lat)
        n = int(mang_all[max(r0, 0):r1, max(c0, 0):c1].sum())
        if n > best_n:
            best, best_n = [float(lon), float(lat), float(lon + BLOCK[0]), float(lat + BLOCK[1])], n
REGION = best
print("region", np.round(REGION, 3), f"{best_n * 0.01:.0f} ha mangrove")
wc_arr, wc_tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=REGION)
mang = wc_arr[0] == 95

# ---- 2. stands ---------------------------------------------------------------------------------------------------
lab, n = ndi.label(mang)
area_ha = np.bincount(lab.ravel())[1:] * 0.01
keep = [i + 1 for i in np.argsort(-area_ha) if area_ha[i] >= MIN_STAND_HA][:MAX_STANDS]
print(f"{len(keep)} stands >= {MIN_STAND_HA} ha (largest {area_ha.max():.0f} ha)")
stand_lab = np.zeros_like(lab, dtype="uint16")
for k, l in enumerate(keep, start=1):
    stand_lab[lab == l] = k

# ---- scenes (one per date, newest processing baseline) -------------------------------------------------------
found = list(cat.search(collections=["sentinel-2-l2a"], bbox=REGION, datetime=PERIOD, query={"eo:cloud_cover": {"lt": 40}}).items())
found = [i for i in found if i.properties["s2:mgrs_tile"] == TILE and shape(i.geometry).contains(box(*REGION))]
bl = lambda i: float(i.properties.get("s2:processing_baseline", "4.0"))
by_date = {}
for i in found:
    by_date.setdefault(i.datetime.date(), []).append(i)
scenes = sorted((sorted(v, key=bl, reverse=True)[0] for v in by_date.values()), key=lambda i: i.datetime)
print(f"{len(scenes)} distinct dates")

with rasterio.open(scenes[0].assets["B04"].href) as ds:
    crs = ds.crs
    w = from_bounds(*transform_bounds("EPSG:4326", crs, *REGION), ds.transform)
    WIN = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height)))
    win_tr = ds.window_transform(WIN)
H, W = int(WIN.height), int(WIN.width)
labels = np.zeros((H, W), "uint16")
reproject(stand_lab, labels, src_transform=wc_tr, src_crs="EPSG:4326", dst_transform=win_tr, dst_crs=crs, resampling=Resampling.nearest)
stand_px, meta = {}, []
for k in range(1, len(keep) + 1):
    m = ndi.binary_erosion(labels == k, iterations=1)                    # interior pixels only
    if m.sum() >= 50:
        stand_px[k] = m
        ys, xs = np.nonzero(labels == k)
        lon, lat = rasterio.transform.xy(win_tr, ys.mean(), xs.mean())
        clon, clat = rasterio.warp.transform(crs, "EPSG:4326", [lon], [lat])
        meta.append(dict(stand=k, area_ha=round(float((stand_lab == k).sum() * 0.01), 1), interior_px=int(m.sum()), lon=clon[0], lat=clat[0]))
pd.DataFrame(meta).to_csv(STANDS_CSV, index=False)
print(len(stand_px), "stands with >= 50 interior pixels ->", STANDS_CSV, f"| grid {H}x{W}")


def read_band(href):
    with rasterio.open(href) as ds:
        win = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
        win = Window(int(round(win.col_off)), int(round(win.row_off)), max(int(round(win.width)), 1), max(int(round(win.height)), 1))
        return ds.read(1, window=win, out_shape=(H, W), resampling=Resampling.nearest).astype("float32")


def process(item):
    rows = []
    try:
        a = item.assets
        off = 1000.0 if bl(item) >= 4.0 else 0.0                          # baseline >= 04.00 adds +1000 to the DN
        rd = lambda k: np.clip((read_band(a[k].href) - off) / 10000.0, 0, None)
        green, red, re1, nir, nir2, swir = (rd(k) for k in ("B03", "B04", "B05", "B08", "B8A", "B11"))
        scl = read_band(a["SCL"].href)
        good = ~np.isin(scl, [0, 1, 3, 8, 9, 10, 11])
        idx = {"ndvi": (nir - red) / (nir + red + 1e-6), "ndre": (nir2 - re1) / (nir2 + re1 + 1e-6),
               "ndmi": (nir2 - swir) / (nir2 + swir + 1e-6), "mndwi": (green - swir) / (green + swir + 1e-6)}
        for k, m in stand_px.items():
            ok = m & good
            row = dict(date=str(item.datetime.date()), id=item.id, baseline=bl(item), stand=k, valid_frac=ok.sum() / m.sum())
            if ok.sum() >= 30:
                for name, v in idx.items():
                    p = np.percentile(v[ok], [25, 50, 75])
                    row.update({f"{name}_p25": p[0], f"{name}_p50": p[1], f"{name}_p75": p[2]})
                row["flooded_frac"] = float((idx["mndwi"][ok] > 0).mean())
            rows.append(row)
    except Exception as e:
        rows.append(dict(date=str(item.datetime.date()), id=item.id, error=repr(e)[:80]))
    return rows


t0, allrows, done = time.time(), [], 0
with cf.ThreadPoolExecutor(12) as ex:
    futs = [ex.submit(process, s) for s in scenes]
    for f in cf.as_completed(futs):
        allrows += f.result(); done += 1
        if done % 25 == 0:
            pd.DataFrame(allrows).to_csv(STATS_CSV, index=False)
            print(f"  {done}/{len(scenes)} scenes, {time.time() - t0:.0f} s", flush=True)
        if time.time() - t0 > TIME_BUDGET_S:
            print("time budget reached, stopping"); [g.cancel() for g in futs]; break
pd.DataFrame(allrows).sort_values(["date", "stand"]).to_csv(STATS_CSV, index=False)
print(f"DONE: {done}/{len(scenes)} scenes in {time.time() - t0:.0f} s -> {STATS_CSV}")
