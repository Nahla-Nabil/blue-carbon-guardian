"""Module 1, step 1: cloud-free, low-tide Sentinel-2 composites of the 25-stand region for two epochs (2021 and 2025).

- picks the 10 driest (lowest scene-level MNDWI = lowest water/tide signal) clean dates between April and October of each year,
  so that both epochs use similar seasons and tide states
- reads 10 bands + SCL for those dates straight from the cloud (Planetary Computer), masks cloud/shadow/cirrus, takes the per-pixel median
- saves analysis/data/composite_{2021,2025}.npz (10 x H x W float32 reflectance) + grid.json (CRS/transform) + WorldCover class map on the same grid
Requires: pystac-client, planetary-computer, rasterio, numpy, pandas, scipy
"""
import json, time, concurrent.futures as cf
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.merge import merge
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import Window, from_bounds
from shapely.geometry import box, shape

REGION = json.load(open("analysis/data/dashboard_data.json"))["region"]        # [lon0, lat0, lon1, lat1] of the 25-stand block
BANDS = ["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
N_DATES, MONTHS, TILE = 10, (4, 10), "40RBN"
t0 = time.time()

s = pd.read_csv("analysis/data/s2_stands_stats.csv"); s["date"] = pd.to_datetime(s["date"]); s = s[(s.valid_frac >= 0.9)].dropna(subset=["mndwi_p50"])
d = s.groupby("date").agg(w=("mndwi_p50", "median"), n=("stand", "nunique")).reset_index()
d = d[(d.n >= 20) & (d.date.dt.month.between(*MONTHS))]
pick = {y: d[d.date.dt.year == y].sort_values("w").head(N_DATES).date.dt.strftime("%Y-%m-%d").tolist() for y in (2021, 2025)}
print({y: (len(v), v[0], v[-1]) for y, v in pick.items()})

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
with rasterio.open(next(iter(cat.search(collections=["sentinel-2-l2a"], bbox=REGION, datetime="2025-06-01/2025-06-20",
                                        query={"eo:cloud_cover": {"lt": 30}}).items())).assets["B04"].href) as ds:
    crs = ds.crs
    w = from_bounds(*transform_bounds("EPSG:4326", crs, *REGION), ds.transform)
    WIN = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height))); win_tr = ds.window_transform(WIN)
H, W = int(WIN.height), int(WIN.width)
print("grid", H, "x", W, "crs", crs)


def read_band(href):
    with rasterio.open(href) as ds:
        win = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
        win = Window(int(round(win.col_off)), int(round(win.row_off)), max(int(round(win.width)), 1), max(int(round(win.height)), 1))
        return ds.read(1, window=win, out_shape=(H, W), resampling=Resampling.nearest).astype("float32")


def read_scene(item):
    off = 1000.0 if float(item.properties.get("s2:processing_baseline", "4.0")) >= 4.0 else 0.0
    scl = read_band(item.assets["SCL"].href); bad = np.isin(scl, [0, 1, 3, 8, 9, 10, 11])
    out = np.empty((len(BANDS), H, W), "float32")
    for k, b in enumerate(BANDS):
        a = np.clip((read_band(item.assets[b].href) - off) / 10000.0, 0, None); a[bad] = np.nan; out[k] = a
    return out


for y, dates in pick.items():
    items = []
    for dt in dates:
        r = list(cat.search(collections=["sentinel-2-l2a"], bbox=REGION, datetime=f"{dt}/{dt}T23:59:59Z").items())
        r = [i for i in r if i.properties["s2:mgrs_tile"] == TILE and shape(i.geometry).contains(box(*REGION))]
        if r: items.append(sorted(r, key=lambda i: float(i.properties.get("s2:processing_baseline", "4")), reverse=True)[0])
    print(y, "scenes found:", len(items), f"({time.time() - t0:.0f}s)")
    with cf.ThreadPoolExecutor(4) as ex:
        stack = list(ex.map(read_scene, items))
    comp = np.nanmedian(np.stack(stack), axis=0).astype("float32")                 # (bands, H, W)
    valid = np.isfinite(comp).all(axis=0)
    print(f"  composite {y}: valid pixels {valid.mean() * 100:.1f}% ({time.time() - t0:.0f}s)")
    np.savez_compressed(f"analysis/data/composite_{y}.npz", comp=comp, bands=np.array(BANDS), dates=np.array(dates))

# WorldCover 2021 class map on the same grid + grid definition
wc_items = list(cat.search(collections=["esa-worldcover"], bbox=REGION, datetime="2021-01-01/2021-12-31").items())
arr, wtr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=REGION)
wc = np.zeros((H, W), "uint8")
reproject(arr[0], wc, src_transform=wtr, src_crs="EPSG:4326", dst_transform=win_tr, dst_crs=crs, resampling=Resampling.nearest)
np.save("analysis/data/worldcover_grid.npy", wc)
json.dump(dict(crs=crs.to_string(), transform=list(win_tr)[:6], H=H, W=W, region=REGION), open("analysis/data/grid.json", "w"))
print(f"done in {time.time() - t0:.0f}s")
