# Onset dating of the two real events (stands 5 and 9)

Scripts: `20_onset_series_fetch.py` (778 Sentinel-2 dates, 2020-2026, 0 errors), `21_onset_analysis.py`. Figure: `21_onset.png`. Table: `data/onset_results.csv`.

Method: median NDVI / NDMI inside the pixels flagged as changed (loss: stand 5 = 26.1 ha, stand 9 = 13.5 ha) minus the same statistic in unchanged mangrove
pixels of the same stand (control, >= 50 m from any flagged pixel). Tide, season and sensor effects shared by both sets cancel. A constant - ramp - constant
model is fitted; 90 % interval for the start from a 300-draw residual bootstrap (approximate).

| Stand | Index | Change starts (90 % interval) | Ramp ends | Stand-level alert in the window | Delay after start |
|---|---|---|---|---|---|
| 5 | NDVI | 2023-04-15 (2023-02-14 .. 2023-05-15) | 2023-06-14 | 2023-03-17 | -29 d |
| 5 | NDMI | 2023-02-14 (2023-01-15 .. 2023-03-16) | 2023-06-14 | 2022-12-07 (weak, 15 d) / 2023-03-17 | -69 d / +31 d |
| 9 | NDVI | 2023-06-14 (2023-05-15 .. 2023-07-14) | 2023-10-12 | 2023-09-23 | +101 d |
| 9 | NDMI | 2023-06-14 (2023-05-15 .. 2023-07-14) | 2023-11-11 | 2023-09-23 | +101 d |

Reading
- Both events are abrupt steps in 2023 (stand 5 over about 2-4 months, stand 9 over about 4-5 months), not slow decline.
- Stand 5: the stand-level alert of 17 Mar 2023 falls inside the interval for the start of change: **detected as the conversion began, not before it.**
- Stand 9: the alert came about **3 months after the start**, while the change was still in progress (ramp ends Oct-Nov 2023).
- Other alerts of these stands before the start (stand 5: 13 May 2022, 7 Dec 2022; stand 9: 2 Jun 2022, 22 Jul 2022) precede the fitted change by 3-13 months.
  We cannot tell whether they are false alarms (the design allows about one episode per stand-year) or real precursors (site preparation); unproven either way.
- Correction to earlier text: the May 2022 alert is NOT "inside the conversion window"; the conversion started in 2023.

Approved wording: "In both confirmed conversion events the alert fired during the conversion: within about one month of its start in stand 5, and about three months after its
start in stand 9 (before it finished). This is detection during change, not advance warning." Do NOT claim a lead time / early warning before the change.

Limits: loss pixels were selected from 2021 vs 2025 imagery, so this dates a known change; two events only; interval from an approximate bootstrap; stand-level averages dilute
partial losses (which is why stand 9 is late).
