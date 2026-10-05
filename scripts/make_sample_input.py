"""Build data/sample_input/ (the small example input used by notebooks/01_blue_carbon_guardian.ipynb) from the full pipeline outputs.

The full series are produced by analysis/05_stand_series.py (stands) and analysis/25_substand_fetch.py (200 m cells). Both read Sentinel-2 L2A from the
Microsoft Planetary Computer STAC API (collection sentinel-2-l2a, MGRS tile 40RBN, eo:cloud_cover < 40, 2020-01-01 to 2026-09-19, one scene per date with
the newest processing baseline; SCL classes 0, 1, 3, 8, 9, 10, 11 masked; baseline >= 04.00 offset of -1000 DN applied). No credentials are needed.
This script only keeps the columns the notebook uses and the cells of stands 9, 12 and 18 (the stands where the cell layer matters).
Run from the repository root: python scripts/make_sample_input.py
"""
import os
import pandas as pd

OUT = "data/sample_input"; os.makedirs(OUT, exist_ok=True)
COLS = ["date", "valid_frac", "ndvi_p50", "ndre_p50", "ndmi_p50", "mndwi_p50", "flooded_frac"]

s = pd.read_csv("analysis/data/s2_stands_stats.csv")
s = s[["stand"] + COLS].dropna(subset=["ndvi_p50"]).round(4)
s.to_csv(f"{OUT}/s2_stand_series.csv", index=False)

st = pd.read_csv("analysis/data/stands.csv")[["stand", "area_ha", "interior_px", "lon", "lat"]].round(5)
st.to_csv(f"{OUT}/stands.csv", index=False)

cells = pd.read_csv("analysis/data/substand/cells.csv")
keep = cells[cells.stand.isin([9, 12, 18])][["cell", "stand", "n_px", "row", "col"]]
keep.to_csv(f"{OUT}/cells_stands_9_12_18.csv", index=False)
c = pd.read_csv("analysis/data/substand/cell_stats.csv", usecols=["date", "cell", "valid_frac", "n_valid", "ndvi_p50", "ndre_p50", "ndmi_p50", "mndwi_p50", "flooded_frac"])
c = c[c.cell.isin(keep.cell)].dropna(subset=["ndvi_p50"]).round(4)
c.to_csv(f"{OUT}/s2_cell_series_stands_9_12_18.csv", index=False)

for f in sorted(os.listdir(OUT)):
    print(f, round(os.path.getsize(f"{OUT}/{f}") / 1e6, 2), "MB")
