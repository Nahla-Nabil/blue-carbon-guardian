"""Scale-out, step 3: visual check of the stands the unchanged monitor flagged as 'decline' on unseen data (analysis/23).

For each flagged stand: Sentinel-2 true colour (B04/B03/B02, identical stretch) from a clear, low-tide May-Sep date in 2020 and in 2026, stand outline in yellow.
Dates are chosen from the stand's own series (valid_frac = 1, lowest MNDWI = driest / lowest tide in that year).
Output: analysis/figures/scaleout_declines_2020_2026.png
"""
import json, numpy as np, pandas as pd, pystac_client, planetary_computer as pc, rasterio
from rasterio.warp import transform_bounds, transform_geom
from rasterio.windows import from_bounds
from shapely.geometry import shape
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

res = pd.read_csv("analysis/data/scaleout/scaleout_status.csv")
flag = res[res.condition != "stable"].sort_values("area_ha", ascending=False)
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)


def pick_date(grp, sid, year):
    s = pd.read_csv(f"analysis/data/scaleout/{grp}_stats.csv"); s = s[(s.stand == sid) & s.mndwi_p50.notna()]
    for y in (year, year + 1):                                            # 2020 has few clean summer dates for some stands -> fall back to 2021
        c = s[(s.date.str[:4] == str(y)) & s.date.str[5:7].isin(["05", "06", "07", "08", "09"]) & (s.valid_frac >= 0.95)]   # same season in both years
        if len(c): return c.sort_values("mndwi_p50").iloc[0]["id"]
    raise ValueError(f"no clean May-Sep date for {sid} in {year}/{year + 1}")


fig, ax = plt.subplots(len(flag), 2, figsize=(10, 4.6 * len(flag)))
for r, row in enumerate(flag.itertuples()):
    gj = json.load(open(f"analysis/data/scaleout/{row.group}_stands.geojson"))
    geoms = [f["geometry"] for f in gj["features"] if f["properties"]["stand"] == row.stand]
    b = np.array([shape(g).bounds for g in geoms]); bb = [b[:, 0].min(), b[:, 1].min(), b[:, 2].max(), b[:, 3].max()]
    pad = max(bb[2] - bb[0], bb[3] - bb[1]) * 0.35 + 0.004; bb = [bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad]
    for c, year in enumerate((2020, 2026)):
        item = pc.sign(cat.get_collection("sentinel-2-l2a").get_item(pick_date(row.group, row.stand, year)))
        off = 1000.0 if float(item.properties.get("s2:processing_baseline", "4.0")) >= 4.0 else 0.0
        bands = []
        for k in ("B04", "B03", "B02"):                                   # same reflectance stretch for both years (TCI clips bright scenes)
            with rasterio.open(item.assets[k].href) as ds:
                win = from_bounds(*transform_bounds("EPSG:4326", ds.crs, *bb), ds.transform)
                bands.append((ds.read(1, window=win).astype("float32") - off) / 10000.0); tr = ds.window_transform(win); crs = ds.crs
        img = np.clip(np.stack(bands, -1) / 0.25, 0, 1) ** 0.8
        a = ax[r, c]; a.imshow(img); a.axis("off")
        for g in geoms:
            gg = transform_geom("EPSG:4326", crs, g)
            for ring in ([gg["coordinates"][0]] if gg["type"] == "Polygon" else [p[0] for p in gg["coordinates"]]):
                xy = np.array(ring); col, rw = ~tr * (xy[:, 0], xy[:, 1]); a.plot(col, rw, "-", color="yellow", lw=1.2)
        a.set_title(f"{row.stand} ({row.area_ha:.0f} ha)  {item.datetime.date()}", fontsize=10)
plt.tight_layout(); plt.savefig("analysis/figures/scaleout_declines_2020_2026.png", dpi=85)
print("saved analysis/figures/scaleout_declines_2020_2026.png for", list(flag.stand))
