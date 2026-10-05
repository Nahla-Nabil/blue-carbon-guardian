"""Out-of-sample test of the product alert, step 1: 200 m cell series for the 66 scale-out stands (blocks ADN, ADW, TRT of analysis/22).

Same recipe as analysis/25 (pilot cells): stands from <block>_stands.geojson, WorldCover-2021 mangrove pixels reprojected to the block's own Sentinel-2 grid,
1-pixel interior erosion, 200 m x 200 m cells (20 x 20 px) with >= 60 interior pixels. For every clean date 2020-2026: median NDVI / NDRE / NDMI / MNDWI,
flooded fraction and valid fraction per cell (SCL cloud mask).
Usage: python analysis/32_scaleout_cells_fetch.py <block> <lon0> <lat0> <lon1> <lat1> [mgrs_tile]
  ADN 54.51 24.56 54.63 24.65 40RBN | ADW 54.39 24.41 54.51 24.50 40RBN | TRT 49.93 26.65 50.05 26.74 39RUK
Outputs (analysis/data/scaleout_cells/): <block>_cells.csv, <block>_cells.npy, <block>_grid.json, <block>_cell_stats.csv
Robustness: each scene is signed right before reading (signed URLs expire), results are saved every 50 scenes, RETRY=1 re-reads only failed dates.
"""
import os, sys, json, time, concurrent.futures as cf
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.features import rasterize
from rasterio.merge import merge
from rasterio.warp import transform_bounds, transform_geom, reproject, Resampling
from rasterio.windows import Window, from_bounds
from scipy import ndimage as ndi
from shapely.geometry import box, shape

B = sys.argv[1]; REGION = [float(x) for x in sys.argv[2:6]]; TILE = sys.argv[6] if len(sys.argv) > 6 else None
CELL_PX, MIN_PX, PERIOD = 20, 60, "2020-01-01/2026-09-19"
OUT = "analysis/data/scaleout_cells"; os.makedirs(OUT, exist_ok=True)
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)

# ---- scenes and the block's Sentinel-2 grid ------------------------------------------------------------------------------------------
found = list(cat.search(collections=["sentinel-2-l2a"], bbox=REGION, datetime=PERIOD, query={"eo:cloud_cover": {"lt": 40}}).items())
found = [i for i in found if shape(i.geometry).contains(box(*REGION)) and (TILE is None or i.properties["s2:mgrs_tile"] == TILE)]
bl = lambda i: float(i.properties.get("s2:processing_baseline", "4.0"))
by_date = {}
for i in found:
    by_date.setdefault(i.datetime.date(), []).append(i)
scenes = sorted((sorted(v, key=bl, reverse=True)[0] for v in by_date.values()), key=lambda i: i.datetime)
with rasterio.open(pc.sign(scenes[0]).assets["B04"].href) as ds:
    crs = ds.crs; w = from_bounds(*transform_bounds("EPSG:4326", crs, *REGION), ds.transform)
    WIN = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height))); tr = ds.window_transform(WIN)
H, W = int(WIN.height), int(WIN.width)
json.dump(dict(crs=str(crs), transform=list(tr)[:6], H=H, W=W, region=REGION), open(f"{OUT}/{B}_grid.json", "w"))
print(B, len(scenes), "dates, grid", H, "x", W, crs)

# ---- mangrove mask, stands, cells -------------------------------------------------------------------------------------------------------
wc_items = list(cat.search(collections=["esa-worldcover"], bbox=REGION, datetime="2021-01-01/2021-12-31").items())
wc_arr, wc_tr = merge([rasterio.open(i.assets["map"].href) for i in wc_items], bounds=REGION)
wc = np.zeros((H, W), "uint8")
reproject(wc_arr[0], wc, src_transform=wc_tr, src_crs="EPSG:4326", dst_transform=tr, dst_crs=crs, resampling=Resampling.nearest)
gj = json.load(open(f"analysis/data/scaleout/{B}_stands.geojson"))
monitored = set(pd.read_csv(f"analysis/data/scaleout/scaleout_status.csv").stand)
names = sorted({f["properties"]["stand"] for f in gj["features"]} & monitored)
rows_, cols_ = np.indices((H, W)); block = (rows_ // CELL_PX) * ((W // CELL_PX) + 1) + (cols_ // CELL_PX)
cells = np.zeros((H, W), "int32"); meta = []; cid = 0
for name in names:
    geoms = [transform_geom("EPSG:4326", crs, f["geometry"]) for f in gj["features"] if f["properties"]["stand"] == name]
    m = rasterize([(g, 1) for g in geoms], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    m = ndi.binary_erosion(m & (wc == 95), iterations=1)
    for bk in np.unique(block[m]):
        px = m & (block == bk)
        if px.sum() >= MIN_PX:
            cid += 1; cells[px] = cid; ys, xs = np.nonzero(px)
            meta.append(dict(cell=cid, stand=name, n_px=int(px.sum()), row=float(ys.mean()), col=float(xs.mean())))
pd.DataFrame(meta).to_csv(f"{OUT}/{B}_cells.csv", index=False); np.save(f"{OUT}/{B}_cells.npy", cells)
print(f"{cid} cells in {len({m['stand'] for m in meta})} stands, {sum(m['n_px'] for m in meta) * .01:.0f} ha interior mangrove pixels")
sel = cells > 0; cell_of_px = cells[sel]


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
        d = pd.DataFrame({"cell": cell_of_px, "good": good, "ndvi": (nir - red) / (nir + red + 1e-6), "ndre": (nir2 - re1) / (nir2 + re1 + 1e-6),
                          "ndmi": (nir2 - swir) / (nir2 + swir + 1e-6), "mndwi": (green - swir) / (green + swir + 1e-6)})
        vf = d.groupby("cell").good.mean(); dg = d[d.good]; dg = dg.assign(flooded=(dg.mndwi > 0).astype(float))
        out = pd.DataFrame({"valid_frac": vf}).join(dg.groupby("cell")[["ndvi", "ndre", "ndmi", "mndwi"]].median().add_suffix("_p50"))
        out = out.join(dg.groupby("cell").flooded.mean().rename("flooded_frac")).join(dg.groupby("cell").size().rename("n_valid"))
        out.loc[out.n_valid.fillna(0) < 30, ["ndvi_p50", "ndre_p50", "ndmi_p50", "mndwi_p50", "flooded_frac"]] = np.nan
        out = out.reset_index(); out.insert(0, "date", str(item.datetime.date())); out["id"] = item.id
        return out.to_dict("records")
    except Exception as e:
        return [dict(date=str(item.datetime.date()), id=item.id, error=repr(e)[:80])]


t0, allrows, done = time.time(), [], 0; path = f"{OUT}/{B}_cell_stats.csv"
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
print(f"DONE {B}: errors {int(out['error'].notna().sum()) if 'error' in out else 0}, rows {len(out)}, {time.time() - t0:.0f}s")
