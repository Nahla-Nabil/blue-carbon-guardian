"""Build the self-contained dashboard page (dashboard/index.html) from the analysis outputs.
No server needed: all data, the map (SVG, no basemap tiles), the charts and the stand-5 before/after image are embedded.
Inputs (analysis/data): stands.geojson, stand_status.csv, stand_alert_episodes.csv, dashboard_data.json; figure stand5_before_after_2021_2026.png
"""
import base64, io, json, os
import numpy as np, pandas as pd
from PIL import Image

D = "analysis/data/"
gj = json.load(open(D + "stands.geojson")); st = pd.read_csv(D + "stand_status.csv"); ep = pd.read_csv(D + "stand_alert_episodes.csv")
series = json.load(open(D + "dashboard_data.json"))["series"]

def to_uri(path, width=1400):
    im = Image.open(path).convert("RGB"); im = im.resize((width, int(width * im.height / im.width)))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=78); return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
img_uri = to_uri("analysis/figures/stand5_before_after_2021_2026.png")
img9_uri = to_uri("analysis/figures/stand9_before_after_2020_2026.png")
img_en_uri = to_uri("analysis/figures/enmap_stand5_two_epochs.png")
img12_uri = to_uri("analysis/figures/stand12_key_years.png")

# ---- product alert = combined rule of analysis/29-31 (stand average <= -1.5 sigma OR any 200 m cell <= -3.5 sigma) ------------------------------
us = pd.read_csv(D + "union_status.csv").set_index("stand"); U = json.load(open(D + "union_series.json"))
ep = pd.read_csv(D + "union_episodes.csv").fillna({"cells": ""})
st = st.copy(); st["alerts_stand_only"] = st["alerts_2022_2026"]
for c in ("alert_now", "alerts_2022_2026", "stand_z_now", "worst_cell_z_now"): st[c] = st.stand.map(us[c])
for k, s in series.items():
    u = U["series"].get(str(k), {}); s["z"] = [u.get(m, [None, None])[0] for m in s["months"]]; s["zc"] = [u.get(m, [None, None])[1] for m in s["months"]]
st["last_obs"] = st["last_obs"].astype(str)
cols = ["stand", "area_ha", "condition", "alert_now", "alerts_2022_2026", "ndvi_base", "ndvi_now", "ndvi_change_pct", "ndmi_base", "ndmi_now",
        "ndmi_change_pct", "trend_ndvi_pct_per_yr", "trend_ndmi_pct_per_yr", "stock_tC_p10", "stock_tC_p50", "stock_tC_p90", "stock_tCO2e_p50", "last_obs",
        "alerts_stand_only", "stand_z_now", "worst_cell_z_now"]
data = dict(features=gj["features"], status=json.loads(st[cols].to_json(orient="records")), series=series,
            episodes=json.loads(ep.to_json(orient="records")),
            kpi=dict(n=int(len(st)), area=float(st.area_ha.sum()), alerts=int(st.alert_now.sum()), severe=int((st.condition == "severe decline").sum()),
                     severe_area=float(st.loc[st.condition == "severe decline", "area_ha"].sum()),
                     stock_p10=float(st.stock_tC_p10.sum()), stock_p50=float(st.stock_tC_p50.sum()), stock_p90=float(st.stock_tC_p90.sum()),
                     last_obs=str(st.last_obs.max())),
            rule=dict(stand=U["stand_thr"], cell=U["cell_thr"], rate=U["rate_per_stand_year"], in_alert=U["in_alert_share"]))

# ---- sub-stand layer: 200 m cells (analysis/25-26) as simplified polygons + their condition --------------------------------------------
from rasterio.features import shapes
from rasterio.transform import Affine
from rasterio.warp import transform_geom
from shapely.geometry import shape as shp, mapping
from shapely.ops import unary_union
grid = json.load(open(D + "grid.json")); cells = np.load(D + "substand/cells.npy")
cst = pd.read_csv(D + "substand/cell_status.csv").set_index("cell")
parts = {}
for geom, v in shapes(cells.astype("int32"), mask=cells > 0, transform=Affine(*grid["transform"])):
    parts.setdefault(int(v), []).append(shp(transform_geom(grid["crs"], "EPSG:4326", geom)))
rnd = lambda o: [rnd(x) for x in o] if isinstance(o, (list, tuple)) and not isinstance(o[0], (int, float)) else [round(o[0], 5), round(o[1], 5)]
data["cells"] = [dict(c=c, s=int(cst.loc[c, "stand"]), cond=cst.loc[c, "condition"], ha=round(float(cst.loc[c, "area_ha"]), 2),
                      dv=round(float(cst.loc[c, "ndvi_change_pct"]), 0), dm=round(float(cst.loc[c, "ndmi_change_pct"]), 0),
                      g=dict(type=(m := mapping(unary_union(p).simplify(0.00004)))["type"], coordinates=rnd(m["coordinates"])))
                 for c, p in parts.items() if c in cst.index]

HTML = open("analysis/dashboard_template.html", encoding="utf-8").read()
HTML = HTML.replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace("__IMG__", img_uri).replace("__IMG9__", img9_uri).replace("__IMGEN__", img_en_uri).replace("__IMG12__", img12_uri)
os.makedirs("dashboard", exist_ok=True); open("dashboard/index.html", "w", encoding="utf-8").write(HTML)
print("dashboard/index.html", round(len(HTML) / 1024), "KB")
