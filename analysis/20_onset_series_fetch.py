"""Onset dating, step 1: per-date Sentinel-2 index medians inside the PIXELS that turned out to change (stands 5 and 9) vs a control set.

Why: the stand-level alert is an average over the whole stand, and for the two confirmed real events we do not know WHEN the conversion began.
Here we read every clean Sentinel-2 date 2020-2026 over the 25-stand region and store, for each stand in (5, 9):
  - 'loss'    : WorldCover-mangrove pixels inside the stand that the 2021->2025 change indicator flagged (analysis/12)
  - 'control' : the remaining mangrove pixels of the same stand, at least 5 pixels (50 m) away from any flagged pixel
The paired difference loss - control cancels tide, season and sensor effects that both sets share (analysis/21 does the change-point analysis).
CAUTION (selection): the loss pixels were chosen with 2021 vs 2025 imagery, so this dates the ONSET inside pixels already known to have changed;
it is not an unbiased detection test. Output: analysis/data/onset_series.csv
Requires: pystac-client, planetary-computer, rasterio, numpy, pandas, scipy, shapely
"""
import json, time, concurrent.futures as cf
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.warp import transform_bounds, transform_geom, Resampling
from rasterio.windows import Window, from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, shape

STANDS, TILE, PERIOD = (5, 9), "40RBN", "2020-01-01/2026-09-19"
g = json.load(open("analysis/data/grid.json")); H, W, REGION, crs, tr = g["H"], g["W"], g["region"], g["crs"], Affine(*g["transform"])
wc = np.load("analysis/data/worldcover_grid.npy")
chg = rasterio.open("analysis/data/change_indicator_2021_2025.tif").read(1)
loss_all = chg == 1
gj = json.load(open("analysis/data/stands.geojson"))

masks = {}
for f in gj["features"]:
    k = f["properties"]["stand"]
    if k not in STANDS:
        continue
    poly = rasterize([(transform_geom("EPSG:4326", crs, f["geometry"]), 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    loss = poly & (wc == 95) & loss_all
    ctrl = poly & (wc == 95) & ~ndi.binary_dilation(loss_all, iterations=5)
    masks[k] = {"loss": loss, "control": ctrl}
    print(f"stand {k}: loss {loss.sum()} px ({loss.sum() * .01:.1f} ha), control {ctrl.sum()} px ({ctrl.sum() * .01:.1f} ha)")

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
found = list(cat.search(collections=["sentinel-2-l2a"], bbox=REGION, datetime=PERIOD, query={"eo:cloud_cover": {"lt": 40}}).items())
found = [i for i in found if i.properties["s2:mgrs_tile"] == TILE and shape(i.geometry).contains(box(*REGION))]
bl = lambda i: float(i.properties.get("s2:processing_baseline", "4.0"))
by_date = {}
for i in found:
    by_date.setdefault(i.datetime.date(), []).append(i)
scenes = sorted((sorted(v, key=bl, reverse=True)[0] for v in by_date.values()), key=lambda i: i.datetime)
print(len(scenes), "dates")


def read_band(href):
    with rasterio.open(href) as ds:
        win = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
        win = Window(int(round(win.col_off)), int(round(win.row_off)), max(int(round(win.width)), 1), max(int(round(win.height)), 1))
        return ds.read(1, window=win, out_shape=(H, W), resampling=Resampling.nearest).astype("float32")


def process(item):
    rows = []
    try:
        a = item.assets; off = 1000.0 if bl(item) >= 4.0 else 0.0
        rd = lambda k: np.clip((read_band(a[k].href) - off) / 10000.0, 0, None)
        green, red, nir, nir2, swir = (rd(k) for k in ("B03", "B04", "B08", "B8A", "B11"))
        good = ~np.isin(read_band(a["SCL"].href), [0, 1, 3, 8, 9, 10, 11])
        idx = {"ndvi": (nir - red) / (nir + red + 1e-6), "ndmi": (nir2 - swir) / (nir2 + swir + 1e-6), "mndwi": (green - swir) / (green + swir + 1e-6)}
        for k, sets in masks.items():
            for name, m in sets.items():
                ok = m & good
                row = dict(date=str(item.datetime.date()), stand=k, part=name, n_valid=int(ok.sum()), n_all=int(m.sum()))
                if ok.sum() >= 20:
                    row.update({f"{i}": float(np.median(v[ok])) for i, v in idx.items()})
                rows.append(row)
    except Exception as e:
        rows.append(dict(date=str(item.datetime.date()), error=repr(e)[:80]))
    return rows


t0, allrows, done = time.time(), [], 0
with cf.ThreadPoolExecutor(10) as ex:
    for r in ex.map(process, scenes):
        allrows += r; done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(scenes)} {time.time() - t0:.0f}s", flush=True)
out = pd.DataFrame(allrows).sort_values(["stand", "part", "date"])
out.to_csv("analysis/data/onset_series.csv", index=False)
print("errors:", int(out["error"].notna().sum()) if "error" in out else 0, "| rows", len(out), f"| {time.time() - t0:.0f}s -> analysis/data/onset_series.csv")
