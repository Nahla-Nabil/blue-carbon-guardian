# Sub-stand monitoring: the same monitor per 200 m cell

Scripts: `25_substand_fetch.py` (778 Sentinel-2 dates, 620 cells, 0 errors), `26_substand_monitor.py` (monitor + condition + checks),
`27_substand_visual_check.py`. Figures: `26_substand.png`, `figures/substand_unsupported_cells.png`. Tables: `data/substand/cell_status.csv`,
`cell_episodes.csv`, `substand_summary.json`.

Setup: the 25 pilot stands cut into 200 m x 200 m cells (4 ha). Each cell keeps its interior WorldCover-mangrove pixels and is used if it has at least 0.6 ha of them.
Result: 620 cells covering 1,539 ha of interior mangrove pixels. The monitor and the condition rule are the stand-level ones, unchanged: last 12 months vs 2020-21,
tide-corrected, NDVI and NDMI.

## What it adds
1. **The partial loss in stand 9 becomes visible.** The stand average reads "stable". At the cell level, 8 of 28 cells (21.8 of 67 ha) are "severe decline",
   and all 5 cells that the independent epoch-difference indicator calls changed are among them. The north-west part stays stable, as the imagery shows.
2. **Earlier alert on stand 9.** The first cell alert came on 27 Jul 2023, about 6 weeks after the dated start of the change (14 Jun 2023).
   The stand-level alert came on 23 Sep 2023, so the cell level is about 2 months earlier. It is still detection during the change, not advance warning.
   Stand 5: a cell alert came on 22 Nov 2022, before the dated start (Feb 2023), like the stand-level alert of Dec 2022. This is unexplained and NOT claimed as warning.
3. **Where inside the stand.** Stand 5: 26 of 45 cells flagged (71 ha of 120 ha of mangrove pixels). Whole cells are counted, so this is coarser than
   the pixel estimates. The quoted stand-5 loss stays 26-62 ha.

## Agreement with an independent method (epoch-difference indicator, analysis/12)
Both use Sentinel-2, but they are different methods: a time-series monitor vs two low-tide composites. Neither is ground truth.
- Cells the indicator marks as changed (at least 50 % of pixels): **11 of 15 flagged (73 %)**.
- Cells it marks as unchanged (under 5 %): **11 of 554 flagged (2 %)**. Looking at those 11:
  - 8 are in stand 5 and drop to NDVI of about 0. Two were inspected on imagery and are clearly converted (sand, built land). The indicator misses them
    because it needs a drop of at least 0.15, and sparse cells cannot drop that far. EnMAP had already shown that the indicator is conservative (62 vs 26 ha).
  - Cells 13 (stand 1) and 452 (stand 12): the 2026 imagery shows a new bright feature (a linear strip across the channel, a sand spread). Probably real, small changes.
  - Cell 296 (stand 6): unclear.
- The 4 changed-but-not-flagged cells were already nearly bare in 2020-21 (NDVI 0.10-0.13): sparse edges with little to lose, so their drop sits inside the noise.

## Cost and design consequence
- Alert rate per cell: 0.97 episodes per cell-year, the same as per stand. Stands have about 25 cells each, though, so raw cell alerts would multiply the alarms
  a user sees. **Product design: the stand-level alert stays the trigger (calibrated to about 1 per stand-year); the cell condition map shows WHERE inside the stand.**
  A calibrated cell-level trigger (for example, several adjacent cells alerting together) is future work.
- Flagged area in total: 51 cells, 126.5 ha. 106 ha of that is in the three conversions seen on imagery (stands 5, 9 and 12, see below).

NOTE 2026-09-27: alert TIMING statements in this file used uncalibrated per-cell alerts (1.3 sigma); they are superseded by the calibrated combined rule of analysis/29 and 31. Condition-map statements stay valid.
Approved wording: "Split into 200 m cells, the same monitor exposes partial losses that stand averages hide. In stand 9, 8 of 28 cells show severe decline while the
stand average reads stable. Against an independent change method, it flags 11 of 15 changed
cells and 11 of 554 unchanged cells; most of those 11 are real conversions that the stricter method misses."
NOT allowed: cell-level accuracy numbers presented as ground truth; "early warning"; cell-flagged area presented as a loss estimate.

## Third conversion found by the cells: stand 12 (checked 2026-09-27, `28_stand_event_check.py 12 2022,2023,2026`)
Figures: `figures/stand12_key_years.png`, `figures/stand12_yearly.png`, `figures/stand12_event_check.png`; numbers: `data/stand12_event_check.json`.
- The stand average reads "stable" (NDVI -24 %, NDMI -24 %, not both past -15 % AND -3 sigma), but **6 of 20 cells (13.2 ha of mangrove pixels) are "severe decline"** along the southern edge.
- Same-season imagery: intact vegetated edge on 4 Aug 2022. By 13 Sep 2023 a new canal crosses the stand and reclamation lagoons press against its edge; the dark
  vegetation strip at the southern edge is gone. By 29 Jul 2026 a canal-style development with rows of buildings occupies the area.
  => a third coastal-development conversion, **visible on 10 m imagery** (same standard as stands 5 and 9). A VHR check is recommended.
- Timing: strong cell alerts from Oct-Dec 2022 (z down to -14.7), i.e. after the last intact image. The stand-level alert came on 7 Mar 2023, about 3-5 months later.
  The change has two phases: a moisture decline and cell alerts from late 2022, then a sharp NDVI drop in mid-2025 (fitted start 3 Jul 2025, 90 % CI Jun-Aug 2025).
  A single ramp does not fit two phases, so no single start date is quoted.
- The epoch-difference indicator supports it only partly (3-41 % of each cell's pixels), which is why this stand was not among the flagged stands before.
- Flagged area counts whole cells, so 13.2 ha overstates the converted strip. No loss area is quoted.

Approved wording: "The 200 m cell layer found a third conversion that the stand average hides: at stand 12 a canal and an adjacent coastal development took the southern
edge (intact in Aug 2022, converted by Sep 2023, built up by 2026). Strong cell alerts came from Oct-Dec 2022, 3-5 months before the stand-level alert."

## Remaining flagged stands checked (2026-09-27; `28_stand_event_check.py 18|6 2020,2023,2026`)
- **Stand 18: fourth conversion.** 3 of 16 cells (5.1 ha) flagged; stand average "stable". Vegetated in Sep 2020. In Sep 2023 the circular reclamation lagoons
  (apparently the same development as at stand 12) reach the stand edge while the cells are still vegetated. By Jul 2026 the flagged part is sand or construction.
  Change start Feb-Apr 2025 (NDMI 3 Feb, NDVI 4 Apr). First cell alert 16 Jul 2025 (uncalibrated 1.3 sigma cells). The old stand-level alert on the stand MEDIAN (analysis/08) never alerted here; the calibrated product rule (analysis/31), whose stand part uses the pixel-weighted MEAN of cell medians, did (from 29 Oct 2024). A median ignores a change in a minority of pixels, a mean does not. The epoch-difference indicator had
  flagged 5.3 ha (13 %) here before.
- **Stand 6: fifth conversion (updated 27 Sep after the sub-metre check, `34_vhr_summary.md`): a canal and lagoon development; by Jan 2025 part of the flagged area is open water.** Earlier note: 5 of 47 cells (10.5 ha). New channels and fill appear around the flagged cells from 2022 (step in moisture, start
  Jun-Aug 2022). First cell alert 5 Jul 2022; stand-level alert only on 3 Dec 2024. This could be development or restoration earthworks (tidal channels):
  it is NOT counted as a loss event.
- Not yet checked (1 cell each): stands 1, 10, 25.

Tally of cell-flagged stands: conversions seen on 10 m imagery in stands 5, 9, 12 and 18 (**12 and 18 found only by the cell layer**); stand 6 has visible
earthworks of unknown purpose; 3 single-cell flags are unchecked.
Approved wording: "Four coastal-development conversions inside our 25 stands are visible on imagery (stands 5, 9, 12, 18). Two of them (12, 18) are hidden in stand
averages and were found only by the 200 m cell layer." (The earlier sentence about stand 18's stand-level alert is withdrawn, see above.)
