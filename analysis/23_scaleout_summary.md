# Scale-out: the unchanged monitor on 66 stands it never saw

Scripts: `22_scaleout_fetch.py` (Sentinel-2 series, 0 failed dates after retry), `23_scaleout_monitor.py` (monitor + condition), `24_scaleout_visual_check.py`
(figure `figures/scaleout_declines_2020_2026.png`). Tables: `data/scaleout/scaleout_status.csv`, `scaleout_episodes.csv`, `scaleout_summary.json`.

Thresholds were calibrated on the 25 pilot stands and NOT re-tuned. Step 0 re-implements the pilot logic and reproduces the saved pilot table exactly
(condition 25/25, alert-episode counts 25/25).

| Block | Where | Stands | Area | Stand-years | Alert episodes per stand-year | Active alerts | Condition |
|---|---|---|---|---|---|---|---|
| Pilot (calibration) | Abu Dhabi | 25 | 2,281 ha | 117 | 0.95 | 0 | 24 stable, 1 severe decline (stand 5) |
| ADN | Abu Dhabi, north of pilot | 36 | 956 ha | 169 | 1.04 | 0 | 35 stable, 1 decline |
| ADW | Abu Dhabi, west of pilot | 21 | 646 ha | 99 | 0.72 | 0 | 21 stable |
| TRT | Saudi Arabia, Tarut Bay (other S2 tile) | 9 | 362 ha | 42 | 0.95 | 0 | 8 stable, 1 decline |

Reading
- **The false-alarm budget transfers.** On 66 unseen stands (1,964 ha), including another country and another Sentinel-2 tile, the alert rate is
  0.72-1.04 episodes per stand-year against the 0.95 it was calibrated to. No re-tuning was needed.
- Coverage in Abu Dhabi rises from 2,281 to 3,883 ha (about 74 % of the 5,262 ha of WorldCover mangrove in our Abu Dhabi box).
  Field-based carbon for the 57 new Abu Dhabi stands: about 174 kt C (126-222, uncertainty of the mean density only). Not computed for Tarut Bay (no local field data).
- **Two 'decline' flags, neither visually confirmed.** ADN27 (8 ha) and TRT9 (3 ha): tide-corrected NDVI about -26 %, -3.2 sigma, just past the rule
  (-15 % and -3 sigma). Same-season true-colour images 2020 vs 2026 show no conversion. **Treat as "inspect" flags, not events.** Contrast: stands 5 and 9
  fell to or near bare values and the conversion is visible.

## Correction made during this step (2026-09-27): seasonal bias in the condition layer
- The 'now' value was the median of the last **180 days**, the baseline the median of 2020-21 (two full years). Summer is lower than winter (baseline
  summer-minus-winter: NDVI -0.07, NDMI -0.08), so a 6-month window ending in September biased every stand down: median change over all 91 stands
  NDVI -7.5 % (180 d) vs -0.5 % (365 d), NDMI -15.3 % vs -7.0 %. **Now: last 365 days (a full cycle).** Test: `23b_condition_window_test.py`, `data/condition_window_test.csv`.
- A second fix: the rule compared values rounded to one decimal (-2.96 sigma counted as -3.0). It now uses unrounded values.
- Effect: new-stand 'decline' flags 4 -> 2 (ADN6 and ADN23 drop out). Pilot classes unchanged (24 stable, stand 5 severe decline); pilot values updated
  (stand 5 NDVI -111 %, stand 9 -14 % -> -10 %); old table kept as `data/stand_status_before_365d.csv`. Dashboard and site reports rebuilt.

Approved wording: "Applied unchanged to 66 new stands (1,964 ha) in Abu Dhabi and Saudi Arabia's Tarut Bay, the monitor kept its false-alarm rate
(0.7-1.0 alert episodes per stand-year vs 0.95 calibrated). It raised two moderate 'decline' flags that imagery does not confirm; they are inspection
candidates, not detected losses."
NOT allowed: "detected decline in Saudi Arabia", "validated across the Gulf" (one Saudi block, 9 stands, no confirmed event there).
