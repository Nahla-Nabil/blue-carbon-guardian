# analysis/: pipeline index

Every number in the dashboard, reports and deck comes from these scripts. Run them from the repository root, for example
`python analysis/05_stand_series.py`. Each result has a short summary `.md` next to its script; start there.
Data are read from the cloud (Microsoft Planetary Computer STAC) without bulk downloads. EnMAP scenes are licensed and are not included.

## 1. Where and what (feasibility)
| Script | What it does | Key output / summary |
|---|---|---|
| 01_aoi_feasibility.py | Mangrove area and patch sizes per candidate AOI (ESA WorldCover 2021) | `01_aoi_feasibility_results.md`: Abu Dhabi 5,262 ha; Bahrain ~5 ha, so not viable at 10-30 m |
| 02_s2_timeseries_spike.py, 03_s2_cleaning_spike.py | First Sentinel-2 series on one cell; finds that tide/wetness is the dominant noise (r ~ -0.9) | figures `02_*.png`, `03_*.png` |

## 2. Stand-level monitor (core)
| Script | What it does | Key output / summary |
|---|---|---|
| 05_stand_series.py | 25 stands (WorldCover patches >= 3 ha), 778 Sentinel-2 dates 2020-2026, per-stand index medians | `data/s2_stands_stats.csv`, `data/stands.csv` |
| 07_tide_anomaly_backtest.py | Tide-aware robust model (trend + season + tide terms), rolling monthly refit, median-of-5 alert; first backtest | `07_summary.md` (noise -30 to -35 % with tide terms; **its detection metric was later corrected, see 30**) |
| 08_stand_status_carbon.py | Stand status, alert episodes, polygons, dashboard series | `data/stand_status.csv`, `stand_alert_episodes.csv`, `stands.geojson`, `dashboard_data.json` |
| 23_scaleout_monitor.py | **Condition rule** (last 12 months vs 2020-21, per stand) + same monitor on 66 unseen stands | `23_scaleout_summary.md` |
| 23b_condition_window_test.py | Shows that a 6-month "now" window biased all stands downward (season); justifies 12 months | `data/condition_window_test.csv` |

## 3. Extent and change (Module 1)
| Script | What it does | Key output / summary |
|---|---|---|
| 04_make_labeling_points.py | 300 stratified, blind reference points (1 km spatial blocks) | `labeling/` (labels: AI-assisted photo-interpretation, `labels_Claude_AI.csv`) |
| 10_extent_composites.py, 11_extent_classify.py | Low-tide composites 2021/2025; random-forest extent (negative result: fails across epochs) | `11_extent_summary.md` |
| 12_change_detection.py | Ratio-index change indicator 2021 -> 2025 (independent of the time series) | `data/change_by_stand.csv`, `12_change.png` |

## 4. Carbon (Module 4)
| Script | What it does | Key output / summary |
|---|---|---|
| 13_carbon_field_data.py | Field carbon density from Schile et al. 2016 (Dryad, CC0): 108 t C/ha (90 % CI 79-138) | `13_carbon_summary.md` |
| 14_update_carbon_in_status.py | Stock = area x field density, per stand, with range | `data/stand_status.csv` |
| 15_eo_vs_field_carbon.py | Do Sentinel-2 indices predict field carbon? Too weak (rho <= 0.38), so no biomass model | `data/eo_vs_field.csv` |

## 5. Hyperspectral check (Module 3, EnMAP)
| Script | What it does | Key output / summary |
|---|---|---|
| 17_enmap_reader.py | Reads EnMAP L2A (224 bands), drops water-vapour bands, per-stand spectra | `data/enmap_stand_spectra.csv` |
| 18_enmap_analysis.py, 19_enmap_scrub_test.py | Cross-sensor check (r = 0.84-0.99), stand-5 conversion 62 ha, separability tests | `18_enmap_summary.md` |

## 6. Real events and timing
| Script | What it does | Key output / summary |
|---|---|---|
| 20_onset_series_fetch.py, 21_onset_analysis.py | Dates the start of the stand 5 and 9 conversions (loss pixels minus control pixels) | `21_onset_summary.md` |
| 28_stand_event_check.py | Same-season imagery and onset check for any stand (used for 12, 18, 6) | `figures/stand*_key_years.png`, `data/stand*_event_check.json` |

## 7. Scale-out and 200 m cells
| Script | What it does | Key output / summary |
|---|---|---|
| 22_scaleout_fetch.py, 24_scaleout_visual_check.py | 66 unseen stands (2 Abu Dhabi blocks, Tarut Bay) | `23_scaleout_summary.md` |
| 25_substand_fetch.py, 26_substand_monitor.py, 27_substand_visual_check.py | 620 cells of 200 m in the pilot stands; cell condition; agreement with the change indicator | `26_substand_summary.md` |
| 29_cell_trigger.py | Calibrates stand / cell / combined alert rules to the same false-alarm budget; partial-loss simulation with a null | `29_cell_trigger.md` |
| 30_backtest_null.py | Re-tests the stand-level backtest with a null and onset-based detection (**corrects 07**) | `30_backtest_null.md` |
| 31_union_alerts.py | Product alert = stand <= -1.5 sigma OR any cell <= -3.5 sigma; episodes for the dashboard and reports | `data/union_*.csv/json` |
| 34_vhr_capture_dates.py, 34b_vhr_view.py | Dated sub-metre captures (Esri World Imagery Wayback) of the four converted sites; view-only imagery written outside the project | `34_vhr_summary.md`, `data/vhr_captures.json` |
| 32_scaleout_cells_fetch.py, 33_scaleout_union.py | **Out-of-sample** test of the product alert on the 66 unseen stands, thresholds fixed | `33_scaleout_union_summary.md`: 0.79 episodes per stand-year out of sample vs 0.96 calibrated |

## 8. Product
| Script | What it does | Output |
|---|---|---|
| 09_build_dashboard.py (+ `dashboard_template.html`) | Self-contained dashboard (no server) | `../dashboard/index.html` |
| 16_site_reports.py | Templated per-stand site report (every sentence from a number) | `../reports/stand_XX_report.html` |

## Rebuild order after new satellite data
`05 -> 08 -> 13 -> 14 -> 23 -> 25 -> 26 -> 29 -> 31 -> 09 -> 16`. The extent and change steps (10-12) and the EnMAP steps (17-19) are only needed when their inputs change.
08 writes a fresh `stand_status.csv`; 14 adds carbon, and 23 adds the condition columns (its verification step is skipped on a fresh table).
