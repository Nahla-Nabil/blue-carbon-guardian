"""Simulated Satellite 813: does our hyperspectral step still work with only the 813 spectral range?

Satellite 813 (planned, not available in the PoC): ~205 bands, ~400-1700 nm, ~5 nm sampling, 20 m. We simulate its SPECTRAL range by keeping
only the EnMAP bands inside 400-1700 nm (water-vapour window 1340-1460 nm removed, as for the full spectrum). What this is NOT:
  - not real 813 data (no 813 noise, calibration or band shapes);
  - not 813 spatial detail: the cube stays at EnMAP's 30 m (813 is 20 m), so the spatial side is conservative;
  - not finer spectral sampling: EnMAP samples ~6.5 nm (VNIR) / ~10 nm (SWIR), coarser than 813's ~5 nm.
Tests (same scenes, pixels and stand-5 groups as analysis/18):
  T1 monitor indices  : which bands the monitor needs, and whether they all sit inside the 813 range
  T2 fingerprint      : stand-5 converted vs persistent pixels, spectral-angle change 2022 -> 2025, and which reference class each pixel's 2025 spectrum is nearest to
  T3 area             : pixels that change from 'mangrove-like' (2022) to 'bare/built-like' (2025) by spectral-library matching, 813 range vs full spectrum
  T4 separability     : spatial-block-CV Random Forest F1, mangrove vs other vegetation AND bare (sand/sabkha) vs built-up, for S2-like bands / 813 range / full spectrum
Attribution: figures/tables derived from EnMAP must be marked "Contains modified EnMAP data (c)DLR 2022 / 2025".
Run from the repository root: python analysis/36_sat813_sim.py   -> analysis/36_sat813_sim.png, analysis/data/sat813_sim.json
"""
import json, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import Affine, rowcol
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import importlib.util
spec = importlib.util.spec_from_file_location("er", "analysis/17_enmap_reader.py"); er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)

R813 = (400, 1700)
rng = np.random.default_rng(9)
S = {}
for tag in ("e20221101", "e20250414"):
    sc = er.load_scene(tag); R = er.reflectance(sc); wl = sc["wl"]
    ok = er.good_band_mask(wl)
    S[tag] = dict(sc=sc, R=R, wl=wl, ok=ok, ok813=ok & (wl >= R813[0]) & (wl <= R813[1]), ind=er.indices(R, wl), frac=er.mangrove_fraction(sc), masks=er.stand_masks(sc))
    print(tag, "loaded:", ok.sum(), "usable bands,", S[tag]["ok813"].sum(), "inside 400-1700 nm", flush=True)
a, b = S["e20221101"], S["e20250414"]
OUT = {"bands_full": int(a["ok"].sum()), "bands_813": int(a["ok813"].sum())}

# ---------------- T1: does the monitor need anything outside 813's range? -----------------------------------------------------------------------
S2_RANGES = dict(B03=(543, 578), B04=(650, 680), B05=(698, 713), B08=(785, 900), B8A=(855, 875), B11=(1565, 1655), B12=(2100, 2280))
USED = {"NDVI": ("B08", "B04"), "NDRE (red edge)": ("B8A", "B05"), "NDMI (SWIR moisture)": ("B8A", "B11"), "MNDWI (wetness / tide)": ("B03", "B11")}
inside = {k: (lo >= R813[0] and hi <= R813[1]) for k, (lo, hi) in S2_RANGES.items()}
T1 = {idx: all(inside[bd] for bd in bands) for idx, bands in USED.items()}
OUT["T1_monitor_indices_inside_813"] = T1
OUT["T1_bands_outside_813"] = [k for k, v in inside.items() if not v]
print("\nT1 monitor indices inside 400-1700 nm:", T1, "| S2 bands outside:", OUT["T1_bands_outside_813"])

# ---------------- reference classes (WorldCover, pure pixels, 2022 grid) ------------------------------------------------------------------------
g = json.load(open("analysis/data/grid.json")); wc = np.load("analysis/data/worldcover_grid.npy"); src_tr = Affine(*g["transform"])
def class_frac(sc, classes):
    out = np.zeros((sc["H"], sc["W"]), "float32")
    reproject(np.isin(wc, classes).astype("float32"), out, src_transform=src_tr, src_crs=g["crs"], dst_transform=sc["transform"], dst_crs=sc["crs"], resampling=Resampling.average)
    return out
CLASSES = {"mangrove": [95], "other vegetation": [10, 20, 30, 40, 90], "bare / sand / sabkha": [60], "built-up": [50]}
R, wl = a["R"], a["wl"]
valid = np.isfinite(R[[int(np.argmin(abs(wl - x))) for x in (560, 665, 865, 1650)]]).all(axis=0)
CF = {k: class_frac(a["sc"], v) for k, v in CLASSES.items()}
PURE = {k: (cf >= 0.8) & valid for k, cf in CF.items()}
print("reference pixels:", {k: int(m.sum()) for k, m in PURE.items()})
REF = {k: np.nanmean(R[:, m], axis=1) for k, m in PURE.items()}           # reference spectra (2022 scene)


def sam(spec, ref, band_ok):
    """spectral angle (radians) between spectra [..., bands] and one reference spectrum, on the selected bands only."""
    x = spec[..., band_ok]; r = ref[band_ok]
    num = np.nansum(x * r, axis=-1); den = np.sqrt(np.nansum(x * x, axis=-1) * np.nansum(r * r)) + 1e-12
    return np.arccos(np.clip(num / den, -1, 1))


def nearest_class(spec, band_ok):
    names = list(REF); ang = np.stack([sam(spec, REF[k], band_ok) for k in names], -1)
    return np.array(names)[np.nanargmin(ang, axis=-1)]


# ---------------- T2 + T3: stand 5 two epochs ---------------------------------------------------------------------------------------------------
def to_grid(arr, src, dst):
    out = np.full((dst["sc"]["H"], dst["sc"]["W"]), np.nan, "float32")
    reproject(arr.astype("float32"), out, src_transform=src["sc"]["transform"], src_crs=src["sc"]["crs"], dst_transform=dst["sc"]["transform"], dst_crs=dst["sc"]["crs"],
              resampling=Resampling.nearest, src_nodata=np.nan, dst_nodata=np.nan)
    return out
m5 = a["masks"][5] & (a["frac"] >= 0.5)
v22 = a["ind"]["NDVI_s2"]; v25 = to_grid(b["ind"]["NDVI_s2"], b, a)
valid5 = m5 & np.isfinite(v22) & np.isfinite(v25)
converted = valid5 & (v22 >= 0.25) & (v25 < 0.15); persist = valid5 & (v22 >= 0.25) & (v25 >= 0.25)      # same groups as analysis/18


def spectra_2025(mask22):
    rr, cc = np.nonzero(mask22); xs, ys = rasterio.transform.xy(a["sc"]["transform"], rr, cc)
    r2, c2 = rowcol(b["sc"]["transform"], xs, ys); r2, c2 = np.array(r2), np.array(c2)
    okp = (r2 >= 0) & (r2 < b["sc"]["H"]) & (c2 >= 0) & (c2 < b["sc"]["W"])
    return R[:, rr[okp], cc[okp]].T, b["R"][:, r2[okp], c2[okp]].T          # [n, bands] 2022 and 2025


ok_full, ok_813 = a["ok"], a["ok813"]
T2 = {}
for gname, gm in (("converted", converted), ("persistent", persist)):
    s22, s25 = spectra_2025(gm)
    keep = np.isfinite(s22[:, ok_full]).mean(1) > .95
    keep &= np.isfinite(s25[:, ok_full]).mean(1) > .95
    s22, s25 = s22[keep], s25[keep]
    for bname, bo in (("full", ok_full), ("813", ok_813)):
        ang = np.array([sam(s25[i], s22[i], bo) for i in range(len(s22))])
        c25 = nearest_class(s25, bo); c22 = nearest_class(s22, bo)
        T2[f"{gname}_{bname}"] = dict(n=int(len(s22)), angle_change_deg=float(np.degrees(np.nanmedian(ang))),
                                      share_2022_mangrove=float(np.mean(c22 == "mangrove")),
                                      share_2025_bare_or_built=float(np.mean(np.isin(c25, ["bare / sand / sabkha", "built-up"]))))
    print(f"\nT2 stand 5, {gname} pixels (n={len(s22)}):")
    for bname in ("full", "813"):
        t = T2[f"{gname}_{bname}"]; print(f"   {bname:4s}: spectral-angle change median {t['angle_change_deg']:.1f} deg | 2022 nearest=mangrove {t['share_2022_mangrove']*100:.0f} % | 2025 nearest=bare/built {t['share_2025_bare_or_built']*100:.0f} %")
OUT["T2"] = T2

# T3: whole stand-5 outline, class change by spectral-library matching
rr, cc = np.nonzero(valid5); xs, ys = rasterio.transform.xy(a["sc"]["transform"], rr, cc)
r2, c2 = rowcol(b["sc"]["transform"], xs, ys); r2, c2 = np.array(r2), np.array(c2)
okp = (r2 >= 0) & (r2 < b["sc"]["H"]) & (c2 >= 0) & (c2 < b["sc"]["W"])
s22 = R[:, rr[okp], cc[okp]].T; s25 = b["R"][:, r2[okp], c2[okp]].T
keep = (np.isfinite(s22[:, ok_full]).mean(1) > .95) & (np.isfinite(s25[:, ok_full]).mean(1) > .95); s22, s25 = s22[keep], s25[keep]
T3 = {}
for bname, bo in (("full", ok_full), ("813", ok_813)):
    c22 = nearest_class(s22, bo); c25 = nearest_class(s25, bo)
    lost = (c22 == "mangrove") & np.isin(c25, ["bare / sand / sabkha", "built-up"])
    T3[bname] = dict(pixels=int(lost.sum()), ha=float(lost.sum() * 0.09)); T3[bname + "_labels"] = c25
agree = float(np.mean(T3["full_labels"] == T3["813_labels"]))
OUT["T3"] = {k: v for k, v in T3.items() if not k.endswith("_labels")}; OUT["T3"]["label_agreement_2025"] = agree
OUT["T3"]["ndvi_rule_converted_ha"] = float(converted.sum() * 0.09)
print(f"\nT3 stand 5 mangrove-like -> bare/built-like: full spectrum {T3['full']['ha']:.1f} ha | 813 range {T3['813']['ha']:.1f} ha | per-pixel 2025 label agreement {agree*100:.0f} % | (NDVI rule of analysis/18: {converted.sum()*0.09:.1f} ha)")

# ---------------- T4: separability (spatial-block CV) ---------------------------------------------------------------------------------------------
s2b = er.s2_like(R, wl)
def cv_f1(pos, neg, label):
    if pos.sum() < 100 or neg.sum() < 100: print(f"   {label}: too few pixels ({pos.sum()}, {neg.sum()})"); return None
    n = min(pos.sum(), neg.sum(), 2500); ip = rng.choice(np.flatnonzero(pos.ravel()), n, replace=False); ineg = rng.choice(np.flatnonzero(neg.ravel()), n, replace=False)
    idx = np.r_[ip, ineg]; y = np.r_[np.ones(n), np.zeros(n)]; rr, cc = np.divmod(idx, a["sc"]["W"]); gid = (rr // 25) * 1000 + (cc // 25)
    sets = {"S2-like (7 bands)": np.stack([v[rr, cc] for v in s2b.values()], 1),
            "S2-like inside 813 (6 bands, no B12)": np.stack([v[rr, cc] for k, v in s2b.items() if k != "B12"], 1),
            "813 range (EnMAP 400-1700 nm)": R[ok_813][:, rr, cc].T, "EnMAP full (420-2450 nm)": R[ok_full][:, rr, cc].T}
    rows_ok = np.ones(len(y), bool)
    for X in sets.values(): rows_ok &= np.isfinite(X).mean(1) >= 0.95
    res = {}
    for nm, X in sets.items():
        X = X[rows_ok]; X = np.where(np.isfinite(X), X, np.nanmedian(X, axis=0)[None, :]); yy, gg = y[rows_ok], gid[rows_ok]; f1 = []
        for trn, tst in GroupKFold(5).split(X, yy, gg):
            m = RandomForestClassifier(200, min_samples_leaf=3, n_jobs=-1, random_state=1).fit(X[trn], yy[trn]); f1.append(f1_score(yy[tst], m.predict(X[tst])))
        res[nm] = [float(np.mean(f1)), float(np.std(f1))]; print(f"   {label:34s} {nm:38s} F1 = {np.mean(f1):.3f} +/- {np.std(f1):.3f}")
    return dict(n=int(rows_ok.sum()), blocks=int(len(np.unique(gid[rows_ok]))), f1=res)
print("\nT4 spatial-block CV, Random Forest:")
OUT["T4_mangrove_vs_other_veg"] = cv_f1(PURE["mangrove"], PURE["other vegetation"], "mangrove vs other vegetation")
OUT["T4_bare_vs_built"] = cv_f1(PURE["bare / sand / sabkha"], PURE["built-up"], "bare/sand vs built-up")

json.dump(OUT, open("analysis/data/sat813_sim.json", "w"), indent=1)

# ---------------- figure ----------------------------------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(1, 3, figsize=(18, 5.2), gridspec_kw=dict(width_ratios=[1.1, 1.3, 1]))
x = np.where(ok_full, wl, np.nan)
for nm, c in (("mangrove", "#0B7A66"), ("bare / sand / sabkha", "#B08A3E"), ("built-up", "#7A2E8E")):
    ax[0].plot(x, np.where(ok_full, REF[nm], np.nan), color=c, lw=2, label=f"{nm} (n={PURE[nm].sum()})")
ax[0].axvspan(400, 1700, color="#1E6FD9", alpha=.07); ax[0].axvline(1700, color="#1E6FD9", ls="--", lw=1)
ax[0].text(1050, 0.03, "Satellite 813 range ~400-1700 nm", ha="center", va="bottom", color="#1E6FD9", fontsize=10)
ax[0].set_title("Reference spectra (EnMAP, 1 Nov 2022)"); ax[0].set_xlabel("wavelength (nm)"); ax[0].set_ylabel("reflectance"); ax[0].legend(frameon=False, fontsize=9, loc="upper right")
cs22, cs25 = spectra_2025(converted)
for sp, c, lab in ((np.nanmean(cs22, 0), "#0B7A66", "converted pixels, Nov 2022"), (np.nanmean(cs25, 0), "#C8384F", "same pixels, Apr 2025")):
    ax[1].plot(np.where(ok_813, wl, np.nan), np.where(ok_813, sp, np.nan), color=c, lw=2.4, label=lab)
    ax[1].plot(np.where(ok_full & ~ok_813, wl, np.nan), np.where(ok_full & ~ok_813, sp, np.nan), color=c, lw=1.2, alpha=.35)
ax[1].plot(np.where(ok_813, wl, np.nan), np.where(ok_813, REF["bare / sand / sabkha"], np.nan), color="#B08A3E", lw=1.2, ls=":", label="bare / sand reference")
ax[1].axvline(1700, color="#1E6FD9", ls="--", lw=1); ax[1].set_xlabel("wavelength (nm)")
t = T2["converted_813"]
ax[1].set_title(f"Stand 5 with 813 bands only: vegetation -> sand/fill\n{t['share_2025_bare_or_built']*100:.0f} % of converted pixels now match bare/built (full spectrum: {T2['converted_full']['share_2025_bare_or_built']*100:.0f} %)", fontsize=11)
ax[1].legend(frameon=False, fontsize=9)
labels, groups = [], []
for key, ttl in (("T4_mangrove_vs_other_veg", "mangrove vs\nother vegetation"), ("T4_bare_vs_built", "bare/sand vs\nbuilt-up")):
    if OUT.get(key): labels.append(ttl); groups.append(OUT[key]["f1"])
names = ["S2-like (7 bands)", "813 range (EnMAP 400-1700 nm)", "EnMAP full (420-2450 nm)"]; cols = ["#9DB3D9", "#1E6FD9", "#06235A"]
for j, (nm, c) in enumerate(zip(names, cols)):
    vals = [g_[nm][0] for g_ in groups]; errs = [g_[nm][1] for g_ in groups]
    ax[2].bar(np.arange(len(groups)) + (j - 1) * .26, vals, .25, yerr=errs, color=c, label=nm.replace(" (EnMAP 400-1700 nm)", ""))
ax[2].set_xticks(range(len(groups))); ax[2].set_xticklabels(labels); ax[2].set_ylim(0, 1.15); ax[2].set_ylabel("F1 (spatial-block CV)"); ax[2].legend(frameon=False, fontsize=9, loc="upper left", ncol=3)
ax[2].set_title("Classification: what the 813 range keeps")
fig.text(.99, .01, "Simulation: EnMAP bands inside 400-1700 nm at 30 m, not real Satellite 813 data. Contains modified EnMAP data (c)DLR 2022, 2025", ha="right", fontsize=8, color="gray")
plt.tight_layout(); plt.savefig("analysis/36_sat813_sim.png", dpi=110); plt.close()
print("\nsaved analysis/36_sat813_sim.png, analysis/data/sat813_sim.json")
