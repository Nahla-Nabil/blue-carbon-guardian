# Stand-level backtest re-tested with a null scenario (analysis/30)

Re-test of the stand-level backtest (analysis/07) with a NULL scenario and onset-based detection.

Problem found on 2026-09-27 (analysis/29): analysis/07 counted a trial as 'detected' if the alert state was on at ANY date after the injected loss began.
An alert episode already running at the start (episodes last weeks to months), or a real change in the same stand, then counts as a detection, and 07 had no
no-loss scenario to show how often that happens by chance.
Here, on the same stand series (config B, thresholds of analysis/08: NDVI 1.3, NDRE 1.4, NDMI 1.4, composite 1.3 sigma):
  - detection = a NEW alert episode (no alert in the previous 30 days) starting within [t0, t0 + 180 d]
  - scenarios: NO loss (null = detection by chance), and whole-stand canopy-cover loss 5 / 10 / 20 % (linear mixing, 60-day ramp, bare NDVI .05 / NDRE .03 / NDMI 0)
  - stands with changes seen on imagery (5, 6, 9, 12, 18) are excluded from the trials
  - the old metric of 07 is also reported on the same trials, to show the size of the bias
Outputs: analysis/data/backtest_null_trials.csv, analysis/30_backtest_null.md


new_* = onset-based detection (% of trials, within 60 / 180 days); old_* = the metric of analysis/07; lift = new minus the null rate of the same detector.

|                |   n |   new_60 |   new_180 |   old_60 |   old_180 |   lift_60 |   lift_180 |
|:---------------|----:|---------:|----------:|---------:|----------:|----------:|-----------:|
| (0.0, 'comp')  | 240 |     15.4 |      40.4 |     31.7 |      51.7 |       0   |        0   |
| (0.0, 'ndmi')  | 240 |     13.8 |      36.2 |     27.9 |      46.7 |       0   |        0   |
| (0.0, 'ndre')  | 240 |     15.8 |      40.4 |     34.6 |      54.2 |       0   |        0   |
| (0.0, 'ndvi')  | 240 |     18.3 |      44.2 |     34.6 |      55.4 |       0   |        0   |
| (0.05, 'comp') | 240 |     22.9 |      51.2 |     39.6 |      64.2 |       7.5 |       10.8 |
| (0.05, 'ndmi') | 240 |     25.8 |      56.7 |     40.4 |      66.2 |      12   |       20.5 |
| (0.05, 'ndre') | 240 |     19.2 |      43.8 |     37.5 |      58.8 |       3.4 |        3.4 |
| (0.05, 'ndvi') | 240 |     22.1 |      53.8 |     38.8 |      67.5 |       3.8 |        9.6 |
| (0.1, 'comp')  | 240 |     29.6 |      64.6 |     46.2 |      80   |      14.2 |       24.2 |
| (0.1, 'ndmi')  | 240 |     35.4 |      72.5 |     50   |      84.6 |      21.6 |       36.3 |
| (0.1, 'ndre')  | 240 |     24.2 |      52.5 |     42.5 |      68.8 |       8.4 |       12.1 |
| (0.1, 'ndvi')  | 240 |     31.2 |      65.4 |     49.2 |      80.4 |      12.9 |       21.2 |
| (0.2, 'comp')  | 240 |     51.2 |      80   |     68.8 |      96.7 |      35.8 |       39.6 |
| (0.2, 'ndmi')  | 240 |     62.9 |      82.9 |     77.5 |      97.1 |      49.1 |       46.7 |
| (0.2, 'ndre')  | 240 |     39.6 |      72.9 |     58.8 |      90.4 |      23.8 |       32.5 |
| (0.2, 'ndvi')  | 240 |     45.4 |      80.4 |     65.4 |      98.8 |      27.1 |       36.2 |
