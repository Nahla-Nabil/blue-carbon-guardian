"""VHR confirmation, step 1 (capture dates only). For each converted site (the flagged 200 m cells of stands 5, 9, 12, 18), list the distinct
very-high-resolution captures in Esri World Imagery Wayback (releases 2019-2026): capture date, resolution and sensor, read from each release's metadata layer.
No imagery is downloaded here. Output: analysis/data/vhr_captures.json
Run from the repository root. View the imagery itself with analysis/34b_vhr_view.py (writes outside the project).
"""
import json, requests, numpy as np, pandas as pd
from rasterio.transform import Affine
from rasterio.warp import transform

STANDS = (5, 9, 12, 18)
g = json.load(open("analysis/data/grid.json")); tr = Affine(*g["transform"])
cells = np.load("analysis/data/substand/cells.npy"); st = pd.read_csv("analysis/data/substand/cell_status.csv")
cfg = requests.get("https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json", timeout=30).json()
rel = sorted(((v["itemTitle"][-11:-1], k, v["metadataLayerUrl"]) for k, v in cfg.items()), key=lambda x: x[0])
rel = [r for r in rel if r[0] >= "2019-01-01"]

out = {}
for k in STANDS:
    bad = st[(st.stand == k) & st.condition.isin(["decline", "severe decline"])].cell.values
    ys, xs = np.nonzero(np.isin(cells, bad)); x, y = tr * (xs.mean() + .5, ys.mean() + .5)
    lon, lat = (v[0] for v in transform(g["crs"], "EPSG:4326", [x], [y]))
    seen, rows = set(), []
    for date, rid, murl in rel:
        try:
            q = requests.get(murl + "/identify", timeout=30, params=dict(
                geometry=f"{lon},{lat}", geometryType="esriGeometryPoint", sr=4326, layers="all", tolerance=1,
                mapExtent=f"{lon - .01},{lat - .01},{lon + .01},{lat + .01}", imageDisplay="800,800,96", returnGeometry="false", f="json")).json()
            att = [r["attributes"] for r in q.get("results", []) if r.get("attributes", {}).get("SRC_DATE")]
            a = att[0] if att else {}; key = (str(a.get("SRC_DATE", "")), a.get("SRC_DESC", ""))
            if key[0] and key not in seen:
                seen.add(key); rows.append(dict(release=date, release_id=rid, capture=key[0], res_m=a.get("SRC_RES"), source=a.get("SRC_DESC") or a.get("NICE_DESC")))
        except Exception as e:
            rows.append(dict(release=date, error=repr(e)[:60]))
    out[k] = dict(lon=round(lon, 5), lat=round(lat, 5), captures=rows)
    print(f"stand {k} ({lon:.4f}, {lat:.4f}): " + ", ".join(f"{r['capture']} ({r['source']}, {r['res_m']} m)" for r in rows if "capture" in r), flush=True)
json.dump(out, open("analysis/data/vhr_captures.json", "w"), indent=1)
