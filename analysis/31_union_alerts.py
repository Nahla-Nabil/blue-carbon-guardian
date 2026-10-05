"""Product alerts with the recommended combined rule (analysis/29): alert a stand when its average is at or below -1.5 sigma OR any of its 200 m cells is at or
below -3.5 sigma (median-of-5 composite z; calibrated to about 1 false-alarm episode per stand-year on the real 2022-2026 series).

Reuses analysis/29 up to its calibration (cached monitor states, date grids, thresholds), then writes for the dashboard and the site reports:
  analysis/data/union_episodes.csv : stand, start, end, days, source (stand / cells / both), cells that alerted, min stand z, min cell z
  analysis/data/union_status.csv   : stand, alert_now, alerts_2022_2026, cells_alerting_now, last_date
  analysis/data/union_series.json  : per stand, monthly median of the stand score and of the worst-cell score (for the charts), thresholds
"""
import json, numpy as np, pandas as pd

src = open("analysis/29_cell_trigger.py", encoding="utf-8").read().split("# ---- real events")[0]; ns = {"__name__": "union"}; exec(src, ns)
GRID, ST_STAND, HALF, T0, n_episodes, UNION_RATE = ns["GRID"], ns["ST_STAND"], ns["HALF"], ns["T0"], ns["n_episodes"], ns["UNION_RATE"]
TS, TC = HALF["STAND"], HALF["CELL-1"]
print(f"combined rule: stand <= -{TS} sigma OR any cell <= -{TC} sigma (realised {UNION_RATE:.2f} episodes per stand-year)")
day = lambda x: (T0 + pd.Timedelta(days=float(x))).date()

eps, status, series = [], [], {}
for k, G in GRID.items():
    ts, zs = ST_STAND[k]; zs = np.nan_to_num(zs, nan=0.0)
    # stand score carried onto the grid dates (the grid contains the stand dates)
    j = np.searchsorted(ts, G["dates"], side="right") - 1; ok = (j >= 0) & (G["dates"] - ts[np.clip(j, 0, None)] <= 20)
    zs_g = np.where(ok, zs[np.clip(j, 0, None)], np.nan)
    M = G["M"]; worst = np.nanmin(np.where(np.isnan(M), np.inf, M), axis=0); worst[np.isinf(worst)] = np.nan
    on_s = np.nan_to_num(zs_g, nan=0.0) <= -TS; al_c = np.nan_to_num(M, nan=0.0) <= -TC; on_c = al_c.any(0); on = on_s | on_c
    t = G["dates"]; idx = np.nonzero(on)[0]; groups = []
    for a in idx:
        if groups and t[a] - t[groups[-1][-1]] <= 30: groups[-1].append(a)
        else: groups.append([a])
    for g in groups:
        g = np.array(g); src_s, src_c = on_s[g].any(), on_c[g].any()
        cells = sorted({G["cells"][r] for r in np.nonzero(al_c[:, g].any(1))[0]})
        eps.append(dict(stand=k, start=day(t[g[0]]), end=day(t[g[-1]]), days=int(t[g[-1]] - t[g[0]]),
                        source="both" if src_s and src_c else ("stand" if src_s else "cells"), cells=" ".join(map(str, cells)),
                        min_stand_z=round(float(np.nanmin(zs_g[g])), 2) if np.isfinite(zs_g[g]).any() else None,
                        min_cell_z=round(float(np.nanmin(worst[g])), 2) if np.isfinite(worst[g]).any() else None))
    last = len(t) - 1
    status.append(dict(stand=k, alert_now=bool(on[last]), alerts_2022_2026=len(groups), last_date=day(t[last]),
                       cells_alerting_now=" ".join(str(G["cells"][r]) for r in np.nonzero(al_c[:, last])[0])))
    m = pd.DataFrame({"stand_z": zs_g, "worst_cell_z": worst}, index=pd.to_datetime([day(x) for x in t])).resample("MS").median()
    series[int(k)] = {mm.strftime("%Y-%m"): [None if np.isnan(a) else round(float(a), 2), None if np.isnan(b) else round(float(b), 2)]
                      for mm, a, b in zip(m.index, m.stand_z, m.worst_cell_z)}

E = pd.DataFrame(eps); S = pd.DataFrame(status)
E.to_csv("analysis/data/union_episodes.csv", index=False); S.to_csv("analysis/data/union_status.csv", index=False)
json.dump(dict(stand_thr=TS, cell_thr=TC, rate_per_stand_year=round(UNION_RATE, 2), series=series), open("analysis/data/union_series.json", "w"))
yrs = sum((ST_STAND[k][0].max() - ST_STAND[k][0].min()) / 365.25 for k in ST_STAND)
print(f"{len(E)} episodes over {yrs:.0f} stand-years ({len(E) / yrs:.2f} per stand-year); by source: {E.source.value_counts().to_dict()}; active now: {int(S.alert_now.sum())}")
print(S.sort_values("alerts_2022_2026", ascending=False).head(8).to_string(index=False))
for k in (5, 9, 12, 18): print(f"stand {k}:", E[E.stand == k][["start", "end", "source", "cells"]].to_string(index=False, header=False).replace("\n", " | "))

# ---- how often is a stand 'in alert' by chance? and the four events under the combined rule ----------------------------------------------------
EXCL = {5, 6, 9, 12, 18}
frac = []
for k, G in GRID.items():
    if k in EXCL: continue
    e = E[E.stand == k]; t = G["dates"]; span = t.max() - t.min()
    inside = sum(min((pd.Timestamp(r.end) - T0).days, t.max()) - max((pd.Timestamp(r.start) - T0).days, t.min()) for r in e.itertuples())
    frac.append(inside / span)
IN_ALERT = float(np.mean(frac)); print(f"share of time in alert, stands without known change: {100 * IN_ALERT:.0f} % (range {100 * min(frac):.0f}-{100 * max(frac):.0f} %)")
EVENTS = {5: "2023-02-14", 9: "2023-06-14", 12: "2022-08-04", 18: "2025-02-03"}   # dated starts (21, 28); stand 12 = last intact image
ev = {}
for k, d0 in EVENTS.items():
    d0 = pd.Timestamp(d0); e = E[E.stand == k].assign(s=lambda x: pd.to_datetime(x.start), f=lambda x: pd.to_datetime(x.end))
    cov = e[(e.s <= d0) & (e.f >= d0)]; nxt = e[e.s > d0].sort_values("s")
    ev[k] = dict(change_start=str(d0.date()), in_alert_at_start_since=str(cov.s.iloc[0].date()) if len(cov) else None,
                 next_new_alert=str(nxt.s.iloc[0].date()) if len(nxt) else None, next_source=nxt.source.iloc[0] if len(nxt) else None)
print(json.dumps(ev, indent=1))
S.merge(pd.DataFrame([dict(stand=k, stand_z_now=v[max(v)][0], worst_cell_z_now=v[max(v)][1]) for k, v in series.items()]), on="stand").to_csv("analysis/data/union_status.csv", index=False)
d = json.load(open("analysis/data/union_series.json")); d.update(in_alert_share=round(IN_ALERT, 3), events=ev); json.dump(d, open("analysis/data/union_series.json", "w"))
