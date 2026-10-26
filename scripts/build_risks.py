"""Risk register: every flagged stand becomes a case, ranked by priority, that stays open until a person closes it with a reason.
Added after expert feedback from the Bahrain Space Agency (26 Oct 2026): rank alerts (urgent vs monitor) and give each one a date,
likely cause, confidence level and expected inspector action.

Inputs : analysis/data/substand/cell_status.csv, union_episodes.csv, union_status.csv (pipeline outputs)
         + the human review log below (REVIEWS): what a person found when checking a case on imagery.
Outputs: analysis/data/risk_register.json (read by scripts/build_site.py) and docs/api/v1/risks.json (public feed).
Run from the repository root after the pipeline:  python scripts/build_risks.py

Priority rule
  urgent  : loss confirmed on sub-metre imagery AND >= 10 ha of 200 m cells in decline
  monitor : a smaller confirmed loss, or cells in decline that nobody has checked yet
  closed  : checked by a person and closed with a reason (e.g. a tide effect, not a loss)
Confidence
  high    : confirmed on dated sub-metre imagery, stand alert and cells agree
  low     : one or two cells, not yet checked on imagery
Carbon at stake = area x 108 t C/ha (90 % CI 79-138, Schile et al. 2017). For stand 5 the converted area (26-62 ha, Sentinel-2 and
EnMAP estimates) is used; elsewhere the whole-cell area, so the value is an upper bound.
"""
import json, pathlib, datetime as dt
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
A = ROOT / "analysis/data"
DENSITY, LO, HI = 108, 79, 138          # t C / ha, field plots near the stands

cells = pd.read_csv(A / "substand/cell_status.csv")
ep = pd.read_csv(A / "union_episodes.csv")
un = pd.read_csv(A / "union_status.csv").set_index("stand")
data_through = str(un.last_date.max())

# Human review log: cases a person has checked on dated sub-metre imagery (analysis/34_vhr_summary.md) or on the data.
CONFIRMED = {   # stand: (alert start of the conversion, cause EN, cause AR)
    5: ("2022-10-25", "Coastal development: reclamation with finger canals", "تطوير ساحلي: ردم مع قنوات متفرعة"),
    9: ("2022-12-07", "Coastal development: canals in the south-east", "تطوير ساحلي: قنوات في الجنوب الشرقي"),
    12: ("2022-12-17", "Coastal development: canal and reclamation at the southern edge", "تطوير ساحلي: قناة وردم على الحافة الجنوبية"),
    6: ("2023-02-17", "Coastal development: canals and a lagoon around the stand", "تطوير ساحلي: قنوات وبحيرة حول المنطقة"),
    18: ("2024-10-29", "Coastal development reaching the stand in 2025", "تطوير ساحلي وصل المنطقة في 2025"),
}
CLOSED = {      # stand: (alert start, closed on, reason EN, reason AR)
    3: ("2026-10-22", "2026-10-26",
        "Low tide in the image: the canopy was greener than in the previous ten images, so a tide effect, not a loss",
        "مدّ منخفض في الصورة: كان الغطاء أكثر اخضراراً من الصور العشر السابقة، فهو أثر للمدّ لا خسارة"),
}


def first_alert(stand, cell_ids):
    """Earliest combined-rule episode of this stand that names one of the given cells."""
    e = ep[ep.stand == stand].sort_values("start")
    for a in e.itertuples():
        named = {int(x) for x in str(a.cells).split()} if isinstance(a.cells, str) else set()
        if named & set(cell_ids): return a.start
    return None


def carbon(ha_lo, ha_hi=None):
    ha_hi = ha_lo if ha_hi is None else ha_hi
    return {"t_c_median_low": round(ha_lo * DENSITY), "t_c_median_high": round(ha_hi * DENSITY),
            "t_c_range": [round(ha_lo * LO), round(ha_hi * HI)]}


risks = []
bad = cells[cells.condition.isin(["decline", "severe decline"])]
for stand, g in bad.groupby("stand"):
    stand = int(stand); ids = [int(c) for c in g.cell]; ha = round(float(g.area_ha.sum()), 1)
    if stand in CONFIRMED:
        opened, cause_en, cause_ar = CONFIRMED[stand]
        prio = "urgent" if ha >= 10 else "monitor"
        conf, conf_ar = "high", "عالية"
        basis = "Confirmed on dated sub-metre imagery (0.3-0.5 m); stand alert and cells agree."
        basis_ar = "مؤكدة بصور مؤرّخة دون المتر (0.3–0.5 م)، وإنذار المنطقة والخلايا متّفقان."
        act = (f"Inspect the {len(ids)} flagged cells ({ha} ha); compare the works boundary with the permit; record the loss for carbon accounting."
               if prio == "urgent" else f"At the next visit, compare the works boundary with the permit; keep watching the {len(ids)} cells.")
        act_ar = (f"تفتيش الخلايا الـ{len(ids)} المنبَّه عليها ({ha} هكتار)، ومقارنة حدود الأعمال بالترخيص، وتسجيل الخسارة في حساب الكربون."
                  if prio == "urgent" else f"في الزيارة القادمة: مقارنة حدود الأعمال بالترخيص، ومتابعة الخلايا الـ{len(ids)}.")
        c = carbon(26, 62) if stand == 5 else carbon(ha)
    else:
        opened = first_alert(stand, ids) or data_through
        prio, conf, conf_ar = "monitor", "low", "منخفضة"
        cause_en, cause_ar = "Unknown: not yet checked on imagery", "غير معروف: لم يُفحص بالصور بعد"
        basis = f"{len(ids)} cell(s) below the 2020-21 baseline; one sensor, not yet checked."
        basis_ar = f"{len(ids)} خلية دون خط أساس 2020–2021؛ مصدر واحد ولم تُفحص بعد."
        act = f"Check the latest sub-metre image of cell {', '.join(map(str, ids))} before sending anyone."
        act_ar = f"فحص أحدث صورة دون المتر للخلية {', '.join(map(str, ids))} قبل إرسال أي شخص."
        c = carbon(ha)
    risks.append({"id": f"R-{stand:02d}", "stand": stand, "priority": prio, "status": "open", "opened": opened,
                  "likely_cause": {"en": cause_en, "ar": cause_ar}, "confidence": {"en": conf, "ar": conf_ar},
                  "confidence_basis": {"en": basis, "ar": basis_ar}, "action": {"en": act, "ar": act_ar},
                  "cells": ids, "ha_to_inspect": ha, "carbon_at_stake": c,
                  "carbon_note": "converted area 26-62 ha x 108 t C/ha" if stand == 5 else "upper bound: whole-cell area x 108 t C/ha"})

for stand, (opened, closed, why_en, why_ar) in CLOSED.items():
    named = un.loc[stand].cells_alerting_now
    risks.append({"id": f"R-{stand:02d}", "stand": stand, "priority": "closed", "status": "closed", "opened": opened, "closed": closed,
                  "likely_cause": {"en": why_en, "ar": why_ar}, "confidence": {"en": "checked: no loss", "ar": "فُحصت: لا خسارة"},
                  "confidence_basis": {"en": "Checked by a person on the image data.", "ar": "فحصها شخص على بيانات الصورة."},
                  "action": {"en": "None. Closed with the reason recorded.", "ar": "لا شيء. أُغلقت مع تسجيل السبب."},
                  "cells": [int(x) for x in str(named).split()] if isinstance(named, str) else [], "ha_to_inspect": 0, "carbon_at_stake": None})

ORDER = {"urgent": 0, "monitor": 1, "closed": 2}
risks.sort(key=lambda r: (ORDER[r["priority"]], -r["ha_to_inspect"]))
out = {"generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "data_through": data_through,
       "rule": {"urgent": "loss confirmed on sub-metre imagery and >= 10 ha of cells in decline",
                "monitor": "smaller confirmed loss, or cells in decline not yet checked",
                "closed": "checked by a person and closed with a reason"},
       "note": "Cases stay open until a person closes them with a reason. Screening indicator, not ground truth. "
               "Prioritisation added after expert evaluation and feedback from the Bahrain Space Agency.",
       "counts": {p: sum(r["priority"] == p for r in risks) for p in ORDER}, "risks": risks}
json.dump(out, open(A / "risk_register.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
(ROOT / "docs/api/v1").mkdir(parents=True, exist_ok=True)
json.dump(out, open(ROOT / "docs/api/v1/risks.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(out["counts"], [(r["id"], r["priority"], r["ha_to_inspect"]) for r in risks])
