# AOI feasibility spike — results (run 2026-09-19)

Script: `01_aoi_feasibility.py` (needs: pystac-client, planetary-computer, rasterio, scipy, numpy).
Data: ESA WorldCover 2021 (class 95 = mangrove, 10 m) and Sentinel-2 L2A (scene cloud < 20 %,
2017-01-01 to 2026-09-19), both via the Microsoft Planetary Computer STAC API.
"Pure" pixels = sensor-sized blocks that are 100 % mangrove (20 m ≈ Satellite 813, 30 m ≈ Tanager/EnMAP).
Boxes are approximate and were not hand-checked on a map.

| AOI | Mangrove (ha) | Patches | Patches ≥ 5 ha | Largest (ha) | Pure 20 m px | S2 distinct clear dates |
|---|---|---|---|---|---|---|
| **Abu Dhabi** (Eastern Mangroves / Jubail) | **5,262** | 784 | **118** | 220 | **120,089** | 1,078 |
| Saudi Red Sea (Jazan / Farasan) | 946 | 124 | 19 | 246 | 21,352 | 1,072 |
| Saudi Gulf — Tarut Bay | 465 | 69 | 13 | 192 | 10,471 | 1,026 |
| Saudi Gulf — Jubail | 132 | 25 | 5 | 90 | 2,955 | 1,057 |
| Bahrain (Tubli / Arad / Hawar) | **5** | 10 | 0 | 3.6 | **103** | 542 |

Caveats
- WorldCover is a model product; it likely **under-detects narrow fringing stands** (Bahrain figure probably too
  low). Re-check with Global Mangrove Watch, but even a 10x correction leaves Bahrain far below Abu Dhabi.
- Cloud filter is per scene, not over the mangrove pixels; usable observations per stand will be fewer.
- Median patch size is ~0.1 ha (single-pixel speckle) — filter patches < 0.5 ha before analysis.

---

# Spike 2 — Sentinel-2 red-edge time series, Abu Dhabi (run 2026-09-19)

Script: `02_s2_timeseries_spike.py`, plot: `02_s2_timeseries_spike.png`.
AOI: densest ~3 km cell of WorldCover mangrove (24.53–24.56 N, 54.45–54.48 E), 268 ha of interior pixels
(edge pixels dropped). Sentinel-2 L2A, tile 40RBN, 2020-01 → 2026-09, scene cloud < 40 %, SCL cloud mask.
Pipeline works end-to-end: 937 scenes read from the cloud (no downloads) in ~6 min; 827 had ≥ 50 % clean mangrove pixels.

| series | seasonal range | robust noise sd (after removing monthly median) | range / noise |
|---|---|---|---|
| NDVI median | 0.052 | 0.042 | 1.2 |
| NDVI p75 | 0.067 | 0.052 | 1.3 |
| NDRE median | 0.032 | 0.030 | 1.1 |
| NDRE p75 | 0.047 | 0.033 | 1.4 |

What it shows (honest reading)
1. A seasonal cycle is visible, but **single-date noise is as large as the seasonal signal** (range/noise ≈ 1.1–1.4).
   The scatter is dominated by a tail of low outliers (thin cloud/haze, tide-flooded pixels, glint), not by Gaussian noise.
2. **NDRE is NOT clearly better than NDVI here** (1.4 vs 1.3). The claim "red-edge flags decline earlier than NDVI" is
   currently unsupported — it must be tested, not assumed.
3. **Unexplained upward drift 2020 → 2026** (NDVI p75 ≈ 0.25 → 0.37): either real greening (growth/planting) or a
   processing artefact (baseline 04.00 offset, duplicate reprocessed scenes — 2022–23 show ~2x scenes per year).
   Must be resolved before any trend/carbon claim.
4. Fixes to try: dedupe by date; harmonise baselines (or use HLS `hls2-s30`); tide/water filter (e.g. MNDWI); cloud
   probability mask; rolling/robust aggregation; per-stand rather than whole-cell statistics.

---

# Spike 3 — cleaning the Sentinel-2 series (run 2026-09-19)

Script `03_s2_cleaning_spike.py` (per-scene stats cached in `data/s2_abudhabi_cell_stats.csv`, so no re-download needed).
Same 268 ha interior-mangrove cell. Scenes: 937 -> **779 distinct dates** (158 reprocessed duplicates removed).

1. **Offset artefact test:** on the 3 dates that exist in both processing baselines, new-minus-old NDVI = +0.003, NDRE = +0.002
   -> the +1000 offset handling looks right (weak evidence: only 3 pairs).
2. **Tide/wetness is the dominant noise source.** Correlation of index anomalies with the water proxy (MNDWI anomaly):
   NDVI r = -0.87, NDRE r = -0.92, NDMI r = +0.78. (An absolute "flooded pixel" threshold failed: mangrove is wet, so MNDWI>0
   almost everywhere -> use *relative* thresholds.)
3. **Cleaning works.** Robust single-date noise sd, raw -> keeping the driest 25 % of scenes (n=169):
   NDVI 0.044 -> 0.022, NDRE 0.033 -> 0.014, NDMI 0.055 -> 0.019. With a 45-day rolling median: NDVI 0.016, NDRE 0.010.
   Simple regression removal of the water proxy (keeps all scenes): NDVI 0.044 -> 0.031, NDRE 0.033 -> 0.022, NDMI 0.055 -> 0.030.
4. **Seasonal range / noise after cleaning (driest 25 %):** NDRE 0.057/0.014 = 4.1, NDVI 0.067/0.022 = 3.0, **NDMI (SWIR moisture) 0.094/0.019 = 4.9**.
   -> After tide control, red-edge beats NDVI (~35 % better SNR) and the SWIR moisture index is best. (Preliminary: one cell, one tile.)
5. **Drift persists after cleaning** (driest 50 %: NDVI 0.230 in 2020 -> 0.283 in 2026; NDRE 0.113 -> 0.142; MNDWI also falls 0.077 -> 0.003).
   Not explained by the offset (test above) -> consistent with real canopy greening/densification, NOT proven. Only 15 scenes/yr in 2020-21.
6. Caveat: a Sentinel-2 SWIR band (B11, ~1610 nm) is inside Satellite 813's range (to ~1700 nm).
