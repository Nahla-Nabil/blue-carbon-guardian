"""VHR confirmation, step 2 (view only): Esri World Imagery Wayback mosaics (zoom 17, about 1.1 m per screen pixel; source imagery 0.31-0.5 m)
of the four converted sites at dated captures, with the flagged 200 m cells outlined in red.
Images are written ONLY to the system temp folder, never to the project: Esri imagery may be displayed with the attribution
"Esri, Maxar, Earthstar Geographics, and the GIS User Community" but is not ours to redistribute. Capture dates: analysis/data/vhr_captures.json (script 34).
Run from the repository root: python analysis/34b_vhr_view.py [stand ids]   (default 5 9 12 18)
                           or: python analysis/34b_vhr_view.py ADN ADN17 ADN6   (scale-out block + stand names)
"""
import io, os, json, math, time, tempfile, concurrent.futures as cf
import requests, numpy as np, pandas as pd
from PIL import Image
from rasterio.features import shapes
from rasterio.transform import Affine
from rasterio.warp import transform_geom
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

OUT = os.path.join(tempfile.gettempdir(), "bcg_vhr_view"); CACHE = os.path.join(OUT, "tiles"); os.makedirs(CACHE, exist_ok=True)
REL = [("42403", "2021-06-08"), ("7110", "2022-03-28"), ("25982", "2023-02-22"), ("52930", "2023-11-14"), ("48925", "2025-01-06")]   # release id, capture date
Z = 17; URL = "https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/{r}/{z}/{y}/{x}"
import sys
ARGS = sys.argv[1:]; BLOCK = ARGS.pop(0) if ARGS and ARGS[0] in ("ADN", "ADW", "TRT") else None      # scale-out block (analysis/32-33) or the pilot
if BLOCK:
    D = f"analysis/data/scaleout_cells/{BLOCK}_"; g = json.load(open(D + "grid.json")); cells = np.load(D + "cells.npy")
    st = pd.read_csv(D + "cell_status.csv"); st["stand"] = st["stand"].astype(str)
else:
    g = json.load(open("analysis/data/grid.json")); cells = np.load("analysis/data/substand/cells.npy"); st = pd.read_csv("analysis/data/substand/cell_status.csv")
tr = Affine(*g["transform"])
sess = requests.Session(); FAILS = [0]


def merc(lon, lat):
    """lon/lat -> global Web-Mercator pixel coordinates at zoom Z."""
    n = 256 * 2 ** Z; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile(r, x, y):
    f = os.path.join(CACHE, f"{r}_{Z}_{y}_{x}.jpg")
    if os.path.exists(f): return Image.open(f).convert("RGB")
    for attempt in range(6):                                          # the tile server rate-limits: retry with back-off
        try:
            resp = sess.get(URL.format(r=r, z=Z, y=y, x=x), timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                im = Image.open(io.BytesIO(resp.content)).convert("RGB"); im.save(f); return im
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))
    FAILS[0] += 1; return Image.new("RGB", (256, 256), (200, 200, 200))


STANDS = ([a for a in ARGS] if BLOCK else [int(a) for a in ARGS]) or [5, 9, 12, 18]
for k in STANDS:
    bad = st[(st.stand == k) & st.condition.isin(["decline", "severe decline"])].cell.values
    m = np.isin(cells, bad).astype("uint8")
    polys = [transform_geom(g["crs"], "EPSG:4326", geom) for geom, v in shapes(m, mask=m > 0, transform=tr)]
    pts = np.array([p for pl in polys for ring in pl["coordinates"] for p in ring])
    lon0, lat0 = pts.min(0) - 0.002; lon1, lat1 = pts.max(0) + 0.002
    x0, y0 = merc(lon0, lat1); x1, y1 = merc(lon1, lat0); tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    fig, axs = plt.subplots(1, len(REL), figsize=(5.2 * len(REL), 5.4))
    for a, (r, d) in zip(axs, REL):
        xy = [(x, y) for y in range(ty0, ty1 + 1) for x in range(tx0, tx1 + 1)]
        with cf.ThreadPoolExecutor(3) as ex: tiles = list(ex.map(lambda p: tile(r, *p), xy))
        mos = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
        for (x, y), t in zip(xy, tiles): mos.paste(t, ((x - tx0) * 256, (y - ty0) * 256))
        a.imshow(mos); a.axis("off")
        for pl in polys:
            for ring in pl["coordinates"]:
                px = np.array([merc(lo, la) for lo, la in ring]); a.plot(px[:, 0] - tx0 * 256, px[:, 1] - ty0 * 256, color="red", lw=1.2)
        a.set_xlim(x0 - tx0 * 256, x1 - tx0 * 256); a.set_ylim(y1 - ty0 * 256, y0 - ty0 * 256); a.set_title(f"stand {k}: capture {d}", fontsize=12)
    fig.text(0.5, 0.01, "Imagery: Esri, Maxar, Earthstar Geographics, and the GIS User Community (World Imagery Wayback)", ha="center", fontsize=9)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, f"vhr_stand{k}.png"), dpi=70); plt.close(fig)
    print(f"stand {k} -> {OUT} (failed tiles so far: {FAILS[0]})", flush=True)
