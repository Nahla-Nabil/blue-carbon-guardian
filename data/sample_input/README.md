# Example input (used by `notebooks/01_blue_carbon_guardian.ipynb`)

Real data clipped to our area of interest: 25 mangrove stands in the densest 13 x 10 km block of mangrove near Abu Dhabi (54.45-54.57 E, 24.47-24.56 N).
About 3.7 MB in total.

| File | Content |
|---|---|
| `stands.csv` | 25 stands (ESA WorldCover 2021 mangrove patches of at least 3 ha): id, area (ha), interior pixel count, centre lon/lat |
| `s2_stand_series.csv` | per stand and Sentinel-2 date: share of valid pixels and medians of NDVI, NDRE, NDMI, MNDWI over interior pixels; flooded fraction (MNDWI > 0) |
| `cells_stands_9_12_18.csv` | 64 cells of 200 m x 200 m in stands 9, 12 and 18: id, stand, interior mangrove pixels, position on the Sentinel-2 grid |
| `s2_cell_series_stands_9_12_18.csv` | the same statistics per cell and date, plus `n_valid` (valid pixels) |

## How it was produced (exact parameters)
- **Sentinel-2 L2A** (ESA / Copernicus), read from the Microsoft Planetary Computer STAC API (`https://planetarycomputer.microsoft.com/api/stac/v1`).
  - collection `sentinel-2-l2a`, MGRS tile **40RBN**, `eo:cloud_cover` < 40, **2020-01-01 to 2026-09-19**;
  - one scene per date (the newest processing baseline);
  - reflectance = (DN - 1000) / 10000 for processing baseline 04.00 or later, otherwise DN / 10000;
  - pixels with SCL classes 0, 1, 3, 8, 9, 10, 11 masked; a date is used if at least 50 % of the stand's or cell's pixels are valid.
- **Indices:** NDVI (B08, B04), NDRE (B8A, B05), NDMI (B8A, B11), MNDWI (B03, B11).
- **Stands and cells:**
  - WorldCover 2021 class 95, reprojected to the Sentinel-2 grid, with a 1-pixel interior erosion;
  - cells are 20 x 20 pixel blocks with at least 60 interior pixels.
- **Scripts:** `analysis/05_stand_series.py` (stands) and `analysis/25_substand_fetch.py` (cells) read the full archive (no credentials needed, about 20-60
  minutes). `scripts/make_sample_input.py` then extracts this sample.

Licence and attribution: "Contains modified Copernicus Sentinel data 2020-2026". ESA WorldCover 2021 v200, CC BY 4.0 (doi 10.5281/zenodo.7254221).
