"""Module 3, step 3: can EnMAP spectra tell true mangrove from the brown 'hummocky scrub' (halophytes?) on tidal flats that we could not resolve by eye?
Reference = our AI-assisted labels (blind) that fall inside the Nov-2022 EnMAP scene; features = 3x3-pixel medians of hyperspectral indices. Small n, mixed 30 m pixels: exploratory only.
Attribution: Contains modified EnMAP data (c)DLR 2022."""
import importlib.util, numpy as np, pandas as pd
from rasterio.warp import transform as wt
from rasterio.transform import rowcol
from scipy.stats import mannwhitneyu
spec = importlib.util.spec_from_file_location("er", "analysis/17_enmap_reader.py"); er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
sc = er.load_scene("e20221101"); R = er.reflectance(sc); wl = sc["wl"]; ind = er.indices(R, wl)
ind["CAI2100"] = 0.5 * (er.band_at(R, wl, 2000) + er.band_at(R, wl, 2200)) - er.band_at(R, wl, 2100)          # 2100 nm absorption depth (dry matter / minerals)
lab = pd.read_csv("labeling/returned/labels_Claude_AI.csv")
xs, ys = wt("EPSG:4326", sc["crs"].to_string(), lab.lon.tolist(), lab.lat.tolist()); r, c = rowcol(sc["transform"], xs, ys); lab["r"], lab["c"] = r, c
lab = lab[lab.r.between(2, sc["H"] - 3) & lab.c.between(2, sc["W"] - 3)].copy()
notes = lab.notes.fillna("").str.lower()
lab["group"] = np.where((lab.label == "mangrove_healthy") & (lab.confidence_1to3 >= 2), "mangrove (conf>=2)",
               np.where((lab.label == "not_mangrove") & notes.str.contains("hummock|scrub|halophyte|marsh"), "brown scrub / marsh", "other"))
for k in ind:
    lab[k] = [np.nanmedian(ind[k][r0 - 1:r0 + 2, c0 - 1:c0 + 2]) for r0, c0 in zip(lab.r, lab.c)]
g = lab[lab.group != "other"].dropna(subset=["NDVI_s2"])
print("points in scene by group:", g.group.value_counts().to_dict())
a = g[g.group == "mangrove (conf>=2)"]; b = g[g.group == "brown scrub / marsh"]
if len(a) >= 5 and len(b) >= 4:
    print(f"\n{'feature':10s} {'mangrove median':>16s} {'scrub median':>13s} {'AUC':>6s} {'p':>7s}")
    for k in ("NDVI_s2", "NDRE_s2", "NDMI_s2", "MNDWI_s2", "REP", "WBI", "NDWI1240", "NDII1650", "CAI2100"):
        u, p = mannwhitneyu(a[k].dropna(), b[k].dropna()); auc = u / (len(a[k].dropna()) * len(b[k].dropna()))
        print(f"{k:10s} {a[k].median():16.3f} {b[k].median():13.3f} {max(auc, 1 - auc):6.2f} {p:7.3f}")
else:
    print("too few points for a comparison")
