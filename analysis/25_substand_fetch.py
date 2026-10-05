"""Sub-stand monitoring, step 1: Sentinel-2 series per 200 m CELL inside the 25 pilot stands.

Why: the stand-level index is an average, so a partial loss is diluted (stand 9 lost its south-east part but its average still reads 'stable', and its
alert came ~3 months after the change started). Here every stand is cut into 200 m x 200 m cells (20 x 20 Sentinel-2 pixels, 4 ha); a cell keeps
its interior WorldCover-mangrove pixels (1-pixel erosion, as for stands) and is used if it has >= 60 of them (0.6 ha).
Per date and cell: median NDVI / NDRE / NDMI / MNDWI, flooded fraction, valid fraction (same recipe and cloud mask as analysis/05).
Outputs: analysis/data/substand/cells.csv (cell id, stand, pixel count, centre), cells.npy (cell label grid), cell_stats.csv
Robustness: every scene is signed right before reading (signed URLs expire after ~1 h), results are saved every 50 scenes, and RETRY=1 re-reads only failed dates.
"""
import os, json, time, concurrent.futures as cf
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from rasterio.warp import transform_bounds, transform_geom, Resampling
from rasterio.windows import Window, from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, shape

CELL_PX, MIN_PX, TILE, PERIOD = 20, 60, "40RBN", "2020-01-01/2026-09-19"
OUT = "analysis/data/substand"; os.makedirs(OUT, exist_ok=True)
g = json.load(open("analysis/data/grid.json")); H, W, REGION, crs, tr = g["H"], g["W"], g["region"], g["crs"], Affine(*g["transform"])
wc = np.load("analysis/data/worldcover_grid.npy")
gj = json.load(open("analysis/data/stands.geojson"))

# ---- cells ---------------------------------------------------------------------------------------------------------------
stand_grid = np.zeros((H, W), "int16")
for f in gj["features"]:
    m = rasterize([(transform_geom("EPSG:4326", crs, f["geometry"]), 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    stand_grid[m] = int(f["properties"]["stand"])
interior = np.zeros((H, W), bool)
for k in np.unique(stand_grid[stand_grid > 0]):
    interior |= ndi.binary_erosion((stand_grid == k) & (wc == 95), iterations=1)
rows_, cols_ = np.indices((H, W)); block = (rows_ // CELL_PX) * ((W // CELL_PX) + 1) + (cols_ // CELL_PX)
cells = np.zeros((H, W), "int32"); meta = []; cid = 0
for k in np.unique(stand_grid[stand_grid > 0]):
    m = interior & (stand_grid == k)
    for b in np.unique(block[m]):
        px = m & (block == b)
        if px.sum() >= MIN_PX:
            cid += 1; cells[px] = cid
            ys, xs = np.nonzero(px); x, y = tr * (xs.mean() + .5, ys.mean() + .5)
            lon, lat = rasterio.warp.transform(crs, "EPSG:4326", [x], [y])
            meta.append(dict(cell=cid, stand=int(k), n_px=int(px.sum()), row=float(ys.mean()), col=float(xs.mean()), lon=lon[0], lat=lat[0]))
pd.DataFrame(meta).to_csv(f"{OUT}/cells.csv", index=False); np.save(f"{OUT}/cells.npy", cells)
print(f"{cid} cells in {len(set(m['stand'] for m in meta))} stands | {sum(m['n_px'] for m in meta) * .01:.0f} ha of interior mangrove pixels")

sel = cells > 0; cell_of_px = cells[sel]

# ---- scenes (same selection as analysis/05) ------------------------------------------------------------------------------
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
    try:
        item = pc.sign(item); a = item.assets; off = 1000.0 if bl(item) >= 4.0 else 0.0
        rd = lambda k: np.clip((read_band(a[k].href) - off) / 10000.0, 0, None)[sel]
        green, red, re1, nir, nir2, swir = (rd(k) for k in ("B03", "B04", "B05", "B08", "B8A", "B11"))
        good = ~np.isin(read_band(a["SCL"].href)[sel], [0, 1, 3, 8, 9, 10, 11])
        d = pd.DataFrame({"cell": cell_of_px, "good": good,
                          "ndvi": (nir - red) / (nir + red + 1e-6), "ndre": (nir2 - re1) / (nir2 + re1 + 1e-6),
                          "ndmi": (nir2 - swir) / (nir2 + swir + 1e-6), "mndwi": (green - swir) / (green + swir + 1e-6)})
        vf = d.groupby("cell").good.mean()
        dg = d[d.good]; dg = dg.assign(flooded=(dg.mndwi > 0).astype(float))
        n = dg.groupby("cell").size(); med = dg.groupby("cell")[["ndvi", "ndre", "ndmi", "mndwi"]].median().add_suffix("_p50")
        out = pd.DataFrame({"valid_frac": vf}).join(med).join(dg.groupby("cell").flooded.mean().rename("flooded_frac")).join(n.rename("n_valid"))
        out.loc[out.n_valid.fillna(0) < 30, ["ndvi_p50", "ndre_p50", "ndmi_p50", "mndwi_p50", "flooded_frac"]] = np.nan
        out = out.reset_index(); out.insert(0, "date", str(item.datetime.date())); out["id"] = item.id
        return out.to_dict("records")
    except Exception as e:
        return [dict(date=str(item.datetime.date()), id=item.id, error=repr(e)[:80])]


t0, allrows, done = time.time(), [], 0
path = f"{OUT}/cell_stats.csv"
if os.environ.get("RETRY") == "1" and os.path.exists(path):
    prev = pd.read_csv(path); bad = set(prev.loc[prev["error"].notna(), "date"]) if "error" in prev else set()
    allrows = prev[prev["error"].isna()].drop(columns=["error"]).to_dict("records") if "error" in prev else prev.to_dict("records")
    scenes = [s for s in scenes if str(s.datetime.date()) in bad]; print("RETRY:", len(scenes), "dates")
with cf.ThreadPoolExecutor(8) as ex:
    for r in ex.map(process, scenes):
        allrows += r; done += 1
        if done % 50 == 0:
            pd.DataFrame(allrows).to_csv(path, index=False); print(f"  {done}/{len(scenes)} {time.time() - t0:.0f}s", flush=True)
out = pd.DataFrame(allrows); out.to_csv(path, index=False)
print(f"DONE: errors {int(out['error'].notna().sum()) if 'error' in out else 0}, rows {len(out)}, {time.time() - t0:.0f}s")
