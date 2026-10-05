# Out-of-sample test of the product alert (analysis/32, 33; 27 Sep 2026)

The combined rule ("stand average <= -1.5 sigma OR any 200 m cell <= -3.5 sigma") was calibrated on the 25 pilot stands (0.96 alert episodes per stand-year).
Here it is applied **with the same thresholds, no re-tuning**, to the scale-out stands that it never saw. Cell series come from `32_scaleout_cells_fetch.py`:
778-796 Sentinel-2 dates per block, 0 failed dates after one retry.

| Block | Stands | Cells | Stand-years | Alert episodes per stand-year (combined) | stand part | cell part |
|---|---|---|---|---|---|---|
| ADN, Abu Dhabi north | 36 | 288 | 168.8 | 0.85 | 0.79 | 0.40 |
| ADW, Abu Dhabi west | 21 | 196 | 98.6 | 0.63 | 0.62 | 0.31 |
| TRT, Tarut Bay, Saudi Arabia (other Sentinel-2 tile) | 8 | 106 | 37.6 | 0.96 | 0.91 | 0.37 |
| **All unseen stands** | **65** | **590** | **305.0** | **0.79** | | |
| Pilot (calibration) | 25 | 620 | 117 | 0.96 | | |

TRT has 8 stands here, not the 9 of analysis/23: one small stand has no cell with enough interior pixels.

**Reading: the false-alarm budget holds out of sample**, at 0.79 per stand-year against 0.96 calibrated, and also on the Saudi tile. Real changes stay in the series,
so 0.79 is an upper bound on the false-alarm rate.

## Candidates flagged by the cell condition layer, checked on sub-metre imagery (34b_vhr_view.py ADN / TRT ...)
| Stand | Flagged cells | What dated Esri Wayback captures (2021-2025) show | Verdict |
|---|---|---|---|
| ADN17 | 2 (2.9 ha) | the mangrove strip stays standing; the sea on its eastern side was filled (land reclamation) by Nov 2023 | no conversion; **inspection-worthy** (a cut-off tidal connection can kill mangroves over years) |
| ADN6 | 2 (3.5 ha) | no visible change | false positive |
| ADN23 | 1 (1.0 ha) | no visible change | false positive |
| TRT9 | 1 (1.3 ha) | no visible change (capture dates not checked for this Saudi site) | false positive |

No conversion was found in the unseen blocks, so this test measures false alarms, not detection. Their cell condition layer gave 3 false-positive stands
(5.8 ha) plus one inspection-worthy stand, out of 65.

Approved wording: "Applied unchanged to 65 stands it never saw (305 stand-years, including Saudi Arabia's Tarut Bay), the combined alert produced 0.79 episodes
per stand-year, against 0.96 where it was calibrated."
