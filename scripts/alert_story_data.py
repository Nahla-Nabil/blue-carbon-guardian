"""README 'alert story', step 1 (data): for stand 5 (the flagship conversion) compute the product-alert states with src/bcg/monitor.py and fetch a few clear
Sentinel-2 true-colour chips over the stand from Planetary Computer (window reads, no full downloads).
Output: video/build/story/story.json + chip_<date>.png (gitignored build folder). Step 2 = scripts/make_alert_story.py.
Run from the repository root: python scripts/alert_story_data.py
"""
import json, pathlib, sys
import numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from PIL import Image
from rasterio.transform import Affine
from rasterio.windows import from_bounds

sys.path.insert(0, "src")
from bcg import monitor as M

STAND, TILE = 5, "40RBN"
OUT = pathlib.Path("video/build/story"); OUT.mkdir(parents=True, exist_ok=True)
# target months for the chips (story beats); the clearest scene within +/- 25 days is used
TARGETS = ["2021-11-15", "2022-06-15", "2022-10-20", "2023-02-20", "2023-05-15", "2023-09-15", "2024-03-15", "2025-02-15", "2026-05-01"]

# ---- 1. alert states (stand average + every 200 m cell), same code path as the notebook ----
cells = pd.read_csv("analysis/data/substand/cells.csv"); cs = cells[cells.stand == STAND]
stats = pd.read_csv("analysis/data/substand/cell_stats.csv"); stats = stats[stats.cell.isin(cs.cell)]
ser = {c: M.to_series(g) for c, g in stats.groupby("cell")}
ids = [c for c in cs.cell if c in ser]
proxy = M.stand_proxy([ser[c] for c in ids], cs.n_px.sum())
st = M.alert_state(proxy); cst = [M.alert_state(ser[c]) for c in ids]
t, on, on_s, on_c = M.product_alert(st, cst)
d = lambda x: str((M.T0 + pd.Timedelta(days=float(x))).date())
eps = [(str(a), str(b)) for a, b in M.episodes(t, on)]
print("episodes:", eps)

# ---- 2. geometry: cell rectangles in grid pixels, chip window ----
g = json.load(open("analysis/data/grid.json")); tr = Affine(*g["transform"])
lab = np.load("analysis/data/substand/cells.npy")
rr, cc = np.nonzero(np.isin(lab, ids)); pad = 40
r0, r1, c0, c1 = rr.min() - pad, rr.max() + pad, cc.min() - pad, cc.max() + pad
cellbox = {}
for c in ids:
    r, q = np.nonzero(lab[r0:r1, c0:c1] == c)
    cellbox[int(c)] = [int(q.min()), int(r.min()), int(q.max() + 1), int(r.max() + 1)]
x0, y1 = tr * (c0, r0); x1, y0 = tr * (c1, r1)

# ---- 3. Sentinel-2 chips ----
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
chips = []
for tg in TARGETS:
    a, b = pd.Timestamp(tg) - pd.Timedelta(days=25), pd.Timestamp(tg) + pd.Timedelta(days=25)
    items = [i for i in cat.search(collections=["sentinel-2-l2a"], bbox=g["region"], datetime=f"{a.date()}/{b.date()}",
                                   query={"eo:cloud_cover": {"lt": 5}}).items() if i.properties["s2:mgrs_tile"] == TILE]
    best = None
    for i in sorted(items, key=lambda i: (i.properties["eo:cloud_cover"], abs((i.datetime.replace(tzinfo=None) - pd.Timestamp(tg)).days))):
        i = pc.sign(i); off = 1000.0 if float(i.properties.get("s2:processing_baseline", "4.0")) >= 4.0 else 0.0
        rgb = []
        for k in ("B04", "B03", "B02"):
            with rasterio.open(i.assets[k].href) as ds:
                rgb.append((ds.read(1, window=from_bounds(x0, y0, x1, y1, ds.transform), out_shape=(r1 - r0, c1 - c0)).astype("float32") - off) / 1e4)
        rgb = np.stack(rgb, -1)
        if (rgb.sum(-1) <= 0).mean() < 0.01:
            best = (i, rgb); break
    if best is None:
        print("no clear scene near", tg); continue
    i, rgb = best; day = str(i.datetime.date())
    img = np.clip(rgb / 0.42, 0, 1) ** (1 / 1.35)
    Image.fromarray((img * 255).astype("uint8")).resize(((c1 - c0) * 2, (r1 - r0) * 2), Image.BICUBIC).save(OUT / f"chip_{day}.png")
    chips.append(day); print("chip", day, i.properties["eo:cloud_cover"])

# ---- 4. monthly states for the animation ----
def at(ts, zs, day):
    j = np.searchsorted(ts, day, side="right") - 1
    return float(zs[j]) if j >= 0 and not np.isnan(zs[j]) else 0.0
months = pd.date_range("2022-01-01", "2026-09-01", freq="SMS")   # twice a month
frames = []
for m in months:
    day = (m - M.T0).days
    cz = [at(ts, zs, day) for ts, zs in cst]
    j = np.searchsorted(t, day, side="right") - 1
    frames.append(dict(date=str(m.date()), stand=round(at(*st, day), 2), worst=round(min(cz), 2), cells=[round(z, 2) for z in cz],
                       alert=bool(on[j]) if j >= 0 else False))
json.dump(dict(stand=STAND, ids=[int(c) for c in ids], cellbox=cellbox, size=[int(c1 - c0), int(r1 - r0)], chips=chips, episodes=eps,
               stand_thr=M.STAND_THR, cell_thr=M.CELL_THR, frames=frames), open(OUT / "story.json", "w"))
print("saved", OUT / "story.json", len(frames), "frames,", len(chips), "chips")
