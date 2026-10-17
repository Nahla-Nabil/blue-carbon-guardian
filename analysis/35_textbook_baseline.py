"""Baseline comparison: the textbook approach (NDVI alone, no tide model) against our monitor, on the same 25 pilot stands and 620 cells.

Why: the common educational recipe for mangrove health is a vegetation index (NDVI) followed by anomaly detection or a classifier. On Gulf tidal
flats the tide drives most of the date-to-date change in the index. This script measures what that costs, using exactly the same alert machinery
as the product (monthly rolling refit on [t-36 m, t-3 m], robust z, median of the last 5, rule: stand <= -1.5 sigma OR any cell <= -3.5 sigma).

Configurations (only the model inside changes):
  A  textbook : NDVI only, trend + season, no tide terms
  B           : NDVI only, with tide terms
  C           : NDVI + red edge + SWIR moisture (composite), no tide terms
  D  ours     : composite, with tide terms (the product)
Metrics, 2022-2026:
  1. false-alarm episodes per stand-year on the 20 stands with no known conversion (5, 6, 9, 12, 18 excluded)
  2. share of time a normal stand is in alert
  3. for the 5 confirmed conversions: does an alert episode START inside the window [last intact, first disturbed] sub-metre capture?
Output: analysis/data/textbook_baseline.json, analysis/35_textbook_baseline.md
"""
import json, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "src")
from bcg import monitor as M

EVENTS = {5: ("2022-03-28", "2023-02-22"), 9: ("2022-03-28", "2023-02-22"), 12: ("2022-03-28", "2023-02-22"),
          6: ("2022-03-28", "2023-02-22"), 18: ("2023-11-14", "2025-01-06")}       # analysis/34_vhr_summary.md
CFG = {"A": (["ndvi"], False), "B": (["ndvi"], True), "C": (M.IDX, False), "D": (M.IDX, True)}


def monitor(s, y, tide):
    t, w, ff = s["t"], s["w"], s["ff"]; ot, oz = [], []
    tf, tt = (pd.Timestamp("2022-01-01") - M.T0).days, (pd.Timestamp("2026-12-31") - M.T0).days
    for m in pd.period_range("2022-01", "2026-12", freq="M"):
        ms = (m.start_time - M.T0).days; me = (m.end_time - M.T0).days
        tr = (t >= ms - M.TRAIN_MONTHS * 30.44) & (t <= ms - M.GUARD_D); te = (t >= max(ms, tf)) & (t <= min(me, tt))
        if tr.sum() < 80 or not te.any():
            continue
        X = (lambda a: M.design(t[a], w[a], ff[a])) if tide else (lambda a: M.design(t[a]))
        beta, sig = M.rfit(X(tr), y[tr]); ot.append(t[te]); oz.append((y[te] - X(te) @ beta) / sig)
    return (np.concatenate(ot), np.concatenate(oz)) if ot else (np.array([]), np.array([]))


def state(s, idx, tide):
    zs = {i: monitor(s, s["y"][i], tide) for i in idx}; t = zs[idx[0]][0]
    if len(t) == 0:
        return t, t
    return t, pd.Series(np.mean([zs[i][1] for i in idx], axis=0)).rolling(M.K_MED, min_periods=M.K_MED).median().values


t0 = time.time()
cells = pd.read_csv("analysis/data/substand/cells.csv")
stats = pd.read_csv("analysis/data/substand/cell_stats.csv")
CSER = {c: M.to_series(g) for c, g in stats.groupby("cell")}
stands = sorted(cells.stand.unique())
out = {}
for name, (idx, tide) in CFG.items():
    eps_normal, years, in_alert, ev = 0, 0.0, [], {}
    for k in stands:
        ids = [c for c in cells[cells.stand == k].cell if c in CSER]
        proxy = M.stand_proxy([CSER[c] for c in ids], cells[cells.stand == k].n_px.sum())
        t, on, _, _ = M.product_alert(state(proxy, idx, tide), [state(CSER[c], idx, tide) for c in ids])
        eps = M.episodes(t, on)
        if k in EVENTS:
            lo, hi = (pd.Timestamp(x).date() for x in EVENTS[k])
            first = [str(a) for a, _ in eps if lo <= a <= hi]
            ev[int(k)] = first[0] if first else None
        else:
            span = (t[-1] - t[0]) / 365.25; eps_normal += len(eps); years += span; in_alert.append(float(on.mean()))
    out[name] = dict(indices=idx, tide=tide, false_alarm_episodes_per_stand_year=round(eps_normal / years, 2),
                     normal_stand_time_in_alert=round(float(np.mean(in_alert)), 3), stand_years=round(years, 1),
                     events_alert_started_in_window=ev, events_caught=sum(v is not None for v in ev.values()))
    print(name, out[name], f"{time.time() - t0:.0f}s", flush=True)
json.dump(out, open("analysis/data/textbook_baseline.json", "w"), indent=1)
