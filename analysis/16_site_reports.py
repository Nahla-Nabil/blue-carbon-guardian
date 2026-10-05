"""Automatic site report per stand (English, printable HTML, no server). Every number comes from the analysis CSV/JSON files; the wording is templated
(no free-form generation), so the report can be regenerated for any stand and never states more than the data support.
Usage: python analysis/16_site_reports.py [stand ids...]   (default: stands 5, 9, 12, 18, 1, 6)
"""
import base64, io, json, sys, datetime
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

st = pd.read_csv("analysis/data/stand_status.csv").set_index("stand")
# product alert = combined rule (analysis/29-31): stand average <= -1.5 sigma OR any 200 m cell <= -3.5 sigma
ep = pd.read_csv("analysis/data/union_episodes.csv").fillna({"cells": ""}); us = pd.read_csv("analysis/data/union_status.csv").set_index("stand")
U = json.load(open("analysis/data/union_series.json")); st["alert_now"] = st.index.map(us.alert_now); st["alerts_2022_2026"] = st.index.map(us.alerts_2022_2026)
ser = json.load(open("analysis/data/dashboard_data.json"))["series"]; chg = pd.read_csv("analysis/data/change_by_stand.csv").set_index("stand")
ids = [int(a) for a in sys.argv[1:]] or [5, 9, 12, 18, 1, 6]
cells = np.load("analysis/data/substand/cells.npy"); cst = pd.read_csv("analysis/data/substand/cell_status.csv")
CCOL = {"stable": "#2E8B78", "decline": "#D99A1E", "severe decline": "#C8384F", "improving": "#3B78A8"}
COND = {"stable": "Stable", "decline": "Decline", "severe decline": "Severe decline", "improving": "Improving"}


def chart(k):
    s = ser[str(k)]; x = pd.to_datetime([m + "-01" for m in s["months"]])
    fig, ax = plt.subplots(2, 1, figsize=(8.2, 4.6), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
    ax[0].plot(x, s["ndmi"], color="#0B7A66", lw=1.8, label="NDMI (canopy moisture)"); ax[0].plot(x, s["ndvi"], color="#C98A10", lw=1.8, label="NDVI")
    for e in ep[ep.stand == k].itertuples(): [a.axvspan(pd.Timestamp(e.start), pd.Timestamp(e.end), color="#C8384F", alpha=.12, lw=0) for a in ax]
    ax[0].legend(frameon=False, fontsize=8, loc="upper right"); ax[0].set_ylabel("tide-corrected index", fontsize=8)
    u = U["series"].get(str(k), {}); zs = np.array([np.nan if u.get(m, [None])[0] is None else u[m][0] for m in s["months"]], float)
    zc = np.array([np.nan if u.get(m, [None, None])[1] is None else u[m][1] for m in s["months"]], float)
    ax[1].plot(x, np.clip(zc, -8, 3), color="#3B78A8", lw=1.2, label=f"worst 200 m cell (alert at -{U['cell_thr']})"); ax[1].axhline(-U["cell_thr"], color="#3B78A8", ls="--", lw=1)
    ax[1].plot(x, zs, color="#222", lw=1.3, label=f"stand average (alert at -{U['stand_thr']})"); ax[1].axhline(-U["stand_thr"], color="#222", ls="--", lw=1); ax[1].legend(frameon=False, fontsize=7, loc="lower left"); ax[1].axhline(0, color="#aaa", lw=.6)
    ax[1].set_ylabel("alert score (z)", fontsize=8); ax[1].set_ylim(-8.2, 3)
    for a in ax: a.tick_params(labelsize=8); [sp.set_visible(False) for sp in (a.spines["top"], a.spines["right"])]
    b = io.BytesIO(); plt.tight_layout(); plt.savefig(b, format="png", dpi=120); plt.close(fig); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def cell_map(k):
    """Where inside the stand: its 200 m cells (analysis/25-26) coloured by condition; returns (image uri, sentence)."""
    cs = cst[cst.stand == k]
    if cs.empty: return None, ""
    lut = np.zeros(cells.max() + 1, "int8"); codes = {c: i + 1 for i, c in enumerate(CCOL)}; lut[cs.cell.values] = cs.condition.map(codes).values
    img = lut[cells]; ys, xs = np.nonzero(img); y0, y1, x0, x1 = ys.min() - 5, ys.max() + 6, xs.min() - 5, xs.max() + 6; img = img[max(y0, 0):y1, max(x0, 0):x1]
    rgb = np.ones(img.shape + (3,))
    for c, i in codes.items(): rgb[img == i] = matplotlib.colors.to_rgb(CCOL[c])
    grid_ = np.zeros(img.shape, bool); cc = cells[max(y0, 0):y1, max(x0, 0):x1]; grid_[:, 1:] |= cc[:, 1:] != cc[:, :-1]; grid_[1:, :] |= cc[1:, :] != cc[:-1, :]
    rgb[grid_ & (img > 0)] = 1
    fig, ax = plt.subplots(figsize=(3.2, 3.2 * img.shape[0] / img.shape[1]) if img.shape[1] >= img.shape[0] else (3.2 * img.shape[1] / img.shape[0], 3.2))
    ax.imshow(rgb, interpolation="nearest"); ax.axis("off"); b = io.BytesIO(); plt.tight_layout(pad=0.1); plt.savefig(b, format="png", dpi=120); plt.close(fig)
    bad = cs[cs.condition.isin(["decline", "severe decline"])]
    txt = (f"<b>{len(bad)} of {len(cs)} cells</b> ({bad.area_ha.sum():.1f} ha of mangrove pixels) show {'severe ' if (bad.condition == 'severe decline').any() else ''}decline "
           "(red / amber). Inspect those first." if len(bad) else f"All {len(cs)} cells are {' or '.join(sorted(set(cs.condition)))}: no part of the stand stands out.")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode(), txt


def report(k):
    r = st.loc[k]; e = ep[ep.stand == k]; c = chg.loc[k] if k in chg.index else None
    f = lambda v, d=0: f"{v:,.{d}f}"
    cs = cst[cst.stand == k]; bad = cs[cs.condition.isin(["decline", "severe decline"])]
    if r.condition == "severe decline":
        summary = (f"Stand {k} shows a <b>severe decline</b>: its tide-corrected NDVI fell from {r.ndvi_base:.2f} (2020–21 median) to {r.ndvi_now:.2f}, and NDMI from {r.ndmi_base:.2f} to {r.ndmi_now:.2f}. "
                   "Recommended action: field or high-resolution inspection to confirm land-use change; do not treat the outline area as lost mangrove without checking (outlines come from a 2021 map).")
    elif r.condition == "decline":
        summary = f"Stand {k} shows a <b>decline</b> against its own 2020–21 baseline (NDVI {r.ndvi_change_pct:+.0f} %, NDMI {r.ndmi_change_pct:+.0f} %). Recommended action: schedule inspection."
    else:
        summary = f"Stand {k} is <b>{COND.get(r.condition, r.condition).lower()}</b> on average against its own 2020–21 baseline (NDVI {r.ndvi_change_pct:+.0f} %, NDMI {r.ndmi_change_pct:+.0f} %). "
        summary += (f"<b>But {len(bad)} of its {len(cs)} cells (200 m blocks, {bad.area_ha.sum():.1f} ha) {'shows' if len(bad) == 1 else 'show'} {'severe ' if (bad.condition == 'severe decline').any() else ''}decline</b>: a partial change that the stand average hides. "
                    "Recommended action: inspect the flagged part (map below)." if len(bad) else "No inspection is triggered by the indicators, at stand or cell level.")
    SRC = {"stand": "stand average", "cells": "cells", "both": "stand average + cells"}
    epi = "".join(f"<tr><td>{x.start}</td><td>{x.end}</td><td class=n>{x.days}</td><td>{SRC[x.source]}</td><td>{len(str(x.cells).split()) if x.cells else 0}</td></tr>" for x in e.itertuples()) or "<tr><td colspan=5>None in 2022–2026</td></tr>"
    cimg, ctxt = cell_map(k)
    cell_html = (f'<h2>Where inside the stand (200 m cells)</h2><div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center"><img alt="200 m cells of stand {k} coloured by condition" src="{cimg}" style="width:260px;max-width:100%">'
                 f'<p style="flex:1;min-width:220px">{ctxt} The same monitor and condition rule run on each 4 ha block. Cells count all their mangrove pixels, so cell area is coarser than a loss estimate. '
                 'Green stable, amber decline, red severe decline, blue improving.</p></div>') if cimg else ""
    chg_txt = (f"The 2021→2025 epoch-difference indicator flags {c.loss_ha:.1f} ha ({c.loss_pct:.1f} % of the outline on its grid) as vegetation loss. This is a screening flag, not a measured loss area." if c is not None else "")
    return f"""<!doctype html><html lang=en><meta charset=utf-8><title>Site report: stand {k}</title>
<style>body{{font:14px/1.55 "Segoe UI",Arial,sans-serif;color:#12302E;max-width:820px;margin:24px auto;padding:0 16px}}h1{{font-size:24px;margin:0}}h2{{font-size:16px;margin:22px 0 6px;border-bottom:1px solid #D3DEDA;padding-bottom:3px}}
.k{{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}}.k div{{border:1px solid #D3DEDA;border-radius:8px;padding:6px 12px;min-width:120px}}.k b{{display:block;font-size:18px}}.k span{{font-size:12px;color:#4A6461}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #D3DEDA;padding:4px 8px;text-align:left}}td.n,th.n{{text-align:right}}.w{{background:#FBEBCF;padding:8px 12px;border-radius:8px;font-size:13px}}small{{color:#4A6461}}img{{width:100%}}</style>
<h1>Mangrove site report: stand {k}</h1><small>Blue Carbon Guardian · Abu Dhabi · generated {datetime.date.today():%d %b %Y} · data to {r.last_obs} · screening indicators, not ground truth</small>
<div class=k><div><b>{f(r.area_ha,1)} ha</b><span>outline area (WorldCover 2021)</span></div><div><b>{COND.get(r.condition, r.condition)}</b><span>condition vs 2020–21 baseline</span></div>
<div><b>{'Yes' if r.alert_now else 'No'}</b><span>active alert today</span></div><div><b>{int(r.alerts_2022_2026)}</b><span>alert episodes 2022–26</span></div></div>
<h2>Summary</h2><p>{summary}</p><p>{chg_txt}</p>
{cell_html}
<h2>Trend</h2><img alt="time series" src="{chart(k)}"><p><small>Monthly medians of tide-corrected indices (interior pixels only). Red bands: alert episodes.</small></p>
<h2>Alert episodes</h2><p><small>Alert = the stand average at or below −{U['stand_thr']} σ OR any 200 m cell at or below −{U['cell_thr']} σ, calibrated together to about one false-alarm episode per stand-year. A stand with no known change is in alert about {round(100 * U['in_alert_share'])} % of the time.</small></p>
<table><tr><th>Start</th><th>End</th><th class=n>Days</th><th>Raised by</th><th>Cells</th></tr>{epi}</table>
<h2>Carbon stock (indicative)</h2><p>About <b>{f(r.stock_tC_p50/1000,1)} kt C</b> (90 % range {f(r.stock_tC_p10/1000,1)}–{f(r.stock_tC_p90/1000,1)}), ≈ {f(r.stock_tCO2e_p50/1000,1)} kt CO<sub>2</sub>e. Method: outline area × mean density 108 t C/ha (24 field plots at four nearby sites; trees + top 1 m of soil; Schile et al. 2016, Dryad doi:10.15146/R3K59Z).
This is a <b>stock</b>, not an emission or a sequestration rate, and it is an upper bound for outlines that include non-mangrove ground.</p>
<h2>Method and limits</h2><ul><li>Sentinel-2 L2A (ESA/Copernicus) 2020–2026; tide handled by regressing indices on a water-wetness signal; alert threshold calibrated to about one false-alarm episode per stand-year.</li>
<li>Simulation test (false alarms held to about one per stand-year; detection = a new alert after the loss begins): a partial loss (a tenth of a stand losing half its canopy) is caught within 60 days in about 73 % of cases, against about 13 % by chance; a uniform 10 % loss of the whole stand within six months in about 63 % (36 % by chance).</li>
<li>Condition compares the last 12 months (a full seasonal cycle) with the 2020–21 median. In the five conversions confirmed on dated sub-metre imagery (stands 5, 9, 12, 18, 6), the alert began between the last undisturbed capture and the first capture showing works: detection of works as they happen, not advance warning.</li>
<li>Not shown: leaf-level physiological stress. Two EnMAP hyperspectral dates confirm the Sentinel-2 indices but cannot separate stress from season and tide.</li></ul>
<p class=w>Indicators are screening results. Confirm any decision-relevant finding with field or very-high-resolution imagery. Contains modified Copernicus Sentinel data. ESA WorldCover 2021 (CC BY 4.0).</p></html>"""


import os; os.makedirs("reports", exist_ok=True)
for k in ids:
    open(f"reports/stand_{k:02d}_report.html", "w", encoding="utf-8").write(report(k)); print("reports/" + f"stand_{k:02d}_report.html")
