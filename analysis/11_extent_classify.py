"""Module 1, step 2: updated mangrove extent (2021 vs 2025) from Sentinel-2 composites, with an honest validation.

Method (simple, explainable baseline first - organizer rule): Random Forest on 10 reflectance bands + NDVI/NDRE/NDMI/MNDWI of the LOW-TIDE 2021 composite,
trained on ESA WorldCover-2021 labels (mangrove core vs non-mangrove away from mangrove), then applied to the 2021 and 2025 composites.
Caveat: the training labels are themselves a model product, so the RF inherits some of its errors. Independence check = our reference points
(AI-assisted photo-interpretation of VHR imagery, blind) that fall inside the region; agreement is reported with bootstrap CIs.
Validation uses spatial 1 km blocks (no random pixel splits). Outputs: GeoTIFFs, stand table, summary markdown, figure.
"""
import json, numpy as np, pandas as pd, rasterio
from rasterio.transform import Affine, rowcol
from rasterio.warp import transform as warp_transform
from rasterio.features import rasterize
from scipy import ndimage as ndi
from shapely.geometry import shape
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

rng = np.random.default_rng(3)
g = json.load(open("analysis/data/grid.json")); H, W = g["H"], g["W"]; tr = Affine(*g["transform"]); crs = g["crs"]
wc = np.load("analysis/data/worldcover_grid.npy")
C = {y: np.load(f"analysis/data/composite_{y}.npz")["comp"] for y in (2021, 2025)}
PIXEL_HA = 0.01


def features(comp):
    b = dict(zip(["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"], comp))
    ndvi = (b["B08"] - b["B04"]) / (b["B08"] + b["B04"] + 1e-6); ndre = (b["B8A"] - b["B05"]) / (b["B8A"] + b["B05"] + 1e-6)
    ndmi = (b["B8A"] - b["B11"]) / (b["B8A"] + b["B11"] + 1e-6); mndwi = (b["B03"] - b["B11"]) / (b["B03"] + b["B11"] + 1e-6)
    return np.concatenate([comp, np.stack([ndvi, ndre, ndmi, mndwi])], axis=0)


# ---- radiometric consistency between epochs: pseudo-invariant bare-ground pixels (WorldCover class 60, no mangrove nearby) -------------------
mang = wc == 95
far = ~ndi.binary_dilation(mang, iterations=30)
pif = (wc == 60) & far
print("PIF pixels:", int(pif.sum()))
ratio = []
for k, name in enumerate(["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]):
    a, b = np.nanmedian(C[2021][k][pif]), np.nanmedian(C[2025][k][pif]); ratio.append(a / b if b > 0 else 1.0)
    print(f"  {name}: 2021 {a:.4f} | 2025 {b:.4f} | ratio 2021/2025 = {a / b:.3f}")
ratio = np.array(ratio)
NORMALISE = bool(np.max(np.abs(ratio - 1)) > 0.05)
print("normalise 2025 to 2021 with per-band gains:", NORMALISE)
if NORMALISE: C[2025] = C[2025] * ratio[:, None, None]
F = {y: features(C[y]) for y in C}; valid = {y: np.isfinite(F[y]).all(axis=0) for y in C}

# ---- training sample from WorldCover-2021 -----------------------------------------------------------------------------------------------------
core = ndi.binary_erosion(mang, iterations=1)
neg_ok = (~ndi.binary_dilation(mang, iterations=2)) & (wc > 0) & valid[2021]
pos_idx = np.flatnonzero((core & valid[2021]).ravel()); pos_idx = rng.choice(pos_idx, min(40000, len(pos_idx)), replace=False)
neg = []
for cl in np.unique(wc[neg_ok]):
    idx = np.flatnonzero((neg_ok & (wc == cl)).ravel()); neg.append(rng.choice(idx, min(6000, len(idx)), replace=False))
neg_idx = np.concatenate(neg)
idx = np.concatenate([pos_idx, neg_idx]); y = np.r_[np.ones(len(pos_idx)), np.zeros(len(neg_idx))]
X = F[2021].reshape(F[2021].shape[0], -1).T[idx]
rows, cols = np.divmod(idx, W); groups = (rows // 100) * 100 + (cols // 100)                   # 1 km spatial blocks
print(f"training pixels: {len(pos_idx)} mangrove + {len(neg_idx)} other, {len(np.unique(groups))} spatial blocks")
oa = []
for trn, tst in GroupKFold(5).split(X, y, groups):
    m = RandomForestClassifier(150, min_samples_leaf=5, n_jobs=-1, random_state=1).fit(X[trn], y[trn]); oa.append(f1_score(y[tst], m.predict(X[tst])))
print(f"spatial-block CV F1 vs WorldCover labels (consistency only): {np.mean(oa):.3f} +/- {np.std(oa):.3f}")
rf = RandomForestClassifier(300, min_samples_leaf=5, n_jobs=-1, random_state=1).fit(X, y)
imp = pd.Series(rf.feature_importances_, index=["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "NDVI", "NDRE", "NDMI", "MNDWI"]).sort_values(ascending=False)
print("top features:", imp.head(5).round(3).to_dict())


def predict(y_):
    flat = F[y_].reshape(F[y_].shape[0], -1).T; p = np.zeros(H * W, "float32"); ok = valid[y_].ravel()
    p[ok] = rf.predict_proba(flat[ok])[:, 1]
    m = (p.reshape(H, W) >= 0.5)
    lab, n = ndi.label(m); sz = np.bincount(lab.ravel()); m = m & (sz[lab] >= 5)               # drop speckle < 0.05 ha
    return p.reshape(H, W), m


P = {}; M = {}
for y_ in (2021, 2025): P[y_], M[y_] = predict(y_)
print("mangrove area in region (ha): WorldCover-2021 %.0f | RF-2021 %.0f | RF-2025 %.0f" % (mang.sum() * PIXEL_HA, M[2021].sum() * PIXEL_HA, M[2025].sum() * PIXEL_HA))
gain = M[2025] & ~M[2021]; loss = M[2021] & ~M[2025]; stay = M[2021] & M[2025]
print("change 2021->2025 (RF): stable %.0f ha | loss %.0f ha | gain %.0f ha" % (stay.sum() * PIXEL_HA, loss.sum() * PIXEL_HA, gain.sum() * PIXEL_HA))

# ---- independent check against reference points inside the region --------------------------------------------------------------------------------
lab = pd.read_csv("labeling/returned/labels_Claude_AI.csv")
xs, ys = warp_transform("EPSG:4326", crs, lab.lon.tolist(), lab.lat.tolist())
r_, c_ = rowcol(tr, xs, ys); lab["r"], lab["c"] = r_, c_
lab = lab[(lab.r.between(0, H - 1)) & (lab.c.between(0, W - 1)) & (lab.label != "unsure")].copy()
lab["ref"] = lab.label.isin(["mangrove_healthy", "mangrove_degraded"]).astype(int)
for nm, mp in [("WorldCover-2021", mang), ("RF-2021", M[2021]), ("RF-2025", M[2025])]:
    lab[nm] = mp[lab.r.values, lab.c.values].astype(int)


def metrics(d, col):
    ref, pr = d.ref.values, d[col].values; tp = ((ref == 1) & (pr == 1)).sum(); fp = ((ref == 0) & (pr == 1)).sum(); fn = ((ref == 1) & (pr == 0)).sum(); tn = ((ref == 0) & (pr == 0)).sum()
    f1 = 2 * tp / max(2 * tp + fp + fn, 1); iou = tp / max(tp + fp + fn, 1); bs = []
    for _ in range(1000):
        ii = rng.integers(0, len(d), len(d)); r2, p2 = ref[ii], pr[ii]; t = ((r2 == 1) & (p2 == 1)).sum()
        bs.append(2 * t / max(2 * t + ((r2 == 0) & (p2 == 1)).sum() + ((r2 == 1) & (p2 == 0)).sum(), 1))
    return dict(n=len(d), TP=tp, FP=fp, FN=fn, TN=tn, OA=round((tp + tn) / len(d), 3), precision=round(tp / max(tp + fp, 1), 3), recall=round(tp / max(tp + fn, 1), 3),
                F1=round(f1, 3), F1_CI95=f"{np.percentile(bs, 2.5):.2f}-{np.percentile(bs, 97.5):.2f}", IoU=round(iou, 3))


tabs = {}
for tag, d in [("all confident>=1", lab), ("confidence>=2", lab[lab.confidence_1to3 >= 2])]:
    tabs[tag] = pd.DataFrame({nm: metrics(d, nm) for nm in ["WorldCover-2021", "RF-2021", "RF-2025"]}).T
    print(f"\nAgreement with AI-assisted reference points inside the region - {tag}:\n", tabs[tag].to_string())

# ---- per-stand table + GeoTIFFs + figure --------------------------------------------------------------------------------------------------------
gj = json.load(open("analysis/data/stands.geojson")); st = pd.read_csv("analysis/data/stand_status.csv")[["stand", "area_ha"]]
rows = []
for f in gj["features"]:
    k = f["properties"]["stand"]
    from rasterio.warp import transform_geom
    geom = transform_geom("EPSG:4326", crs, f["geometry"])
    m = rasterize([(geom, 1)], out_shape=(H, W), transform=tr, fill=0, dtype="uint8").astype(bool)
    rows.append(dict(stand=k, wc2021_ha=round(m.sum() * PIXEL_HA, 1), rf2021_ha=round((m & M[2021]).sum() * PIXEL_HA, 1), rf2025_ha=round((m & M[2025]).sum() * PIXEL_HA, 1)))
tab = pd.DataFrame(rows).sort_values("stand"); tab["change_ha"] = (tab.rf2025_ha - tab.rf2021_ha).round(1)
tab["change_pct"] = (100 * tab.change_ha / tab.rf2021_ha.replace(0, np.nan)).round(1); tab.to_csv("analysis/data/extent_by_stand.csv", index=False)
print("\nstands with the largest change (ha):\n", tab.reindex(tab.change_ha.abs().sort_values(ascending=False).index).head(6).to_string(index=False))
prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="uint8", crs=crs, transform=tr, compress="lzw")
for nm, arr in [("rf_mangrove_2021", M[2021]), ("rf_mangrove_2025", M[2025]), ("rf_change_2021_2025", (gain * 2 + loss * 3 + stay * 1))]:
    with rasterio.open(f"analysis/data/{nm}.tif", "w", **prof) as dst: dst.write(arr.astype("uint8"), 1)
rgb = np.clip(np.stack([C[2025][2], C[2025][1], C[2025][0]], -1) / 0.25, 0, 1) ** 0.7
fig, ax = plt.subplots(1, 4, figsize=(20, 5.2)); [a.axis("off") for a in ax]
ax[0].imshow(rgb); ax[0].set_title("Sentinel-2 low-tide composite 2025"); ax[1].imshow(mang, cmap="Greens"); ax[1].set_title(f"WorldCover 2021 ({mang.sum() * PIXEL_HA:.0f} ha)")
ax[2].imshow(M[2025], cmap="Greens"); ax[2].set_title(f"RF 2025 ({M[2025].sum() * PIXEL_HA:.0f} ha)")
cm = np.zeros((H, W, 3)); cm[stay] = (.35, .65, .45); cm[loss] = (.85, .2, .3); cm[gain] = (.2, .45, .85); ax[3].imshow(cm); ax[3].set_title("Change 2021-2025: loss red, gain blue")
plt.tight_layout(); plt.savefig("analysis/11_extent.png", dpi=95)
with open("analysis/11_extent_summary.md", "w", encoding="utf-8") as fh:
    NL = chr(10)
    fh.write("# Module 1 results" + NL + NL + f"Spatial-block CV F1 vs WorldCover labels (consistency only): {np.mean(oa):.3f}" + NL + NL)
    fh.write(f"Area (ha): WorldCover-2021 {mang.sum() * PIXEL_HA:.0f} | RF-2021 {M[2021].sum() * PIXEL_HA:.0f} | RF-2025 {M[2025].sum() * PIXEL_HA:.0f}; loss {loss.sum() * PIXEL_HA:.0f}, gain {gain.sum() * PIXEL_HA:.0f}" + NL + NL)
    for tag, t in tabs.items(): fh.write(f"## Agreement with AI-assisted reference points ({tag})" + NL + t.to_markdown() + NL + NL)
    fh.write("## Change by stand" + NL + tab.to_markdown(index=False) + NL)
print("saved figure + tables")
