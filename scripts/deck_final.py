"""Final-judging deck (21-23 Oct 2026): 8-minute pitch + 4-minute Q&A, scored on the organisers' final criteria
(team, space-data use, problem/user fit, innovation, scientific reliability, presentation; bonus: scalability, documentation/reproducibility).
Reuses the PoC slides built by scripts/deck_v5.py (same design and numbers), adds a team slide (required by the organisers),
a scalability + reproducibility slide and a closing slide, merges validation and impact, and replaces every speaker note with a timed script.
Every number is one already approved in the analysis summaries. Run from the repository root:
    python scripts/deck_final.py && python scripts/export_slides_pdf.py deck_final docs/final_deck.pdf
Writes deck_final/deck.json, deck_final/slides/*.html and docs/pitch_script.md.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import deck_v5 as v  # builds the PoC slides in memory (v.S); does not write them

OUT = ROOT / "deck_final"; SL = OUT / "slides"; SL.mkdir(parents=True, exist_ok=True)
NAVY, BLUE, CYAN, ICE, CORAL, AMBER, MUTED = v.NAVY, v.BLUE, v.CYAN, v.ICE, v.CORAL, v.AMBER, v.MUTED
icon, light, dark = v.icon, v.light, v.dark
for k in ("team", "validation", "impact", "scale", "close", "different", "sequence"):
    v.NOTES[k] = ""  # notes are attached below

ORDER = ["cover", "team", "problem", "product", "usecase", "data", "hyperspectral", "solution", "sequence", "innovation", "cells", "different", "validation-real", "validation", "impact", "scale", "close"]
TOTAL = len(ORDER)
S = {k: v.S[k] for k in ("cover", "problem", "usecase", "data", "innovation", "cells", "product", "validation-real", "hyperspectral", "solution")}

# ---- small edits to reused slides ------------------------------------------------------------------------------------
S["cover"] = S["cover"].replace("Arab Youth Space Hackathon 2026 &#183; Challenge 813", "Arab Youth Space Hackathon 2026 &#183; Challenge 813 &#183; Final")
S["product"] = S["product"].replace('<span class="pill">JSON alert API (concept)</span>',
                                    '<span class="pill">JSON alert API (concept)</span><span class="pill" style="background:#06235A;color:#fff;border-color:#06235A">live: nahla-nabil.github.io/blue-carbon-guardian</span>')
S["validation-real"] = S["validation-real"].replace("Validation 1 &#183; real events", "Validation 1 &#183; real events")

# ---- NEW: team (required by the organisers: roles, responsibilities, relevant expertise) -----------------------------
roles = [("target", "Project lead &amp; product owner", "problem framing, user needs, scope, every claim on these slides"),
         ("sat", "Earth-observation data engineer", "Sentinel-2 series (778 dates), EnMAP reader, WorldCover stands, sub-metre checks"),
         ("chart", "Modelling &amp; statistics", "tide-aware model, stand + cell alert rule, calibration against chance"),
         ("shield", "Validation &amp; scientific integrity", "real events, simulations, unseen stands, a withdrawn claim"),
         ("layers", "Product &amp; delivery", "dashboard, website, site reports, alert API concept, notebook"),
         ("dollar", "Business &amp; impact", "customers, pricing hypotheses, unit economics, carbon with ranges")]
rc = "".join(f'<div class="card" style="display:flex;gap:20px;align-items:center;padding:18px 24px">{icon(i, 30)}<div><p class="t b" style="font-size:25px">{a}</p><p class="s" style="font-size:19px;margin-top:4px">{b}</p></div></div>' for i, a, b in roles)
skills = ["AI / LLM backend engineering", "machine learning", "computer vision (deepfake detection)", "federated learning", "semantic search systems", "Python geospatial stack"]
S["team"] = light("team", 2, "The team", "One engineer, every role &#8212; delivered in the open", f"""
<div class="row" style="gap:28px;flex:1">
  <div class="card dk" style="width:560px;padding:26px 30px;display:flex;flex-direction:column;gap:12px;justify-content:space-between">
    <div style="display:flex;gap:20px;align-items:center"><img src="images/nahla.png" style="width:130px;height:130px;border-radius:50%;border:4px solid #8FD3FF"><div><p style="font-size:38px;font-weight:700">Nahla Nabil</p><p class="s ws" style="font-size:19px">Team lead &#183; AI engineer &#183; IEEE researcher &#183; Bahrain</p></div></div>
    <p class="lab" style="color:#8FD3FF;margin-top:4px">Education</p>
    <p class="t w" style="font-size:20px"><b>BSc Artificial Intelligence</b> &#183; Arab Open University, Bahrain &#183; final semester &#183; First-Class Honours standing</p>
    <p class="lab" style="color:#8FD3FF;margin-top:4px">Relevant expertise</p>
    <ul style="color:#fff;font-size:18px;line-height:1.45;padding-left:22px;margin:0">
      <li>2 IEEE papers: federated learning for industrial IoT (ICCA 2025); random-forest audit of GCC sustainability indicators (ICAISET 2026)</li>
      <li>AI &amp; LLM product engineering (Doo Bahrain; FlyRank backend AI)</li>
      <li>Machine learning, computer vision (deepfake detection), Python geospatial stack</li></ul>
    <p class="lab" style="color:#8FD3FF;margin-top:4px">Community</p>
    <p class="t w" style="font-size:19px">NASA Space Apps Challenge local lead (Manama): organising and mentoring space-data teams</p>
  </div>
  <div class="col" style="flex:1;gap:14px">
    <p class="lab" style="color:{BLUE}">Roles &amp; responsibilities in this project</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:1fr;gap:14px;flex:1">{rc}</div>
    <div class="card" style="padding:18px 24px;border-left:6px solid {CYAN}"><p class="t b" style="font-size:23px">The gap we will close in incubation</p>
      <p class="s" style="margin-top:6px;font-size:19px">a mangrove ecologist as mentor &#183; a restoration or agency partner for site records &#183; a GIS analyst for scale-out</p></div>
  </div>
</div>""")

# ---- NEW: validation (simulation + unseen stands + EnMAP + what we do not claim) -------------------------------------
S["validation"] = light("validation", 10, "Validation 2 &#183; against chance, out of sample, second sensor", "Every rate next to its chance rate", f"""
<div class="row" style="gap:26px;flex:1">
  <div class="card" style="width:1060px;padding:20px 28px;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{BLUE}">Artificial loss injected into real stands with no known change</p>
    <p class="s" style="margin:6px 0 12px;font-size:19px">Counts only a <b>new</b> alert after the loss starts; the same test with no loss gives the chance rate. ~160&#8211;240 trials per row.</p>{v.sim_chart()}</div>
  <div class="col" style="flex:1;gap:16px">
    <div class="card" style="padding:18px 24px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{MUTED}">False alarms &#183; calibrated, 25 stands</p><p class="big" style="margin-top:6px;font-size:56px">0.96</p><p class="s" style="font-size:18px">episodes per stand-year</p></div>
    <div class="card dk" style="padding:18px 24px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:#8FD3FF">Unseen &#183; 65 stands, thresholds fixed</p><p class="bigw" style="margin-top:6px;font-size:56px">0.79</p><p class="s ws" style="font-size:18px">per stand-year, 305 stand-years, incl. Saudi Tarut Bay</p></div>
    <div class="card" style="padding:18px 24px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:#7C4DFF">EnMAP hyperspectral &#183; same dates</p><p class="big" style="margin-top:6px;font-size:50px">r = 0.84&#8211;0.99</p><p class="s" style="font-size:18px">vs our Sentinel-2 indices; stand-5 loss 62 ha vs our conservative 26 ha</p></div>
  </div>
</div>
<div class="card" style="margin-top:16px;padding:14px 26px;display:flex;gap:18px;align-items:center;border-left:6px solid {AMBER}">{icon("alert", 26, bg="linear-gradient(135deg,#FFB020,#FF8A00)")}
  <p class="t" style="font-size:20px"><b>What we do not claim:</b> advance warning, field verification, species discrimination, or that hyperspectral classifies better (F1 0.74 vs 0.72). We withdrew our own first test (58 % / 90 %) when we found it had no chance baseline.</p></div>""")

# ---- NEW: impact (carbon + business) ---------------------------------------------------------------------------------
kp = [("108 t C/ha", "field density near the stands (90 % CI 79&#8211;138), 82 % of it in the soil"), ("247 kt C", "pilot stock, 2,281 ha (range 180&#8211;316) &#8776; 907 kt CO&#8322;e"),
      ("2.8&#8211;6.7 kt C", "stock on the 26&#8211;62 ha lost at stand 5: what one alert puts on the table")]
tiers = [("Monitor", "$12k", "per site / yr", "alert, cell map, condition, carbon, monthly reports"), ("Evidence", "$25k", "per site / yr", "+ sub-metre check of every alert, audit pack"), ("Development watch", "$8k", "per project / yr", "for coastal developers and EIA consultants")]
S["impact"] = light("impact", 11, "Impact &amp; business viability", "Carbon at stake, and who pays to protect it", f"""
<div class="row" style="gap:22px">{"".join(f'<div class="card{" dk" if k == 2 else ""}" style="flex:1;padding:22px 28px"><p class="{"bigw" if k == 2 else "big"}" style="font-size:54px">{a}</p><p class="s{" ws" if k == 2 else ""}" style="margin-top:8px;font-size:20px">{b}</p></div>' for k, (a, b) in enumerate(kp))}</div>
<div class="row" style="gap:22px;margin-top:22px;flex:1">
  <div class="card" style="flex:1.3;padding:22px 28px;display:flex;flex-direction:column;gap:14px;justify-content:space-between"><p class="lab" style="color:{BLUE}">Service tiers (prices are pilot hypotheses)</p>
    <div class="row" style="gap:14px;flex:1">{"".join(f'<div style="flex:1;background:{ICE};border-radius:16px;padding:18px 20px;display:flex;flex-direction:column;justify-content:center"><p class="t b" style="font-size:22px">{a}</p><p class="big" style="font-size:50px;margin-top:8px">{b}</p><p class="s" style="font-size:17px">{c}</p><p class="t" style="font-size:19px;margin-top:12px">{d}</p></div>' for a, b, c, d in tiers)}</div>
    <p class="s" style="font-size:19px">Cost to serve &#8776; <b>$3.3k</b> / site / yr: compute &lt; $5 (measured), sub-metre checks on alerts $500&#8211;750, analyst $2k (assumption).</p>
    <p class="s" style="font-size:19px"><b>Customers:</b> agencies (EAD, MOCCAE, NCVC) &#183; planting programmes (ADNOC 10 M, Red Sea Global 50 M) &#183; carbon developers &#183; EIA consultants</p></div>
  <div class="col" style="flex:1;gap:16px">
    <div class="card" style="padding:24px 28px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{BLUE}">Competition</p><p class="t" style="margin-top:10px;font-size:22px">Global Mangrove Watch sends free monthly loss alerts (Gulf coverage not confirmed). We are complementary: tide-aware, calibrated, stand + cell, carbon and reports.</p></div>
    <div class="card dk" style="padding:24px 28px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:#8FD3FF">The honest market</p><p class="t w" style="margin-top:10px;font-size:23px">Gulf + Red Sea site subscriptions &#8776; $0.2&#8211;0.4 M / yr. The real prize: a <b>national MRV contract</b> or a monitoring layer on <b>gIQ</b>.</p>
      <div style="display:flex;gap:8px;margin-top:12px"><span class="pill">SDG 13</span><span class="pill">SDG 14</span><span class="pill">SDG 15</span></div></div>
  </div>
</div>""")

# ---- NEW: scalability + reproducibility (the two bonus criteria) -----------------------------------------------------
rep = [("file", "Public repository, MIT licence", "code, notebook, figures, data provenance and licences"),
       ("check", "Re-runs end to end in ~24 s", "notebook with outputs committed; pinned requirements; example input + output"),
       ("shield", "Clean-machine test passed", "fresh environment, same numbers, 0 errors"),
       ("search", "Every number traceable", "each figure on these slides comes from a script and a written summary"),
       ("map", "Live website + site reports", "anyone can open the monitor and check a stand")]
rp = "".join(f'<div style="display:flex;gap:16px;align-items:center">{icon(i, 26)}<div><p class="t b" style="font-size:22px">{a}</p><p class="s" style="font-size:18px">{b}</p></div></div>' for i, a, b in rep)
ph = [("check", "Proven now", ["91 stands, 2 countries, 2 Sentinel-2 tiles", "65 unseen stands: 0.79 false alarms / stand-yr", "compute &lt; $5 per site per year", "backfill: 22&#8211;73 min per block"]),
      ("flag", "Incubation", ["Satellite 813 in the spectral step", "deployment on gIQ", "a pilot customer + site records", "more EnMAP dates per season"]),
      ("target", "Scale", ["Gulf &#8776; 165 km&#178; + Red Sea &#8776; 200 km&#178; of mangrove", "sub-metre data for small stands (Bahrain)", "national MRV &#183; platform licensing"])]
phc = "".join(f'<div class="card{" dk" if k == 0 else ""}" style="padding:18px 26px;flex:1;display:flex;flex-direction:column;justify-content:center"><div style="display:flex;gap:14px;align-items:center">{icon(i, 26)}<p class="t b" style="font-size:24px{";color:#fff" if k == 0 else ""}">{a}</p></div>'
              f'<p class="s{" ws" if k == 0 else ""}" style="margin-top:10px;font-size:21px">{" &#183; ".join(items)}</p></div>' for k, (i, a, items) in enumerate(ph))
S["scale"] = light("scale", 12, "Bonus criteria &#183; beyond the proof of concept", "Reproducible today, built to scale tomorrow", f"""
<div class="row" style="gap:28px;flex:1">
  <div class="card" style="flex:1;padding:24px 30px;display:flex;flex-direction:column;gap:16px;justify-content:space-between"><p class="lab" style="color:{BLUE}">Bonus &#183; documentation, evidence &amp; reproducibility</p>{rp}
    <p class="mono" style="font-size:17px;color:{BLUE}">github.com/Nahla-Nabil/blue-carbon-guardian</p></div>
  <div class="col" style="flex:1.15;gap:16px"><p class="lab" style="color:{BLUE}">Bonus &#183; scalability beyond the PoC</p>{phc}</div>
</div>
<p class="s" style="font-size:16px;margin-top:12px">Mangrove areas: Frontiers in Marine Science 2025 (doi:10.3389/fmars.2025.1695426). Compute measured on our runs; prices and analyst time are assumptions.</p>""")


# ---- NEW: how we differ (comparison with what exists today; same rows as the README table) ----------------------------
_rows = [("How often", "campaigns", "yearly or less", "monthly", "every ~5 days"), ("Corrects for the tide", "n/a", "not usually", "not documented", "&#10003; tide model"),
         ("Says where inside a stand", "&#10003;", "&#8212;", "&#8212;", "&#10003; 200 m cells"), ("Published false-alarm rate", "n/a", "n/a", "accuracy only", "&#10003; &#8776; 1 per stand-year"),
         ("Carbon at stake per alert", "&#8212;", "&#8212;", "&#8212;", "&#10003; field-based"), ("Gulf coverage", "&#10003;", "&#10003;", "not confirmed", "&#10003; Abu Dhabi + Tarut Bay")]
_th = "".join(f'<th style="font-size:20px;color:{NAVY if k < 4 else "#fff"};background:{ICE if k < 4 else BLUE}">{h}</th>' for k, h in enumerate(["", "Field surveys", "One-off satellite maps", "Global Mangrove Watch alerts", "Blue Carbon Guardian"]))
_tr = "".join("<tr>" + "".join(f'<td style="font-size:21px;{"font-weight:700;" if k in (0, 4) else ""}{"background:#E8F2FF;color:#06235A" if k == 4 else ""}">{c}</td>' for k, c in enumerate(r)) + "</tr>" for r in _rows)
S["different"] = light("different", 9, "Innovation &amp; differentiation", "How we differ from what exists today", f"""
<div class="card" style="padding:10px 14px"><table><tr>{_th}</tr>{_tr}</table></div>
<div class="card dk" style="margin-top:22px;padding:20px 30px"><p class="t w" style="font-size:24px"><b>Complementary, not competing:</b> Global Mangrove Watch flags loss worldwide; we add the tide model, the 200 m cells, a measured false-alarm rate and the carbon at stake &#8212; built and tested for the Gulf.</p></div>""")


# ---- NEW: how a user receives it (README sequence diagram) -------------------------------------------------------------
S["sequence"] = light("sequence", 8, "Delivery &#183; how a user receives it", "One alert, one message, one targeted visit", f"""
<div class="row" style="gap:26px;flex:1"><div class="card" style="flex:1.6;padding:18px;background:#0B1B30;display:flex;align-items:center"><img src="images/diagram_sequence.png" style="width:100%"></div>
<div class="col" style="flex:1;gap:16px">{"".join(f'<div class="card" style="flex:1;padding:18px 22px"><p class="t b">{a}</p><p class="s" style="margin-top:6px">{b}</p></div>' for a, b in [("Every ~5 days", "a new Sentinel-2 scene runs through the tide-aware model, per stand and per 200 m cell"), ("If an alert fires", "sub-metre check of the flagged cells, then an email or JSON alert with the cell map and the carbon at stake"), ("If nothing changes", "a monthly site report: condition, trend and carbon stock")])}</div></div>""")

# ---- NEW: close ------------------------------------------------------------------------------------------------------
S["close"] = dark("close", f"""
  <div style="position:absolute;left:110px;top:190px;width:1700px">
    <p class="mono" style="font-size:22px;letter-spacing:4px;color:#8FD3FF;font-weight:600">TEAM BLUE ATHAR &#183; <span style="font-family:'IBM Plex Sans Arabic',sans-serif;letter-spacing:0;word-spacing:8px;font-size:26px">&#1575;&#1604;&#1571;&#1579;&#1585;&nbsp;&#1575;&#1604;&#1571;&#1586;&#1585;&#1602;</span></p>
    <h2 style="font-size:84px;font-weight:700;line-height:1.08;margin-top:24px;background:linear-gradient(90deg,#FFFFFF,#CBEBFF 60%,#7FD3FF);-webkit-background-clip:text;color:transparent">Every lost mangrove leaves a trace.<br>We find it from space.</h2>
    <div style="display:flex;gap:26px;margin-top:56px">
      {"".join(f'<div style="flex:1;padding:26px 30px;border-radius:22px;background:linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.04));border:1px solid rgba(169,228,255,.35)"><p class="bigw" style="font-size:46px">{a}</p><p style="font-size:21px;color:#D8EEFF;margin-top:10px">{b}</p></div>' for a, b in [("Tide-aware", "29&#8211;35 % less noise"), ("5 of 5", "real conversions alerted during the works, 3 only by cells"), ("0.79", "false alarms / stand-yr on unseen stands"), ("Open", "public code, re-runs in ~24 s")])}
    </div>
    <div style="margin-top:44px;padding:24px 32px;border-radius:22px;background:linear-gradient(135deg,rgba(14,165,233,.35),rgba(30,111,217,.25));border:1px solid rgba(169,228,255,.45)">
      <p style="font-size:26px;color:#fff;line-height:1.45"><b>Our ask:</b> incubation to run a pilot with a Gulf agency or planting programme, mentor access on hyperspectral reading of mangroves, and Satellite 813 scenes when available.</p></div>
    <p class="mono" style="font-size:22px;color:#BFDFFF;margin-top:36px">nahla-nabil.github.io/blue-carbon-guardian &#183; github.com/Nahla-Nabil/blue-carbon-guardian &#183; Thank you</p>
  </div>""")

# ---- timed speaker script (replaces the PoC notes) -------------------------------------------------------------------
SCRIPT = {
 "cover": (15, """SAY (calm, slow): "Good morning. I'm Nahla Nabil, team Blue Athar.
What you are watching is a satellite pass over 25 mangrove stands in Abu Dhabi.
The five in red were lost to construction between 2022 and 2025 — and our system raised an alert on every one of them while the works were happening.
This is Blue Carbon Guardian."

DO: let the scan run for one sweep, then press → .
BEFORE YOU START: PowerPoint in Slide Show (Presenter View); browser already open on nahla-nabil.github.io/blue-carbon-guardian/#monitor (page loaded, zoom 100 %); notifications off."""),

 "problem": (40, """SAY: "The Gulf is planting mangroves at record scale: 100 million pledged by the UAE, more than 100 million by Saudi Arabia. In February the first GCC mangrove monitoring guide was published.
But planting is scaling faster than watching. Look at stand 5." (point at the images, left to right)
"November 2021: intact. October 2022: works start — and that is when our alert fired. 2023: canals. Today: a canal development.
Today, a loss like this is found at the next field survey — after the fact. What we solve: a calibrated alert every five days that says where to inspect, and what carbon is at stake."

DO: press → after "at stake"."""),

 "product": (75, """SAY: "So here is what we built. Let me show you — live."

DO: Alt+Tab to the browser (monitor section).
SAY: "Every stand is coloured by its condition. Stand 5, in red: severe decline."

DO: click "200 m cells" above the map.
SAY: "Now the key idea: we split every stand into 200-metre cells."

DO: scroll down to the table → click the row "9" → scroll back up to the map.
SAY: "Stand 9. On average it reads 'stable'. But 8 of its 28 cells are in severe decline. That is exactly where you send the inspector."

DO: move the mouse over the alert-score chart.
SAY: "Blue is the stand average, red is the worst single cell. The red line plunges far below its threshold — the cells see the damage much more sharply than the average does."

DO (only if ahead of time): click "Open the site report" → new tab → 3 seconds → Ctrl+W.
SAY: "And every stand gets a one-page report with the carbon at stake."

DO: Alt+Tab back to PowerPoint → press → .
FALLBACK: if the site does not load, stay on this slide — the recording plays the same steps; narrate it with the same lines."""),

 "usecase": (15, """SAY: "Three users, three decisions.
Agencies: which stands do we inspect this month. Planting and carbon developers: is the carbon we report still there. Developers and regulators: did the works stay outside the mangrove line."

DO: press → ."""),

 "data": (15, """SAY: "The analysis rests on five independent data sources: 778 Sentinel-2 dates over six years, EnMAP hyperspectral, ESA WorldCover, field carbon plots, and dated sub-metre imagery.
Every image is cloud-masked, only interior pixels are used, and every finding is cross-checked by a second source."

DO: press → ."""),

 "solution": (20, """SAY: "Here is the whole method, left to right.
We cut every stand into 200-metre cells and read every Sentinel-2 date. The tide-aware model — in blue — predicts what each stand and each cell should look like.
If reality falls too far below, the alert rule — in rose — fires. The decision layer — in sand — adds the cell map and the carbon at stake, with EnMAP and sub-metre imagery as independent checks."

DO: point along the boxes as you speak, then press → ."""),
 "sequence": (20, """SAY: "And this is what the user experiences.
Every five days a new scene runs through the model. If an alert fires, we first check the flagged cells on sub-metre imagery, then send the alert with the cell map and the carbon at stake — and the inspector visits only those cells.
If nothing changes, the user still gets a monthly report. No dashboards to watch: the system comes to them."

DO: press → ."""),
 "innovation": (45, """SAY: "Now the hard part — the one that breaks most monitors in the Gulf: the tide.
When the tide comes in, flooded mangroves look, from space, like dying mangroves. In this illustration the same trees drop from 0.30 to 0.18.
On our stands, index noise follows wetness with a correlation of minus 0.9.
So for every stand and every date we model trend, season — and the tide.
Noise falls by 29 to 35 percent on every index." (point at the right card at the bottom)
"And we tested the textbook recipe — NDVI alone, no tide model — on the same stands with the same alert rule: 1.61 false alarms per stand per year. Ours: 0.96. Forty percent fewer wasted site visits, and the tide model is most of that gain. That is what makes a reliable alert possible."

DO: wait for the water to rise in the illustration, then press → on "reliable alert"."""),

 "cells": (25, """SAY: "Our second innovation: averages hide damage.
Real data from stand 5: watch the cells turn red while the stand average barely moves. Three of our five real conversions were found only by the cells.
In simulation, a partial loss is caught within 60 days 73 percent of the time — against 13 percent by chance."

DO: press → ."""),

 "validation-real": (35, """SAY: "Does it work on real events? Five real conversions, all confirmed on 30-to-50-centimetre imagery.
The blue bar is the window between the last intact image and the first image showing works; the diamond is when our alert started. Every alert falls inside that window." (point at stand 5's diamond)
"This is detection while the works happen — not a prediction. We never claim advance warning."

DO: press → ."""),

 "validation": (35, """SAY: "We also tested ourselves against pure chance — every rate has its chance rate next to it.
Partial loss: 73 percent caught, 13 by chance. A uniform 10-percent loss is harder: 63 versus 36, and we show that too.
On 65 stands the model never saw, thresholds frozen, false alarms stayed at 0.79 per stand-year.
And when we found a flaw in our own first test, we withdrew it. These are the numbers that survived."

DO: press → on "survived"."""),

 "impact": (30, """SAY: "Why it matters. 108 tonnes of carbon per hectare in these stands — 82 percent in the soil, released when the stand is cleared. The pilot holds about 247 thousand tonnes; stand 5 alone lost 3 to 7 thousand.
As a service: about 12 thousand dollars per site per year, against a cost to serve of about 3 thousand. The real prize is a national MRV contract, or a monitoring layer on gIQ."

DO: press → ."""),

 "scale": (20, """SAY: "Beyond the proof of concept: everything is public and reproducible — the notebook re-runs in 24 seconds, and a clean-machine test gives the same numbers.
It already transferred to unseen stands and a second country, at under five dollars of compute per site per year. Next: Satellite 813, gIQ, and a pilot customer."

DO: press → ."""),

 "team": (30, """SAY: "Before the problem — who is behind this. A team of one. I held every role on this slide — satellite pipeline, statistics, product and business case.
I'm finishing a BSc in Artificial Intelligence at the Arab Open University in Bahrain, with First-Class Honours standing; I have two IEEE papers in machine learning, and I lead NASA Space Apps locally. I worked with an AI-assisted engineering workflow that I direct and review — and every number is public and checkable.
In incubation I will add what I don't have: a mangrove ecologist and a field partner."

DO: press → ."""),

 "hyperspectral": (20, """SAY: "Here is the second source at work: EnMAP hyperspectral, 224 bands.
On stand 5, the green curves are the vegetation in 2022; the red dashed curves are the same pixels in 2025 — the spectrum of sand and fill. That is reclamation, not dieback.
On the same dates, EnMAP agrees with our Sentinel-2 indices with r up to 0.99."

DO: press → ."""),
 "different": (25, """SAY: "So how is this different from what exists?
Field surveys are periodic. Satellite maps are one-off. Global Mangrove Watch sends free monthly loss alerts — and we see it as complementary.
What we add" (point down the blue column) ": every five days, the tide removed, where inside the stand, a measured false-alarm rate, and the carbon at stake — built and tested for the Gulf."

DO: press → ."""),
 "close": (15, """SAY (slow, look at the camera): "A working product, five real events confirmed, every number reproducible.
Every lost mangrove leaves a trace — and we find it from space.
Our ask: incubation, to run a pilot with a Gulf agency or planting programme. Thank you — I'm happy to take your questions."

DO: stop talking; stay on this slide during the Q&A. If asked to see the product again: last slide (backup video) or Alt+Tab to the website."""),
}
assert set(SCRIPT) == set(ORDER)

for n, sid in enumerate(ORDER, 1):
    html = S[sid]
    html = re.sub(r">\d{2} / 16</p>", f">{n:02d} / {TOTAL}</p>", html)
    secs, text = SCRIPT[sid]
    note = f"<aside>[{secs} s] {text}</aside>"
    html = re.sub(r"<aside>.*?</aside>", note, html, flags=re.S) if "<aside>" in html else html.replace("</section>", f"  {note}\n</section>")
    (SL / f"{sid}.html").write_text(html, encoding="utf-8")

deck = json.load(open(ROOT / "deck_source" / "deck.json", encoding="utf-8"))
deck.update(title="Blue Carbon Guardian - final", order=ORDER, sections={})
json.dump(deck, open(OUT / "deck.json", "w", encoding="utf-8"), indent=2)

total = sum(s for s, _ in SCRIPT.values())
md = [f"# Pitch script - final judging (8 min pitch + 4 min Q&A)\n\nGenerated by scripts/deck_final.py. Total planned: {total // 60} min {total % 60:02d} s (slack inside 8 min). PowerPoint: docs/Blue_Carbon_Guardian_final.pptx (same text in its speaker notes).\n\nSAY = say it word for word. DO = what to click or open.\n"]
t = 0
for n, sid in enumerate(ORDER, 1):
    secs, text = SCRIPT[sid]
    md.append(f"## {n}. {sid}  ({t // 60}:{t % 60:02d} - {(t + secs) // 60}:{(t + secs) % 60:02d}, {secs} s)\n\n{text}\n")
    t += secs
(ROOT / "docs" / "pitch_script.md").write_text("\n".join(md), encoding="utf-8")
BACKUP_NOTE = ("BACKUP - only if a judge asks to see the product again, or the live demo failed.\n\n"
               "DO: click the video to play it (sound on, 2 min). Press Esc to leave the slideshow afterwards.\n"
               "SAY: \"Here is the two-minute walkthrough of the product.\"")
json.dump({**{k: f"TIME: {t} s\n\n{x}" for k, (t, x) in SCRIPT.items()}, "backup": BACKUP_NOTE}, open(ROOT / "deck_pptx" / "notes.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)  # speaker notes for the PowerPoint
print(f"wrote {TOTAL} slides to {OUT.relative_to(ROOT)}; script {total} s")
