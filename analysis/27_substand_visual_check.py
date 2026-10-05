"""Sub-stand monitoring, step 3: visual check of cells flagged 'severe decline' that the epoch-difference indicator does NOT support.

Same-season (May-Sep), low-tide Sentinel-2 true colour, 2020 vs 2026, identical reflectance stretch; the cell's pixels are outlined in yellow.
Dates: the driest clean date of each year from the pilot stand series (lowest regional median MNDWI, >= 20 stands valid).
Output: analysis/figures/substand_unsupported_cells.png
"""
import json, numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.transform import Affine
from rasterio.warp import transform_bounds, Resampling
from rasterio.windows import Window, from_bounds
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

CELLS = [13, 296, 452, 211, 234]                 # stands 1, 6, 12 (unsupported), and two stand-5 cells for comparison
g = json.load(open("analysis/data/grid.json")); H, W, REGION = g["H"], g["W"], g["region"]
cells = np.load("analysis/data/substand/cells.npy"); st = pd.read_csv("analysis/data/substand/cell_status.csv").set_index("cell")
s = pd.read_csv("analysis/data/s2_stands_stats.csv"); s = s[s.valid_frac >= 0.95].dropna(subset=["mndwi_p50"])
d = s.groupby(["date", "id"]).agg(w=("mndwi_p50", "median"), n=("stand", "nunique")).reset_index()
d = d[(d.n >= 20) & d.date.str[5:7].isin(["05", "06", "07", "08", "09"])]
ids = {y: d[d.date.str[:4] == str(y)].sort_values("w").iloc[0]["id"] for y in (2020, 2026)}
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)


def rgb(item_id):
    item = pc.sign(cat.get_collection("sentinel-2-l2a").get_item(item_id)); off = 1000.0 if float(item.properties.get("s2:processing_baseline", "4")) >= 4 else 0.0
    out = []
    for k in ("B04", "B03", "B02"):
        with rasterio.open(item.assets[k].href) as ds:
            w = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *REGION), ds.transform)
            w = Window(int(round(w.col_off)), int(round(w.row_off)), int(round(w.width)), int(round(w.height)))
            out.append((ds.read(1, window=w, out_shape=(H, W), resampling=Resampling.nearest).astype("float32") - off) / 10000.0)
    return np.clip(np.stack(out, -1) / 0.25, 0, 1) ** 0.8, str(item.datetime.date())


img = {y: rgb(i) for y, i in ids.items()}
fig, ax = plt.subplots(len(CELLS), 2, figsize=(8, 3.9 * len(CELLS)))
for r, c in enumerate(CELLS):
    ys, xs = np.nonzero(cells == c); cy, cx = int(ys.mean()), int(xs.mean()); R = 45
    y0, y1, x0, x1 = max(cy - R, 0), min(cy + R, H), max(cx - R, 0), min(cx + R, W)
    for k, y in enumerate((2020, 2026)):
        a = ax[r, k]; a.imshow(img[y][0][y0:y1, x0:x1]); a.axis("off")
        a.contour((cells[y0:y1, x0:x1] == c).astype(float), levels=[0.5], colors="yellow", linewidths=1.3)
        a.set_title(f"cell {c} (stand {int(st.loc[c, 'stand'])}, {st.loc[c, 'area_ha']:.1f} ha)  {img[y][1]}", fontsize=9)
plt.tight_layout(); plt.savefig("analysis/figures/substand_unsupported_cells.png", dpi=85); print("saved", ids)
