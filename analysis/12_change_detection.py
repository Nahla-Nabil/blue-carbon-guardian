"""Module 1, step 3: pixel-level CHANGE indicator 2021 -> 2025 that does not depend on absolute reflectance transfer.

Why: analysis/11 showed that a classifier trained on the 2021 composite fails on the 2025 composite (radiometric/seasonal mismatch: -70 % "loss").
Here we use ratio indices (NDVI, NDMI) on the two low-tide composites, per-band gain normalisation on pseudo-invariant bare ground, and a ROBUST z-score of the
difference computed on WorldCover-mangrove pixels, so uniform shifts cancel out. A pixel is 'loss' when both indices fall by >= 0.15 AND robust z <= -3 for both.
Outputs: analysis/data/change_by_stand.csv, analysis/12_change.png, GeoTIFF analysis/data/change_indicator_2021_2025.tif
"""
import json, numpy as np, pandas as pd, rasterio
from rasterio.transform import Affine
from rasterio.features import rasterize
from rasterio.warp import transform_geom
from scipy import ndimage as ndi
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

g = json.load(open("analysis/data/grid.json")); H, W = g["H"], g["W"]; tr = Affine(*g["transform"]); crs = g["crs"]
wc = np.load("analysis/data/worldcover_grid.npy"); C = {y: np.load(f"analysis/data/composite_{y}.npz")["comp"] for y in (2021, 2025)}
mang = wc == 95; pif = (wc == 60) & ~ndi.binary_dilation(mang, iterations=30)
gain = np.array([np.nanmedian(C[2021][k][pif]) / np.nanmedian(C[2025][k][pif]) for k in range(10)]); C[2025] = C[2025] * gain[:, None, None]


def idx(c):
    b04, b08, b8a, b11 = c[2], c[6], c[7], c[8]
    return (b08 - b04) / (b08 + b04 + 1e-6), (b8a - b11) / (b8a + b11 + 1e-6)


nv21, nm21 = idx(C[2021]); nv25, nm25 = idx(C[2025]); dv, dm = nv25 - nv21, nm25 - nm21
ok = np.isfinite(dv) & np.isfinite(dm)
ref = mang & ok
def rz(d):
    med = np.median(d[ref]); mad = 1.4826 * np.median(np.abs(d[ref] - med)); return (d - med) / (mad + 1e-9), med, mad
zv, mv, sv = rz(dv); zm, mm, sm = rz(dm)
print(f"median change on mangrove pixels: dNDVI {mv:+.3f} (robust sd {sv:.3f}) | dNDMI {mm:+.3f} (robust sd {sm:.3f})")
loss = ok & (dv <= -0.15) & (dm <= -0.15) & (zv <= -3) & (zm <= -3)
lab, n = ndi.label(loss); sz = np.bincount(lab.ravel()); loss = loss & (sz[lab] >= 5)
gain_px = ok & (dv >= 0.15) & (dm >= 0.15) & (zv >= 3) & (zm >= 3); lab, n = ndi.label(gain_px); sz = np.bincount(lab.ravel()); gain_px = gain_px & (sz[lab] >= 5)
print(f"region: loss {loss.sum() * .01:.0f} ha ({(loss & mang).sum() * .01:.0f} ha on WorldCover-mangrove pixels), gain {gain_px.sum() * .01:.0f} ha")

gj = json.load(open("analysis/data/stands.geojson")); rows = []
for f in gj["features"]:
    k = f["properties"]["stand"]; m = rasterize([(transform_geom("EPSG:4326", crs, f["geometry"]), 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    rows.append(dict(stand=k, area_ha=round(m.sum() * .01, 1), loss_ha=round((m & loss).sum() * .01, 1), loss_pct=round(100 * (m & loss).sum() / max(m.sum(), 1), 1),
                     median_dNDVI=round(float(np.median(dv[m & ok])), 3), median_dNDMI=round(float(np.median(dm[m & ok])), 3)))
tab = pd.DataFrame(rows).sort_values("loss_pct", ascending=False); tab.to_csv("analysis/data/change_by_stand.csv", index=False)
print(tab.head(8).to_string(index=False)); print("median loss % of the other 24 stands:", tab[tab.stand != 5].loss_pct.median())
with rasterio.open("analysis/data/change_indicator_2021_2025.tif", "w", driver="GTiff", height=H, width=W, count=1, dtype="uint8", crs=crs, transform=tr, compress="lzw") as d:
    d.write((loss * 1 + gain_px * 2).astype("uint8"), 1)
rgb = lambda c: np.clip(np.stack([c[2], c[1], c[0]], -1) / 0.3, 0, 1) ** 0.75
fig, ax = plt.subplots(1, 3, figsize=(19, 5.6)); [a.axis("off") for a in ax]
ax[0].imshow(rgb(C[2021])); ax[0].set_title("Low-tide composite 2021"); ax[1].imshow(rgb(C[2025])); ax[1].set_title("Low-tide composite 2025")
o = rgb(C[2025]).copy(); o[loss] = (1, 0, .2); o[gain_px] = (0, .4, 1); ax[2].imshow(o); ax[2].set_title("Change indicator: loss red, gain blue")
plt.tight_layout(); plt.savefig("analysis/12_change.png", dpi=90); print("saved")
