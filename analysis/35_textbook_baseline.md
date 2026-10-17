# The textbook approach against our monitor (analysis/35, 17 Oct 2026)

**Question.** The usual educational recipe for mangrove health is a vegetation index (NDVI) followed by anomaly detection. How does it compare
with our monitor on the same Gulf stands, using exactly the same alert machinery?

**Set-up.** 25 pilot stands and their 620 cells (200 m), Sentinel-2 2020–2026. Same alert machinery in every configuration: monthly rolling refit on
[t − 36 months, t − 3 months], robust z, median of the last 5, product rule "stand ≤ −1.5σ OR any cell ≤ −3.5σ". Only the model inside changes.
False alarms are counted on the 20 stands with no known conversion (93.9 stand-years, 2022–2026). Script: `analysis/35_textbook_baseline.py`.

| Configuration | Indices | Tide terms | False-alarm episodes per stand-year | Conversions with an alert start inside the sub-metre window |
|---|---|---|---|---|
| A · textbook | NDVI | no | **1.61** | 5 of 5 |
| B | NDVI | yes | 1.04 | 5 of 5 |
| C | NDVI + red edge + SWIR moisture | no | 1.36 | 5 of 5 |
| D · ours (product) | NDVI + red edge + SWIR moisture | yes | **0.96** | 5 of 5 |

## Reading
- **Same rule, same stands: the textbook approach raises 1.61 false-alarm episodes per stand-year, ours 0.96, that is 40 % fewer** (about 68 % more
  alarms for the textbook approach). For the 25 pilot stands this is about 40 against 24 alarms a year with no change behind them: roughly 16 fewer
  unnecessary inspections a year.
- **The tide model is the main ingredient**: adding tide terms to NDVI alone already brings 1.61 down to 1.04; the extra indices add a little more (0.96).
- All four configurations put an alert start inside the capture window of all five real conversions. The windows are wide (about 11 months), so this
  shows that the textbook approach also sees large conversions; it does not separate the configurations. The difference is the false-alarm cost.
- Share of time a normal stand spends in alert is similar (14–16 %): the textbook approach produces more, shorter, separate episodes, and each
  episode is a separate inspection decision.

## Limits
- Thresholds were calibrated for configuration D; at a stricter threshold the textbook approach would raise fewer alarms but also catch less. A
  calibrated detection-vs-chance comparison for each configuration was not run.
- 20 normal stands, one Sentinel-2 tile, 2022–2026.

**APPROVED wording:** "With the same alert rule on the same 25 Abu Dhabi stands, the textbook NDVI-only approach raises 1.61 false alarms per
stand-year; our tide-aware monitor raises 0.96 — 40 % fewer, and the tide model alone accounts for most of the gain."
**NOT allowed:** "the textbook approach misses losses", "ours detects more conversions", any claim that the educational example is wrong.
