"""Static JSON alert feed on GitHub Pages: the 'alert API' of docs/api_alert_concept.md, served as files (no server).

  docs/api/v1/stands.json        list of stands: condition, alert now, cells in decline, carbon stock
  docs/api/v1/stands/<id>.json   one stand: the above + every alert episode (combined stand + cell rule) + cells in decline
  docs/api/v1/alerts.json        stands with an alert now, and episodes that started in the last 90 days
Inputs: analysis/data/stand_status.csv, union_status.csv, union_episodes.csv, substand/cell_status.csv (rebuilt by the pipeline, see analysis/README.md).
Run from the repository root after the pipeline:  python scripts/build_api.py
"""
import json, pathlib, datetime as dt
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
A = ROOT / "analysis/data"; OUT = ROOT / "docs/api/v1"; (OUT / "stands").mkdir(parents=True, exist_ok=True)
SITE = "https://nahla-nabil.github.io/blue-carbon-guardian/"

st = pd.read_csv(A / "stand_status.csv").set_index("stand")
un = pd.read_csv(A / "union_status.csv").set_index("stand")
ep = pd.read_csv(A / "union_episodes.csv")
cells = pd.read_csv(A / "substand/cell_status.csv")
rule = json.load(open(A / "union_series.json"))
reports = {int(p.stem.split("_")[1]) for p in (ROOT / "docs/reports").glob("stand_*_report.html")}
data_through = str(un.last_date.max())

META = {
    "service": "Blue Carbon Guardian - tide-aware mangrove monitor (Abu Dhabi pilot)",
    "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
    "data_through": data_through,
    "alert_rule": f"stand average <= -{rule['stand_thr']} sigma OR any 200 m cell <= -{rule['cell_thr']} sigma (median of the last 5 Sentinel-2 observations, "
                  "tide-, season- and trend-corrected); thresholds frozen, calibrated to about one false-alarm episode per stand-year",
    "condition_rule": "last 12 months vs the stand's own 2020-21 baseline: severe decline <= -50 %; decline <= -15 % and <= -3 sigma",
    "note": "Screening indicator, not ground truth. Verify with very-high-resolution imagery or on site.",
    "attribution": "Contains modified Copernicus Sentinel data 2020-2026. Carbon: Schile et al. 2016 field plots (CC0). Code: MIT.",
    "docs": "https://github.com/Nahla-Nabil/blue-carbon-guardian/blob/main/docs/api_alert_concept.md",
}


def r1(x): return None if pd.isna(x) else round(float(x), 1)


def stand_record(k):
    s, u = st.loc[k], un.loc[k]; c = cells[cells.stand == k]; bad = c[c.condition.isin(["decline", "severe decline"])]
    return {
        "stand": int(k), "area_ha": r1(s.area_ha), "condition": s.condition, "ndvi_change_pct": r1(s.ndvi_change_pct),
        "alert_now": bool(u.alert_now), "cells_alerting_now": [int(x) for x in str(u.cells_alerting_now).split()] if isinstance(u.cells_alerting_now, str) else [],
        "alert_episodes_2022_now": int(u.alerts_2022_2026), "last_observation": str(u.last_date),
        "cells_total": int(len(c)), "cells_in_decline": int(len(bad)), "ha_to_inspect": r1(bad.area_ha.sum()),
        "carbon_stock_t_c": {"p10": int(s.stock_tC_p10), "median": int(s.stock_tC_p50), "p90": int(s.stock_tC_p90)},
        "report": f"{SITE}reports/stand_{k:02d}_report.html" if k in reports else None,
        "detail": f"{SITE}api/v1/stands/{k}.json",
    }


rows = [stand_record(int(k)) for k in sorted(st.index)]
json.dump({**META, "stands": rows}, open(OUT / "stands.json", "w"), indent=1)
for r in rows:
    k = r["stand"]; e = ep[ep.stand == k].sort_values("start")
    c = cells[(cells.stand == k) & cells.condition.isin(["decline", "severe decline"])]
    detail = {**META, **r,
              "episodes": [{"start": a.start, "end": a.end, "days": int(a.days), "raised_by": a.source,
                            "cells": [int(x) for x in str(a.cells).split()] if isinstance(a.cells, str) else []} for a in e.itertuples()],
              "cells_in_decline_detail": [{"cell": int(x.cell), "condition": x.condition, "area_ha": r1(x.area_ha), "ndvi_change_pct": r1(x.ndvi_change_pct)} for x in c.itertuples()]}
    detail.pop("detail")
    json.dump(detail, open(OUT / "stands" / f"{k}.json", "w"), indent=1)

cut = (pd.Timestamp(data_through) - pd.Timedelta(days=90)).date().isoformat()
recent = ep[ep.start >= cut].sort_values("start", ascending=False)
alerts = {**META, "active_alerts": [r for r in rows if r["alert_now"]],
          "episodes_started_last_90_days": [{"stand": int(a.stand), "start": a.start, "end": a.end, "raised_by": a.source} for a in recent.itertuples()]}
json.dump(alerts, open(OUT / "alerts.json", "w"), indent=1)
print(f"docs/api/v1: {len(rows)} stands, data through {data_through}, active alerts {len(alerts['active_alerts'])}, episodes started since {cut}: {len(recent)}")
