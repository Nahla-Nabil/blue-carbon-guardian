"""Module 3, step 2: what does hyperspectral (EnMAP) tell us that Sentinel-2 cannot, and does it agree where both see the same thing?

Q1 spectra   : mean spectra of pure-mangrove pixels vs WorldCover reference classes (Nov 2022 scene)
Q2 consistency: EnMAP-derived S2-like indices vs our Sentinel-2 stand medians on (almost) the same date -> validates the S2 chain
Q3 stand 5   : pixel-level two-epoch comparison (2022-11 vs 2025-04): converted vs persistent-vegetation pixels, area estimate, spectra of both groups
Q4 separability: RF (spatial-block CV) mangrove vs other vegetation using S2-like bands vs the full EnMAP spectrum
Attribution: figures/tables derived from EnMAP must be marked "Contains modified EnMAP data (c)DLR 2022 / 2025".
"""
import json, numpy as np, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from scipy.stats import pearsonr, spearmanr
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import importlib.util
spec = importlib.util.spec_from_file_location("er", "analysis/17_enmap_reader.py"); er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)

rng = np.random.default_rng(9)
S = {}
for tag in ("e20221101", "e20250414"):
    sc = er.load_scene(tag); R = er.reflectance(sc); wl = sc["wl"]
    ind = er.indices(R, wl); frac = er.mangrove_fraction(sc); masks = er.stand_masks(sc)
    S[tag] = dict(sc=sc, R=R, wl=wl, ind=ind, frac=frac, masks=masks, ok=er.good_band_mask(wl))
    print(tag, "loaded", flush=True)

# ---------------- Q1: spectra vs reference classes (2022 scene) -------------------------------------------------------------------------------------
from rasterio.transform import Affine
g = json.load(open("analysis/data/grid.json")); wc = np.load("analysis/data/worldcover_grid.npy"); src_tr = Affine(*g["transform"])


def class_frac(sc, classes):
    out = np.zeros((sc["H"], sc["W"]), "float32")
    reproject(np.isin(wc, classes).astype("float32"), out, src_transform=src_tr, src_crs=g["crs"], dst_transform=sc["transform"], dst_crs=sc["crs"], resampling=Resampling.average)
    return out


A = S["e20221101"]; R, wl, ok = A["R"], A["wl"], A["ok"]
classes = {"Mangrove (WorldCover)": [95], "Other vegetation (tree/shrub/grass/wetland)": [10, 20, 30, 40, 90], "Bare / sparse (sabkha, sand)": [60], "Built-up": [50]}
CF = {k: class_frac(A["sc"], v) for k, v in classes.items()}
valid = np.isfinite(R[[int(np.argmin(abs(wl - x))) for x in (560, 665, 865, 1650)]]).all(axis=0)
fig, ax = plt.subplots(1, 2, figsize=(15, 5))
cols = ["#0B7A66", "#C98A10", "#8a8a8a", "#7A2E8E"]; cnt = {}
for (k, cf), c in zip(CF.items(), cols):
    m = (cf >= 0.8) & valid; cnt[k] = int(m.sum())
    if m.sum() < 20: continue
    sp = np.nanmean(R[:, m], axis=1); sd = np.nanstd(R[:, m], axis=1)
    x = np.where(ok, wl, np.nan); ax[0].plot(x, np.where(ok, sp, np.nan), color=c, lw=2, label=f"{k} (n={m.sum()})"); ax[0].fill_between(x, sp - sd, sp + sd, color=c, alpha=.12, lw=0)
ax[0].set_xlabel("wavelength (nm)"); ax[0].set_ylabel("surface reflectance"); ax[0].set_title("EnMAP spectra by WorldCover class, 1 Nov 2022"); ax[0].legend(fontsize=8, frameon=False)
print("Q1 pixel counts (fraction>=0.8):", cnt)
sp_tab = pd.read_csv("analysis/data/enmap_stand_spectra.csv"); s22 = sp_tab[(sp_tab.scene == "e20221101") & (sp_tab.n_pix >= 5)]
rc = [c for c in sp_tab.columns if c.startswith("r") and c[1:].replace(".", "").isdigit()]; xs = np.array([float(c[1:]) for c in rc]); okx = er.good_band_mask(xs)
for _, r in s22.iterrows(): ax[1].plot(np.where(okx, xs, np.nan), np.where(okx, r[rc].values.astype(float), np.nan), color="#0B7A66", alpha=.35, lw=1)
ax[1].set_xlabel("wavelength (nm)"); ax[1].set_title(f"Mean spectrum of each of {len(s22)} mangrove stands (pure pixels)"); ax[1].set_ylim(0, 0.6)
fig.text(.99, .01, "Contains modified EnMAP data (c)DLR 2022", ha="right", fontsize=8, color="gray"); plt.tight_layout(); plt.savefig("analysis/18_enmap_spectra.png", dpi=110); plt.close()

# ---------------- Q2: cross-sensor consistency with Sentinel-2 -------------------------------------------------------------------------------------
s2 = pd.read_csv("analysis/data/s2_stands_stats.csv"); s2["date"] = pd.to_datetime(s2["date"]); s2 = s2[s2.valid_frac >= 0.7].dropna(subset=["ndvi_p50", "ndmi_p50", "ndre_p50"])
out2 = []
for tag, day in (("e20221101", "2022-11-01"), ("e20250414", "2025-04-14")):
    B = S[tag]; ind = B["ind"]; rows = []
    d0 = pd.Timestamp(day); near = s2[(s2.date - d0).abs() <= pd.Timedelta(days=3)]
    best = near.assign(dd=(near.date - d0).abs()).sort_values("dd"); use_date = best.date.iloc[0] if len(best) else None
    print(f"\nQ2 {tag}: nearest S2 date within 3 days -> {use_date.date() if use_date is not None else 'none'}")
    if use_date is None: continue
    ss = near[near.date == use_date].set_index("stand")
    for k, m in B["masks"].items():
        pure = m & (B["frac"] >= 0.7) & np.isfinite(ind["NDVI_s2"]) & np.isfinite(ind["NDMI_s2"])
        if pure.sum() < 5 or k not in ss.index: continue
        rows.append(dict(stand=k, n=int(pure.sum()), en_ndvi=float(np.nanmedian(ind["NDVI_s2"][pure])), en_ndmi=float(np.nanmedian(ind["NDMI_s2"][pure])), en_ndre=float(np.nanmedian(ind["NDRE_s2"][pure])),
                         en_mndwi=float(np.nanmedian(ind["MNDWI_s2"][pure])), s2_ndvi=ss.loc[k, "ndvi_p50"], s2_ndmi=ss.loc[k, "ndmi_p50"], s2_ndre=ss.loc[k, "ndre_p50"], s2_mndwi=ss.loc[k, "mndwi_p50"]))
    d = pd.DataFrame(rows); d["scene"] = tag; out2.append(d)
    print(f"  stands compared: {len(d)}")
    for nm in ("ndvi", "ndmi", "ndre", "mndwi"):
        r = pearsonr(d[f"en_{nm}"], d[f"s2_{nm}"])[0]; rs = spearmanr(d[f"en_{nm}"], d[f"s2_{nm}"])[0]; bias = (d[f"s2_{nm}"] - d[f"en_{nm}"]).mean()
        print(f"  {nm:6s}: Pearson r={r:+.2f}  Spearman={rs:+.2f}  mean(S2-EnMAP)={bias:+.3f}")
pd.concat(out2).to_csv("analysis/data/enmap_vs_s2_stands.csv", index=False)

# ---------------- Q3: stand 5, two epochs -------------------------------------------------------------------------------------------------------------
a, b = S["e20221101"], S["e20250414"]
def to_grid(arr, src, dst, resamp=Resampling.nearest):
    out = np.full((dst["sc"]["H"], dst["sc"]["W"]), np.nan, "float32")
    reproject(arr.astype("float32"), out, src_transform=src["sc"]["transform"], src_crs=src["sc"]["crs"], dst_transform=dst["sc"]["transform"], dst_crs=dst["sc"]["crs"], resampling=resamp, src_nodata=np.nan, dst_nodata=np.nan)
    return out
m5 = a["masks"][5] & (a["frac"] >= 0.5)
v22 = a["ind"]["NDVI_s2"]; v25 = to_grid(b["ind"]["NDVI_s2"], b, a)
valid5 = m5 & np.isfinite(v22) & np.isfinite(v25)
converted = valid5 & (v22 >= 0.25) & (v25 < 0.15); persist = valid5 & (v22 >= 0.25) & (v25 >= 0.25)
print(f"\nQ3 stand 5: {m5.sum()} mangrove-pixels (fraction>=0.5), {valid5.sum()} valid in both epochs -> converted {converted.sum()} ({converted.sum() * 0.09:.1f} ha), persistent vegetation {persist.sum()} ({persist.sum() * 0.09:.1f} ha), other {valid5.sum() - converted.sum() - persist.sum()}")
print(f"   share of valid pixels converted: {100 * converted.sum() / max(valid5.sum(), 1):.0f} % (S2 epoch-difference indicator said 18.9 % of the outline / 26 ha)")
grp = {"persistent": persist, "converted": converted}
fig, ax = plt.subplots(1, 3, figsize=(17, 4.8)); stats = {}
for name, mk in grp.items():
    mk25 = to_grid(mk.astype("float32"), a, b) > 0.5 if False else None
# spectra of the same 2022-grid groups in the 2025 scene: map pixel centres
from rasterio.transform import rowcol
def spectra_for(mask22, B):
    rr, cc = np.nonzero(mask22); xs, ys = rasterio.transform.xy(a["sc"]["transform"], rr, cc)
    r2, c2 = rowcol(B["sc"]["transform"], xs, ys); r2, c2 = np.array(r2), np.array(c2)
    okp = (r2 >= 0) & (r2 < B["sc"]["H"]) & (c2 >= 0) & (c2 < B["sc"]["W"]); return np.nanmean(B["R"][:, r2[okp], c2[okp]], axis=1), int(okp.sum())
for name, mk in grp.items():
    for tag, B, ls in (("2022-11", a, "-"), ("2025-04", b, "--")):
        sp, n = spectra_for(mk, B); x = np.where(B["ok"], B["wl"], np.nan)
        ax[0 if name == "persistent" else 1].plot(x, np.where(B["ok"], sp, np.nan), ls, lw=2, label=f"{tag} (n={n})", color="#0B7A66" if tag == "2022-11" else "#C8384F")
        stats[(name, tag)] = sp
    ax[0 if name == "persistent" else 1].set_title(f"Stand 5 - {name} pixels"); ax[0 if name == "persistent" else 1].legend(frameon=False); ax[0 if name == "persistent" else 1].set_xlabel("wavelength (nm)")
ax[0].set_ylabel("reflectance")
rgb = np.stack([np.clip(np.nan_to_num(er.band_at(a["R"], a["wl"], w)) / 0.25, 0, 1) for w in (665, 560, 490)], -1) ** .7
r0, r1 = np.nonzero(a["masks"][5])[0].min() - 15, np.nonzero(a["masks"][5])[0].max() + 15; c0, c1 = np.nonzero(a["masks"][5])[1].min() - 15, np.nonzero(a["masks"][5])[1].max() + 15
ov = rgb.copy(); ov[converted] = (1, 0, .2); ov[persist] = (0, .9, .3); ax[2].imshow(ov[r0:r1, c0:c1]); ax[2].set_title("Stand 5 on EnMAP 2022 grid: converted (red) / persistent (green)"); ax[2].axis("off")
fig.text(.99, .01, "Contains modified EnMAP data (c)DLR 2022, 2025", ha="right", fontsize=8, color="gray"); plt.tight_layout(); plt.savefig("analysis/18_enmap_stand5.png", dpi=110); plt.close()
# persistent-vegetation change in hyperspectral features (exploratory: Nov vs Apr = season confounded)
for nm in ("REP", "WBI", "NDII1650", "NDVI_s2"):
    x22 = a["ind"][nm][persist]; x25 = to_grid(b["ind"][nm], b, a)[persist]
    print(f"   persistent pixels {nm:9s}: 2022 mean {np.nanmean(x22):.3f} -> 2025 mean {np.nanmean(x25):.3f}  (paired diff {np.nanmean(x25 - x22):+.3f})")

# ---------------- Q4: separability, EnMAP full spectrum vs S2-like bands -------------------------------------------------------------------------
pos = (A["frac"] >= 0.8) & valid; neg = (CF["Other vegetation (tree/shrub/grass/wetland)"] >= 0.8) & valid
print(f"\nQ4 pixels: mangrove {pos.sum()}, other vegetation {neg.sum()}")
if neg.sum() >= 100 and pos.sum() >= 100:
    n = min(pos.sum(), neg.sum(), 2500); ip = rng.choice(np.flatnonzero(pos.ravel()), n, replace=False); ineg = rng.choice(np.flatnonzero(neg.ravel()), n, replace=False)
    idx = np.r_[ip, ineg]; y = np.r_[np.ones(n), np.zeros(n)]; rr, cc = np.divmod(idx, A["sc"]["W"]); grp_id = (rr // 25) * 1000 + (cc // 25)         # ~750 m spatial blocks
    Xfull = R[ok][:, rr, cc].T; s2b = er.s2_like(R, wl); Xs2 = np.stack([v[rr, cc] for v in s2b.values()], 1)
    ok_rows = (np.isfinite(Xfull).mean(1) >= 0.95) & np.isfinite(Xs2).all(1); Xfull, Xs2, y, grp_id = Xfull[ok_rows], Xs2[ok_rows], y[ok_rows], grp_id[ok_rows]
    Xfull = np.where(np.isfinite(Xfull), Xfull, np.nanmedian(Xfull, axis=0)[None, :])          # fill the few missing bands with the band median
    res = {}
    for nm, X in (("S2-like 7 bands", Xs2), ("EnMAP full spectrum", Xfull)):
        f1 = []
        for trn, tst in GroupKFold(5).split(X, y, grp_id):
            m = RandomForestClassifier(200, min_samples_leaf=3, n_jobs=-1, random_state=1).fit(X[trn], y[trn]); f1.append(f1_score(y[tst], m.predict(X[tst])))
        res[nm] = (np.mean(f1), np.std(f1)); print(f"   {nm:22s}: spatial-block CV F1 = {np.mean(f1):.3f} +/- {np.std(f1):.3f}  (n={len(y)}, {len(np.unique(grp_id))} blocks)")
else:
    print("   too few pixels for a separability test")
