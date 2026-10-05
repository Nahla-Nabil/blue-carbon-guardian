# Alert rule: stand average, 200 m cells, or both? (analysis/29, analysis/30)

## 1. A correction to our own earlier backtest (analysis/30)
analysis/07 counted a trial as detected if the alert was on at any date after the injected loss began. It also had no no-loss scenario.
- An alert episode already running at the start date counts as a detection under that metric, and episodes last weeks to months.
- A real change in the same stand also counts.

Re-tested on the same stand series with three changes:
- detection = a NEW alert episode (no alert in the previous 30 days) starting within 180 days;
- a no-loss (null) scenario;
- the stands with changes seen on imagery (5, 6, 9, 12, 18) excluded; 240 trials per scenario.

| Whole-stand cover loss | Old metric: NDMI 60 d / 180 d | **New: NDMI** 60 d / 180 d | New: composite (the dashboard alert) | Chance (null): NDMI / composite |
|---|---|---|---|---|
| 5 % | 40 / 66 | 26 / 57 | 23 / 51 | 14 / 36 and 15 / 40 |
| 10 % | 50 / 85 | **35 / 73** | 30 / 65 | 14 / 36 and 15 / 40 |
| 20 % | 78 / 97 | **63 / 83** | 51 / 80 | 14 / 36 and 15 / 40 |

Under the old metric, even with NO loss, 28-35 % of trials counted as "detected within 60 days". **The claim "10 % loss detected within 2 months in about 58 %
of cases and within 6 months in about 90 %" is withdrawn.** Detection is real, well above chance, but lower.

## 2. Stand average vs cells vs both (analysis/29)
Every detector is calibrated on the real 2022-2026 series of the 25 stands to at most 1 alert episode per stand-year. The real events stay in the calibration,
which is conservative.
- STAND: stand monitor on the pixel-weighted mean of the cell medians, 1.2 sigma.
- CELL-k: k adjacent cells alerting on the same date (k = 1: 3.0 sigma, k = 2: 2.3, k = 3: 1.9).
- **UNION: the stand at 1.5 sigma OR any single cell at 3.5 sigma.** Both parts got the same individual budget (0.75 per stand-year), raised until the union
  reached 1 per stand-year (realised 0.96). This used only the no-loss side of the data, never the detection results.

Trials: the 20 stands without known changes, 8 random start dates each (n = 160 per scenario, so about +/- 7 percentage points).
Detection = a new episode within 60 / 180 days.

| Scenario | STAND | CELL-1 | **UNION** | Chance (null) STAND / CELL-1 / UNION |
|---|---|---|---|---|
| patch of 10 % of the stand loses 50 % of its cover | 25 / 65 | 77 / 84 | **73 / 84** | 11 / 41, 11 / 29, 13 / 36 |
| patch of 10 % loses 100 % | 45 / 79 | 84 / 85 | **83 / 83** | same |
| patch of 25 % loses 50 % | 44 / 79 | 81 / 84 | **78 / 84** | same |
| whole stand loses 10 % | 33 / 73 | 16 / 48 | **25 / 63** | same |
| whole stand loses 20 % | 58 / 83 | 40 / 81 | **53 / 83** | same |

Adjacency rules (CELL-2, CELL-3) did not beat a single cell at a higher threshold.

Real events (first alert from the dated change start, within a year):

| Stand | Change start | STAND | UNION |
|---|---|---|---|
| 5 | 14 Feb 2023 (dated, analysis/21) | +1 d* | +1 d* |
| 9 | 14 Jun 2023 (dated) | +38 d | +1 d* |
| 12 | after 4 Aug 2022 (last intact image) | +187 d | +107 d |
| 18 | 3 Feb 2025 (dated, analysis/28) | +1 d* | +1 d* |

\* = an episode was already running at the start date, so this is not a clean delay. Stands 5, 9 and 18 all had alerts in the 120 days before the dated start,
which are unexplained: chance (about a 28 % chance per 4-month window at this budget) or site preparation.
Note: the STAND proxy here alerts at stand 18, but the product's stand alert (on the stand median, analysis/08) never did.

## Decision
**The recommended product alert is UNION: "the stand average at 1.5 sigma OR any 200 m cell at 3.5 sigma", calibrated to about 1 false-alarm episode per stand-year.**
- It keeps nearly all of the cell advantage on partial losses, which is how all four real conversions happened.
- It gives up a little on uniform whole-stand loss.
- **Wired in on 2026-09-27** (analysis/31_union_alerts.py -> dashboard + site reports): 112 episodes over 117 stand-years (0.96), by source: both 51, cells only 31, stand only 30; 0 active on 17 Sep 2026.
- A stand with no known change is in alert about 18 % of the time (range 3-35 %). In 3 of 4 events the alert was already on at the dated start (stand 5 from 25 Oct 2022, mostly from cells that later converted; stand 9 from 7 Dec 2022, from the south-east cells that later converted; stand 18 from 29 Oct 2024, spread across the stand). By chance alone that would happen about 2 % of the time (binomial, p = 0.18). This is suggestive (site preparation, or change starting before we can date it) but NOT claimed as advance warning: four events, no site records.

## Limits
- Calibration and trials use the same 25 stands. **Out-of-sample check done afterwards (analysis/33): 0.79 episodes per stand-year on 65 unseen stands.**
- n = 160 per scenario.
- Simulated loss is linear mixing of cover with bare values, not leaf stress.
- Chance rates vary between runs (about 9-19 % within 60 d), so always quote the chance rate next to a detection rate.

Approved wording: "Calibrated to about one false alarm per stand per year, our combined stand-and-cell alert catches a partial loss (a tenth of a stand losing half its canopy)
within two months in about 73 % of simulated cases, against about 13 % by chance. A uniform 10 % loss over a whole stand is harder: about 63 % within six months
(36 % by chance)."
NOT allowed: "58 % / 90 %" (withdrawn), any detection rate without its chance rate, "early warning".
