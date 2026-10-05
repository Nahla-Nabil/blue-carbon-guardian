"""Scale-out, step 1: per-stand Sentinel-2 series for NEW blocks that the 25-stand pilot never saw (unseen-data test + "scalable across the Gulf").

Usage:  python analysis/22_scaleout_fetch.py <name> <lon0> <lat0> <lon1> <lat1> [exclude_pilot_region=1] [mgrs_tile]
  e.g.  python analysis/22_scaleout_fetch.py ADN 54.51 24.56 54.63 24.65 1     (Abu Dhabi, north of the pilot block)
        python analysis/22_scaleout_fetch.py TRT 49.93 26.65 50.05 26.74 0     (Saudi Arabia, Tarut Bay, Gulf coast)
Same recipe as analysis/05_stand_series.py: ESA WorldCover-2021 mangrove patches >= 3 ha become stands (interior pixels only, >= 50 px), every clean
Sentinel-2 L2A date 2020-2026 is read straight from the cloud (no downloads), SCL cloud mask, robust per-stand NDVI / NDRE / NDMI / MNDWI + flooded fraction.
Stands that touch the pilot region (analysis/data/dashboard_data.json 'region') are excluded so that no pilot stand is counted twice.
Outputs (analysis/data/scaleout/): <name>_stats.csv, <name>_stands.csv, <name>_stands.geojson
"""
import os, sys, time, json, concurrent.futures as cf
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.features import shapes
from rasterio.merge import merge
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import Window, from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, shape, mapping

name = sys.argv[1]; REGION = [float(x) for x in sys.argv[2:6]]; excl = (sys.argv[6] == "1") if len(sys.argv) > 6 else False
TILE = sys.argv[7] if len(sys.argv) > 7 else None          # optional MGRS tile filter (keeps one radiometric/geometric family, like the pilot)
MIN_STAND_HA, PERIOD = 3.0, "2020-01-01/2026-09-19"
OUT = "analysis/data/scaleout"; os.makedirs(OUT, exist_ok=True)
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)

# ---- stands from WorldCover ----------------------------------------------------------------------------------------
wc_items = list(cat.search(collections=["esa-worldcover"], bbox=REGION, datetime="2021-01-01/2021-12-31").items())
wc_arr, wc_tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=REGION)
mang = wc_arr[0] == 95
lab, n = ndi.label(mang)
area_ha = np.bincount(lab.ravel())[1:] * 0.01
drop = set()
if excl:
    P = json.load(open("analysis/data/dashboard_data.json"))["region"]
    r0, c0 = rasterio.transform.rowcol(wc_tr, P[0], P[3]); r1, c1 = rasterio.transform.rowcol(wc_tr, P[2], P[1])
    sub = lab[max(r0, 0):max(r1, 0), max(c0, 0):max(c1, 0)]
    drop = set(np.unique(sub[sub > 0]).tolist())
keep = [i + 1 for i in np.argsort(-area_ha) if area_ha[i] >= MIN_STAND_HA and (i + 1) not in drop]
print(f"{name}: {len(keep)} stands >= {MIN_STAND_HA} ha ({sum(area_ha[k - 1] for k in keep):.0f} ha); excluded {len(drop)} patches touching the pilot region")
stand_lab = np.zeros_like(lab, dtype="uint16")
for k, l in enumerate(keep, start=1):
    stand_lab[lab == l] = k
feats = []
for geom, v in shapes(stand_lab.astype("int32"), mask=stand_lab > 0, transform=wc_tr):
    feats.append(dict(type="Feature", properties=dict(stand=f"{name}{int(v)}"), geometry=geom))
json.dump(dict(type="FeatureCollection", features=feats), open(f"{OUT}/{name}_stands.geojson", "w"))

# ---- scenes ----------------------------------------------------------------------------------------------------------
found = list(cat.search(collections=["sentinel-2-l2a"], bbox=REGION, datetime=PERIOD, query={"eo:cloud_cover": {"lt": 40}}).items())
found = [i for i in found if shape(i.geometry).contains(box(*REGION)) and (TILE is None or i.properties['s2:mgrs_tile'] == TILE)]
bl = lambda i: float(i.properties.get("s2:processing_baseline", "4.0"))
by_date = {}
for i in found:
    by_date.setdefault(i.datetime.date(), []).append(i)
scenes = sorted((sorted(v, key=bl, reverse=True)[0] for v in by_date.values()), key=lambda i: i.datetime)
print(len(scenes), "distinct dates; tiles:", sorted({s.properties['s2:mgrs_tile'] for s in scenes}))

# per-tile grids can differ (UTM zone / tile offset), so every scene is read straight into the WorldCover-labelled window of ITS OWN CRS
def grid_for(item):
    with rasterio.open(item.assets["B04"].href) as ds:
        w = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
        win = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height)))
        return ds.crs, win, ds.window_transform(win)
_grid_cache = {}


def get_masks(item):
    """Interior-pixel masks per stand on the scene's grid (cached per CRS + window offset)."""
    crs, win, tr = grid_for(item); key = (str(crs), win.col_off, win.row_off, win.width, win.height)
    if key not in _grid_cache:
        H, W = int(win.height), int(win.width); labels = np.zeros((H, W), "uint16")
        reproject(stand_lab, labels, src_transform=wc_tr, src_crs="EPSG:4326", dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)
        _grid_cache[key] = (H, W, {k: ndi.binary_erosion(labels == k, iterations=1) for k in range(1, len(keep) + 1)})
    return _grid_cache[key]


H0, W0, m0 = get_masks(scenes[0])
meta = []
for k, m in m0.items():
    if m.sum() >= 50:
        ys, xs = np.nonzero(stand_lab == k)
        lon, lat = rasterio.transform.xy(wc_tr, ys.mean(), xs.mean())
        meta.append(dict(stand=f"{name}{k}", area_ha=round(float((stand_lab == k).sum() * 0.01), 1), interior_px=int(m.sum()), lon=lon, lat=lat))
pd.DataFrame(meta).to_csv(f"{OUT}/{name}_stands.csv", index=False)
print(len(meta), "stands with >= 50 interior px ->", f"{OUT}/{name}_stands.csv")


def read_band(href, H, W):
    with rasterio.open(href) as ds:
        win = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
        win = Window(int(round(win.col_off)), int(round(win.row_off)), max(int(round(win.width)), 1), max(int(round(win.height)), 1))
        return ds.read(1, window=win, out_shape=(H, W), resampling=Resampling.nearest).astype("float32")


def process(item):
    rows = []
    try:
        item = pc.sign(item)                                              # signed URLs expire after ~1 h: sign right before reading
        H, W, masks = get_masks(item); a = item.assets
        off = 1000.0 if bl(item) >= 4.0 else 0.0
        rd = lambda k: np.clip((read_band(a[k].href, H, W) - off) / 10000.0, 0, None)
        green, red, re1, nir, nir2, swir = (rd(k) for k in ("B03", "B04", "B05", "B08", "B8A", "B11"))
        good = ~np.isin(read_band(a["SCL"].href, H, W), [0, 1, 3, 8, 9, 10, 11])
        idx = {"ndvi": (nir - red) / (nir + red + 1e-6), "ndre": (nir2 - re1) / (nir2 + re1 + 1e-6),
               "ndmi": (nir2 - swir) / (nir2 + swir + 1e-6), "mndwi": (green - swir) / (green + swir + 1e-6)}
        for k, m in masks.items():
            if m.sum() < 50:
                continue
            ok = m & good
            row = dict(date=str(item.datetime.date()), id=item.id, baseline=bl(item), stand=f"{name}{k}", valid_frac=ok.sum() / m.sum())
            if ok.sum() >= 30:
                for nm, v in idx.items():
                    p = np.percentile(v[ok], [25, 50, 75]); row.update({f"{nm}_p25": p[0], f"{nm}_p50": p[1], f"{nm}_p75": p[2]})
                row["flooded_frac"] = float((idx["mndwi"][ok] > 0).mean())
            rows.append(row)
    except Exception as e:
        rows.append(dict(date=str(item.datetime.date()), id=item.id, error=repr(e)[:80]))
    return rows


t0, allrows, done = time.time(), [], 0
# RETRY mode (env RETRY=1): keep the rows of dates that already worked, re-read only the dates that failed (e.g. HTTP 403 from expired URLs)
prev_path = f"{OUT}/{name}_stats.csv"
if os.environ.get("RETRY") == "1" and os.path.exists(prev_path):
    prev = pd.read_csv(prev_path); bad = set(prev.loc[prev["error"].notna(), "date"]) if "error" in prev else set()
    allrows = prev[prev["error"].isna()].drop(columns=["error"], errors="ignore").to_dict("records") if "error" in prev else prev.to_dict("records")
    scenes = [s for s in scenes if str(s.datetime.date()) in bad]; print("RETRY: re-reading", len(scenes), "failed dates")
with cf.ThreadPoolExecutor(8) as ex:
    for r in ex.map(process, scenes):
        allrows += r; done += 1
        if done % 50 == 0:
            pd.DataFrame(allrows).to_csv(f"{OUT}/{name}_stats.csv", index=False)          # incremental save: a killed process loses at most 50 scenes
            print(f"  {done}/{len(scenes)} {time.time() - t0:.0f}s", flush=True)
out = pd.DataFrame(allrows); out.to_csv(f"{OUT}/{name}_stats.csv", index=False)
print(f"DONE {name}: errors {int(out['error'].notna().sum()) if 'error' in out else 0}, rows {len(out)}, {time.time() - t0:.0f}s")
