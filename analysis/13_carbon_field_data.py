"""Module 4: carbon density from the open Abu Dhabi Blue Carbon field dataset (Schile et al. 2016, Dryad doi:10.15146/R3K59Z, CC0; field work 2013-14).

Per plot: ecosystem carbon = tree carbon (above + below ground, Mg C/ha) + soil ORGANIC carbon (Mg C/ha, summed over the sampled core sections).
IMPORTANT: soil cores have different depths (8-300 cm); we report soil to the sampled core depth and ALSO to a fixed 100 cm cap where possible.
Outputs: analysis/data/carbon_plots.csv, analysis/data/carbon_density_summary.json, analysis/13_carbon_summary.md
"""
import json, numpy as np, pandas as pd
f = "data/external/schile_2016_abu_dhabi_blue_carbon.xlsx"
rng = np.random.default_rng(5)
sc = pd.read_excel(f, "soil carbon data"); sc.columns = [c.strip() for c in sc.columns]
sc = sc.rename(columns={"OC (Mg/ha)": "oc_mgha", "depth (cm)": "depth", "plot": "Plot"})
sc["Plot"] = pd.to_numeric(sc.Plot, errors="coerce")
sc["d0"] = sc.depth.astype(str).str.extract(r"^([\d.]+)-")[0].astype(float); sc["d1"] = sc.depth.astype(str).str.extract(r"-([\d.]+)$")[0].astype(float)
CAP = 100.0                                                    # standardise soil carbon to the top 1 m (prorate the section that crosses 100 cm)
sc["frac"] = ((sc.d1.clip(upper=CAP) - sc.d0.clip(upper=CAP)) / (sc.d1 - sc.d0)).clip(lower=0)
sc["oc_cap"] = sc.oc_mgha * sc.frac
soil = sc.groupby(["Site", "Ecosystem", "Plot"]).agg(soil_full=("oc_mgha", "sum"), soil_oc=("oc_cap", "sum"), soil_depth_cm=("d1", "max"), n_sections=("d1", "size")).reset_index()
tr = pd.read_excel(f, "raw mature mangrove tree data"); tr["Location"] = tr.Location.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
tc, dead = "total tree Carbon   (Mg/ha)", "dead?"
tr[tc] = pd.to_numeric(tr[tc], errors="coerce"); alive = tr[tr[dead].isna()] if dead in tr else tr
tree = alive.groupby(["Location", "Plot"]).agg(tree_c=(tc, "sum"), n_trees=(tc, "size")).reset_index()
print("tree plots:", len(tree), "| sites:", tree.Location.nunique())
pi = pd.read_excel(f, "plot information")
# match site names between sheets
alias = {"Jubail Is.": "Jubail Island", "Jubail Is. East": "Jubail Island East", "Marawah Is.": "Marawah Island", "Al Zorah": "Ajman Al Zorah", "Bu Tinah Janoub": "Bu Tinah Jaoub",
         "Bu Tinah Janoub": "Bu Tinah Jaoub", "Umm Al Quwain": "Umm al Quwain", "Bu Tinah Shamal": "Bu Tinah Shamal", "Ras Al Kaimah": "Ras Al Kaimah", "Khalba East": "Kalba East", "Khalba North": "Kalba North", "Khalba South": "Kalba South", "Khalba West": "Kalba West"}
norm = lambda x: " ".join(str(x).split()).lower()
tree["key"] = tree.Location.map(norm); soil["key"] = soil.Site.map(norm)
mg = soil[soil.Ecosystem.astype(str).str.contains("mangrove", case=False) & ~soil.Ecosystem.astype(str).str.contains("plant|plated", case=False)].merge(tree[["key", "Plot", "tree_c", "n_trees"]], on=["key", "Plot"], how="inner")
mg["Site"] = mg.Site.map(lambda x: alias.get(" ".join(str(x).split()), " ".join(str(x).split())))
mg["total_c"] = mg.soil_oc + mg.tree_c
coords = pi.groupby(["Site", "Plot"]).agg(lat=("Latitude", "mean"), lon=("Longitude", "mean")).reset_index(); coords["Plot"] = pd.to_numeric(coords.Plot, errors="coerce"); coords["Site"] = coords.Site.map(lambda x: " ".join(str(x).split()))
mg = mg.merge(coords, on=["Site", "Plot"], how="left"); mg.to_csv("analysis/data/carbon_plots.csv", index=False)
print("natural-mangrove plots with soil+tree:", len(mg), "| sites:", mg.Site.nunique())
summ = mg.groupby("Site").agg(n=("Plot", "count"), tree=("tree_c", "mean"), soil=("soil_oc", "mean"), total=("total_c", "mean"), soil_depth=("soil_depth_cm", "median"), lat=("lat", "mean"), lon=("lon", "mean")).round(1).sort_values("total")
print(summ.to_string())
allm = mg.total_c.values; loc = mg[(mg.lon.between(54.35, 54.60)) & (mg.lat.between(24.40, 24.60))]; print(mg[["Site","Plot","lat","lon"]].drop_duplicates("Site").to_string(index=False))
print(f"\nALL UAE natural mangrove plots: n={len(mg)}, mean {allm.mean():.0f}, median {np.median(allm):.0f}, p10-p90 {np.percentile(allm, 10):.0f}-{np.percentile(allm, 90):.0f} Mg C/ha")
print(f"NEAR OUR REGION (sites {sorted(loc.Site.unique())}): n={len(loc)}, mean {loc.total_c.mean():.0f} (tree {loc.tree_c.mean():.0f} + soil {loc.soil_oc.mean():.0f}), p10-p90 {np.percentile(loc.total_c, 10):.0f}-{np.percentile(loc.total_c, 90):.0f}")
# planted mangroves near the region (Eastern Mangrove planted, by age)
pl = pd.read_excel(f, "planted mangrove data"); pl["tc"] = pd.to_numeric(pl["total plant carbon  (kgC/ha)"], errors="coerce") / 1000
plt_ = pl.groupby(["Location", "Age (yr)", "Plot"]).tc.sum().reset_index().groupby(["Location", "Age (yr)"]).tc.agg(["mean", "std", "count"]).round(1)
print("\nplanted mangrove TREE carbon (Mg C/ha, plot means):\n", plt_.to_string())
# bootstrap of the per-hectare density distribution for the product: local natural plots
sites = loc.Site.unique(); bm = []
for _ in range(20000):
    pick = rng.choice(sites, len(sites), replace=True); bm.append(np.mean(np.concatenate([loc[loc.Site == k].total_c.values for k in pick])))
np.save("analysis/data/carbon_boot_means.npy", np.array(bm)); ci = np.percentile(bm, [5, 50, 95]); print(f"cluster-bootstrap (by site, n_sites={len(sites)}) 90% CI of the LOCAL mean density: {ci[0]:.0f} - {ci[2]:.0f} Mg C/ha (median {ci[1]:.0f})")
print("soil to core depth (uncapped) local mean:", round(loc.soil_full.mean()), "| capped 100 cm:", round(loc.soil_oc.mean()))
out = dict(local_n=int(len(loc)), local_sites=sorted(loc.Site.unique()), local_mean=float(loc.total_c.mean()), local_p10=float(np.percentile(loc.total_c, 10)), local_p50=float(np.percentile(loc.total_c, 50)),
           local_p90=float(np.percentile(loc.total_c, 90)), uae_n=int(len(mg)), uae_mean=float(allm.mean()), uae_p10=float(np.percentile(allm, 10)), uae_p50=float(np.median(allm)), uae_p90=float(np.percentile(allm, 90)),
           ci90_lo=float(ci[0]), ci90_hi=float(ci[2]), n_sites=int(len(sites)), soil_uncapped_local=float(loc.soil_full.mean()), tree_local=float(loc.tree_c.mean()), soil_local=float(loc.soil_oc.mean()), soil_depth_median=float(loc.soil_depth_cm.median()))
json.dump(out, open("analysis/data/carbon_density_summary.json", "w"), indent=1)
with open("analysis/13_carbon_summary.md", "w", encoding="utf-8") as fh:
    NL = chr(10); fh.write("# Carbon density from field data (Schile et al. 2016)" + NL + NL + summ.to_markdown() + NL + NL + json.dumps(out, indent=1) + NL)
