"""Replace the placeholder carbon columns in stand_status.csv with field-based values (analysis/13): stock = stand area x density, where the density draws are the
site-clustered bootstrap means of local natural-mangrove plots (Eastern Mangrove, Jubail Island, Jubail Island East, Salaam; n=24 plots, 4 sites; soil capped at 100 cm).
The range expresses uncertainty of the MEAN density (4 sites); it does not include within-stand variability or trees/soil below 1 m."""
import numpy as np, pandas as pd
CO2E = 44 / 12; rng = np.random.default_rng(11)
st = pd.read_csv("analysis/data/stand_status.csv"); boot = np.load("analysis/data/carbon_boot_means.npy")
d = rng.choice(boot, 20000)
for i, r in st.iterrows():
    lo, md, hi = np.percentile(r.area_ha * d, [5, 50, 95])
    st.loc[i, ["stock_tC_p10", "stock_tC_p50", "stock_tC_p90", "stock_tCO2e_p50"]] = [round(lo), round(md), round(hi), round(md * CO2E)]
st["carbon_source"] = "Schile et al. 2016 field plots (Dryad), 24 plots / 4 sites near Jubail-Eastern Mangroves; soil top 1 m"
st.to_csv("analysis/data/stand_status.csv", index=False)
print("total stock p5/p50/p95 (kt C):", *(round(st[c].sum() / 1000) for c in ("stock_tC_p10", "stock_tC_p50", "stock_tC_p90")), "| tCO2e median (kt):", round(st.stock_tCO2e_p50.sum() / 1000))
print("stand 5 stock kt C:", *(round(float(st.loc[st.stand == 5, c].iloc[0]) / 1000, 1) for c in ("stock_tC_p10", "stock_tC_p50", "stock_tC_p90")))
