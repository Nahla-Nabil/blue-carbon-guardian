"""Build the public website docs/index.html (served by GitHub Pages from /docs): landing page + interactive monitor + validation story.
Data: analysis/data/site_data.json (written by analysis/09_build_dashboard.py). Images: docs/assets/. Site reports: docs/reports/ (copies of reports/).
Every number on the page is one already approved in README section 8. Run from the repository root:
    python analysis/09_build_dashboard.py && python scripts/build_site.py
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.load(open(ROOT / "analysis/data/site_data.json"))
for s in data["series"].values():          # keep the page light: 3 decimals
    for k in ("ndvi", "ndmi", "z", "zc"):
        if k in s: s[k] = [None if v is None else round(v, 3) for v in s[k]]
REPORTS = sorted(int(p.stem.split("_")[1]) for p in (ROOT / "docs/reports").glob("stand_*_report.html"))

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blue Carbon Guardian</title>
<meta name="description" content="Tide-aware satellite monitoring for Gulf mangroves: alerts per stand and per 200 m cell, carbon at stake, validated on real events.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans+Arabic:wght@600&display=swap" rel="stylesheet">
<style>
:root{--navy:#06235A;--deep:#030B26;--blue:#1E6FD9;--sky:#2F80ED;--cyan:#0EA5E9;--ice:#E8F2FF;--mist:#F4F8FF;--line:#D6E6FF;--ink:#0B1B3F;--muted:#4A5F86;--coral:#FF4D6D;--amber:#FFB020;--green:#2E9E6B}
*{box-sizing:border-box;margin:0}
html{scroll-behavior:smooth}
body{font-family:'IBM Plex Sans',system-ui,sans-serif;color:var(--ink);background:#fff;line-height:1.55}
a{color:var(--blue);text-decoration:none}
.mono{font-family:'IBM Plex Mono',monospace}
.wrap{max-width:1200px;margin:0 auto;padding:0 24px}
.k{font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:3px;text-transform:uppercase;color:var(--blue);font-weight:600}
h2{font-size:clamp(28px,4vw,42px);line-height:1.15;color:var(--navy);margin:8px 0 12px}
.lede{font-size:18px;color:var(--muted);max-width:760px}
section{padding:84px 0}
.alt{background:linear-gradient(180deg,#F4F8FF,#FFFFFF)}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 30px rgba(10,61,145,.07);padding:22px}
.dark{background:linear-gradient(135deg,#06235A,#0B4A9E);color:#fff;border:none}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.big{font-size:40px;font-weight:700;line-height:1.05;background:linear-gradient(90deg,#0A3D91,#1E6FD9 60%,#0EA5E9);-webkit-background-clip:text;background-clip:text;color:transparent}
.pill{display:inline-block;padding:4px 12px;border-radius:999px;font-size:13px;font-weight:600;background:var(--ice);color:#0A3D91;border:1px solid #C3DDFF}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 20px;border-radius:12px;font-weight:600;font-size:15px}
.btn.p{background:#fff;color:var(--navy)} .btn.s{background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.4)}
/* nav */
nav{position:sticky;top:0;z-index:50;background:rgba(3,11,38,.88);backdrop-filter:blur(10px);border-bottom:1px solid rgba(169,228,255,.15)}
nav .wrap{display:flex;align-items:center;gap:22px;height:60px}
nav .brand{color:#fff;font-weight:700;display:flex;align-items:center;gap:10px;margin-right:auto;white-space:nowrap}
nav a.l{color:#BFDFFF;font-size:14px;white-space:nowrap} nav a.l:hover{color:#fff}
/* hero */
.hero{background:radial-gradient(900px 520px at 80% 20%,rgba(76,169,255,.32),transparent 70%),linear-gradient(120deg,#030B26 0%,#06235A 40%,#0B4A9E 75%,#1477D6 100%);color:#fff;padding:80px 0 70px;position:relative;overflow:hidden}
.hero:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:56px 56px}
.hero .wrap{position:relative;display:grid;grid-template-columns:1.15fr .85fr;gap:40px;align-items:center}
.hero h1{font-size:clamp(38px,4.6vw,60px);white-space:nowrap;line-height:1.02;background:linear-gradient(90deg,#fff,#CBEBFF 60%,#7FD3FF);-webkit-background-clip:text;background-clip:text;color:transparent;margin:14px 0}
.hero p.sub{font-size:20px;color:#D8EEFF;max-width:620px}
.hero .tags{margin:18px 0 26px;display:flex;flex-wrap:wrap;gap:8px}
.hero .tags>span{padding:5px 13px;border-radius:999px;font-size:14px;background:rgba(108,199,255,.14);border:1px solid rgba(108,199,255,.4);color:#D8EEFF}
.hero .ctas{display:flex;flex-wrap:wrap;gap:12px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:44px;position:relative}
.kpi{padding:16px 18px;border-radius:16px;background:linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.05));border:1px solid rgba(169,228,255,.35)}
.kpi b{display:block;font-size:30px;line-height:1.1;background:linear-gradient(90deg,#fff,#A9E4FF);-webkit-background-clip:text;background-clip:text;color:transparent}
.kpi span{font-size:14px;color:#BFDFFF}
.heroimg{border-radius:18px;overflow:hidden;border:1px solid rgba(169,228,255,.35);box-shadow:0 30px 70px rgba(0,0,0,.35)}
.heroimg img{display:block;width:100%}
/* monitor */
.mon{display:grid;grid-template-columns:1.1fr .9fr;gap:20px;margin-top:28px}
.maptools{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.seg{display:inline-flex;background:var(--ice);border-radius:10px;padding:3px}
.seg button{border:0;background:transparent;padding:7px 14px;border-radius:8px;font:600 13px 'IBM Plex Sans';color:#0A3D91;cursor:pointer}
.seg button.on{background:#fff;box-shadow:0 2px 8px rgba(10,61,145,.15)}
#map{width:100%;height:auto;display:block;background:linear-gradient(180deg,#EEF5FF,#F8FBFF);border-radius:14px}
#map path{cursor:pointer;transition:opacity .15s} #map path:hover{opacity:.75}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--muted);margin-top:10px}
.sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.det h3{font-size:26px;color:var(--navy)}
.badge{display:inline-block;padding:4px 12px;border-radius:999px;font-size:13px;font-weight:700;color:#fff}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:14px 0}
.stat{background:var(--mist);border-radius:12px;padding:10px 12px}.stat b{display:block;font-size:20px;color:var(--navy)}.stat span{font-size:12.5px;color:var(--muted)}
.chart{width:100%;height:auto;display:block}
.note{font-size:13px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:14px}
th{background:var(--navy);color:#fff;text-align:left;padding:9px 10px;font-weight:600;cursor:pointer;white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid var(--line)} tbody tr{cursor:pointer} tbody tr:hover td{background:var(--mist)} tr.sel td{background:#E1EEFF}
.tablewrap{max-height:360px;overflow:auto;border-radius:14px;border:1px solid var(--line);margin-top:20px}
/* steps */
.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-top:28px}
.step{position:relative}.step .n{font-family:'IBM Plex Mono';font-size:13px;color:var(--cyan);font-weight:600}
.step h4{font-size:18px;color:var(--navy);margin:6px 0}.step p{font-size:14px;color:var(--muted)}
.bar{height:16px;border-radius:6px}
.events{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:28px}
.ev img{width:100%;height:260px;object-fit:contain;border-radius:12px;display:block;background:var(--mist)}
.ev h4{font-size:18px;color:var(--navy);margin:12px 0 4px}
.cmp{display:grid;grid-template-columns:260px 1fr;gap:10px 18px;align-items:center;margin-top:12px}
.price b{font-size:34px;color:var(--navy)}
footer{background:#030B26;color:#BFDFFF;padding:44px 0;font-size:14px}
footer a{color:#fff}
@media(max-width:900px){.hero h1{white-space:normal}.hero .wrap,.mon,.grid2,.grid3,.events{grid-template-columns:1fr}.kpis,.grid4{grid-template-columns:1fr 1fr}.steps{grid-template-columns:1fr}nav a.l{display:none}nav a.l.keep{display:inline}.cmp{grid-template-columns:1fr}}
</style></head>
<body>
<nav><div class="wrap">
  <a class="brand" href="#top"><svg width="26" height="26" viewBox="0 0 240 240"><circle cx="120" cy="120" r="104" fill="none" stroke="#7FD3FF" stroke-width="14"/><path d="M120 52 C 160 80 168 128 120 170 C 72 128 80 80 120 52 Z" fill="none" stroke="#fff" stroke-width="14"/></svg>Blue Carbon Guardian</a>
  <a class="l keep" href="#monitor">Monitor</a><a class="l" href="#how">How it works</a><a class="l" href="#events">Real events</a><a class="l" href="#validation">Validation</a><a class="l" href="#carbon">Carbon</a><a class="l" href="#offer">Offer</a>
  <a class="l keep" href="https://github.com/Nahla-Nabil/blue-carbon-guardian">GitHub ↗</a>
</div></nav>

<header class="hero" id="top"><div class="wrap">
  <div>
    <div class="mono" style="font-size:13px;letter-spacing:3px;color:#8FD3FF">ARAB YOUTH SPACE HACKATHON 2026 · CHALLENGE 813</div>
    <h1>Blue Carbon Guardian</h1>
    <p class="sub">Tide-aware satellite monitoring for Gulf mangroves. We flag losses stand by stand and in 200&nbsp;m cells, show where to inspect, and report the carbon at stake.</p>
    <div class="tags"><span style="background:rgba(255,255,255,.16);color:#fff;font-weight:600">Team Blue Athar · <span style="font-family:'IBM Plex Sans Arabic'">الأثر الأزرق</span></span><span>Ecosystem Health &amp; Blue Carbon</span><span>by Nahla Nabil</span></div>
    <div class="ctas"><a class="btn p" href="#monitor">Open the monitor →</a><a class="btn s" href="https://github.com/Nahla-Nabil/blue-carbon-guardian#-demo-video-214--english-narration-arabic-subtitles">▶ Demo video</a><a class="btn s" href="slides.pdf">Slides (PDF)</a></div>
  </div>
  <div class="heroimg"><img src="assets/alert_story.gif" alt="Real data, stand 5: Sentinel-2 images, 200 m cells turning red, and the alert score crossing its threshold"></div>
  <div class="kpis" style="grid-column:1/-1">
    <div class="kpi"><b>−29 to −35 %</b><span>index noise after the tide model</span></div>
    <div class="kpi"><b>5 confirmed</b><span>real mangrove conversions, on 0.3–0.5 m imagery</span></div>
    <div class="kpi"><b>73 % vs 13 %</b><span>partial loss caught within 60 days, vs chance</span></div>
    <div class="kpi"><b>≈ 247 kt C</b><span>carbon stock in the pilot area</span></div>
  </div>
</div></header>

<section id="monitor"><div class="wrap">
  <div class="k">Live product · Abu Dhabi pilot</div>
  <h2>The monitor</h2>
  <p class="lede">25 mangrove stands (2,281 ha), Sentinel-2 from 2020 to <span id="lastobs"></span>. Click a stand on the map or in the table. Switch to <b>200 m cells</b> to see where inside a stand the change is.</p>
  <div class="mon">
    <div class="card">
      <div class="maptools"><div class="seg"><button id="bStands" class="on">Stands</button><button id="bCells">200 m cells</button></div>
        <span class="note">Colour = condition, last 12 months vs 2020–21</span></div>
      <svg id="map"></svg>
      <div class="legend"><span><i class="sw" style="background:#7FB6F5"></i>stable</span><span><i class="sw" style="background:#2E9E6B"></i>improving</span><span><i class="sw" style="background:#FFB020"></i>decline</span><span><i class="sw" style="background:#FF4D6D"></i>severe decline</span><span><i class="sw" style="background:#fff;border:2px solid #7C4DFF"></i>alert active</span></div>
      <div style="margin-top:16px;background:var(--mist);border-radius:12px;padding:14px 16px;font-size:14px"><b style="color:var(--navy)">How to read it</b>
        <p style="margin-top:6px"><b>Alert</b> = a recent drop below what tide, season and trend predict (combined stand + cell rule). <b>Condition</b> = the last 12 months against the stand's own 2020–21 baseline. A red cell inside a blue stand means: the stand is fine on average, inspect that part.</p></div>
    </div>
    <div class="card det" id="det"></div>
  </div>
  <div class="tablewrap"><table id="tbl"><thead><tr><th data-k="stand">Stand</th><th data-k="area_ha">Area (ha)</th><th data-k="condition">Condition</th><th data-k="ndvi_change_pct">NDVI change</th><th data-k="cells_bad">Cells in decline</th><th data-k="alerts_2022_2026">Alert episodes 2022–26</th><th data-k="stock_tC_p50">Carbon (kt C)</th></tr></thead><tbody></tbody></table></div>
  <p class="note" style="margin-top:10px">Alert rule: stand average ≤ −1.5σ OR any 200 m cell ≤ −3.5σ (about one false-alarm episode per stand-year). Condition and alert are screening results, not field verification. Contains modified Copernicus Sentinel data 2020–2026.</p>
</div></section>

<section class="alt" id="how"><div class="wrap">
  <div class="k">How it works</div>
  <h2>From satellite pixels to an inspection decision</h2>
  <p class="lede">On Gulf tidal flats the tide, not the trees, drives most of the change in a satellite index. A naive monitor raises a false alarm at every high tide. We model the tide out first.</p>
  <div class="steps">
    <div class="card step"><div class="n">01</div><h4>Stands &amp; cells</h4><p>WorldCover 2021 mangrove patches ≥ 3 ha, cut into 200 m cells; interior pixels only.</p></div>
    <div class="card step"><div class="n">02</div><h4>Sentinel-2 series</h4><p>778 dates 2020–26, read in place from the cloud; NDVI, red edge, SWIR moisture, wetness.</p></div>
    <div class="card step"><div class="n">03</div><h4>Tide-aware model</h4><p>Robust trend + season + tide terms per stand and cell, refitted every month.</p></div>
    <div class="card step"><div class="n">04</div><h4>Alert &amp; condition</h4><p>Stand ≤ −1.5σ OR any cell ≤ −3.5σ; condition = last 12 months vs 2020–21.</p></div>
    <div class="card step dark"><div class="n" style="color:#8FD3FF">05</div><h4 style="color:#fff">Decision</h4><p style="color:#BFDFFF">Cell map, carbon at stake, dashboard, site reports, alert API (concept).</p></div>
  </div>
  <div class="grid2" style="margin-top:22px">
    <div class="card"><h4 style="color:var(--navy)">Noise removed by the tide model</h4><p class="note">Robust residual noise, 25 stands, 2020–2026</p><div id="noise"></div></div>
    <div class="card"><h4 style="color:var(--navy)">Why cells matter</h4><p style="margin-top:8px">A stand average hides a partial loss. Stand 9 reads <b>“stable”</b> on average while <b>8 of its 28 cells</b> are in severe decline. <b>3 of the 5</b> real conversions were found <b>only</b> at cell level (stands 12, 18 and 6).</p>
      <div class="cmp" style="grid-template-columns:170px 1fr"><span class="note">stand + cells</span><div><div class="bar" style="width:73%;background:linear-gradient(90deg,#0A3D91,#0EA5E9)"></div><b>73 %</b></div>
      <span class="note">stand average alone</span><div><div class="bar" style="width:25%;background:#7FB6F5"></div><b>25 %</b></div>
      <span class="note">by chance</span><div><div class="bar" style="width:13%;background:#C9D3E3"></div><b>13 %</b></div></div>
      <p class="note" style="margin-top:6px">Partial loss caught within 60 days (simulated, ±7 points).</p></div>
  </div>
</div></section>

<section id="events"><div class="wrap">
  <div class="k">Validation 1 · real events</div>
  <h2>Five real conversions, confirmed on sub-metre imagery</h2>
  <p class="lede">All five are coastal developments (reclamation, canals, lagoons). Dated WorldView-2/3 and Legion-1 captures (0.3–0.5 m) confirm each one. At every site the alert began <b>between the last intact and the first disturbed capture</b>: detection of works as they happen, not advance warning.</p>
  <div class="card" style="margin-top:24px"><h4 style="color:var(--navy)">Stand 5 through time (Sentinel-2)</h4>
    <div class="grid4" style="margin-top:12px">
      <figure><img src="assets/site/s2_2021.jpg" style="width:100%;border-radius:10px" alt="Nov 2021"><figcaption class="note"><b>Nov 2021</b> · intact fringe</figcaption></figure>
      <figure><img src="assets/site/s2_2022.jpg" style="width:100%;border-radius:10px;outline:3px solid #FF4D6D" alt="Oct 2022"><figcaption class="note"><b style="color:#FF4D6D">Oct 2022</b> · works start, alert fires (25 Oct)</figcaption></figure>
      <figure><img src="assets/site/s2_2023.jpg" style="width:100%;border-radius:10px" alt="Jun 2023"><figcaption class="note"><b>Jun 2023</b> · canals cut</figcaption></figure>
      <figure><img src="assets/site/s2_2026.jpg" style="width:100%;border-radius:10px" alt="May 2026"><figcaption class="note"><b>May 2026</b> · development</figcaption></figure></div></div>
  <div class="events">
    <div class="card ev"><img src="assets/site/stand5.jpg" alt="Stand 5 before and after"><h4>Stand 5 · reclamation with finger canals</h4><p class="note">26–62 ha converted (Sentinel-2 and EnMAP estimates). Alert from 25 Oct 2022.</p></div>
    <div class="card ev"><img src="assets/site/stand9.jpg" alt="Stand 9 before and after"><h4>Stand 9 · canal development in the south-east</h4><p class="note">Average “stable”; 8 of 28 cells in severe decline. Alert from 7 Dec 2022.</p></div>
    <div class="card ev"><img src="assets/site/stand12.jpg" alt="Stand 12 key years"><h4>Stand 12 · found only by the cells</h4><p class="note">New canal and reclamation at the southern edge. Alert from 17 Dec 2022.</p></div>
    <div class="card ev"><img src="assets/site/stand18.jpg" alt="Stand 18 key years"><h4>Stand 18 · found only by the cells</h4><p class="note">The same development reaches it in 2025. Alert from 29 Oct 2024. (Stand 6, a fifth event, is in the gantt below.)</p></div>
  </div>
  <div class="card" style="margin-top:20px"><h4 style="color:var(--navy)">When did the alert start?</h4><p class="note">Bar = last intact capture → first capture with works. Diamond = start of our alert.</p><div id="gantt"></div></div>
</div></section>

<section class="alt" id="validation"><div class="wrap">
  <div class="k">Validation 2 &amp; 3 · against chance, unseen stands, hyperspectral</div>
  <h2>Every rate comes with its chance rate</h2>
  <p class="lede">We injected artificial loss into real stands with no known change, holding false alarms to about one per stand-year. A detection counts only if a <b>new</b> alert starts after the loss begins; the same test with <b>no</b> loss gives the chance rate.</p>
  <div class="grid2" style="margin-top:24px">
    <div class="card"><div id="sim"></div><p class="note" style="margin-top:8px">~160–240 trials per row (±7 points). We withdrew our own first figure (58 % / 90 %) after a null test showed its metric counted alerts that were already running.</p></div>
    <div style="display:grid;gap:16px">
      <div class="card"><div class="k" style="color:var(--muted)">Calibrated · 25 pilot stands</div><div class="big" style="margin-top:6px">0.96</div><p class="note">false-alarm episodes per stand-year (117 stand-years)</p></div>
      <div class="card dark"><div class="k" style="color:#8FD3FF">Unseen · 65 stands, thresholds fixed</div><div style="font-size:40px;font-weight:700;margin-top:6px">0.79</div><p style="color:#BFDFFF;font-size:14px">per stand-year over 305 stand-years, including Saudi Arabia's Tarut Bay</p></div>
    </div>
  </div>
  <div class="card" style="margin-top:20px"><div class="grid2" style="align-items:center">
    <img src="assets/site/enmap.jpg" style="width:100%;border-radius:10px" alt="EnMAP spectra of stand 5">
    <div><div class="k">Hyperspectral · EnMAP, 224 bands</div><h4 style="color:var(--navy);font-size:22px;margin:6px 0">An independent check, and a material fingerprint</h4>
      <p><b>r = 0.84–0.99</b> between EnMAP and our Sentinel-2 indices on the same dates. The converted part of stand 5 turns from a vegetation spectrum into a bright, mineral-like one: reclamation, not dieback. As a classifier, EnMAP did not beat multispectral bands (F1 0.74 vs 0.72), and we say so.</p>
      <p class="note" style="margin-top:6px">Contains modified EnMAP data © DLR 2022, 2025.</p></div></div></div>
</div></section>

<section id="carbon"><div class="wrap">
  <div class="k">Impact · carbon</div>
  <h2>Carbon stock, grounded in field measurements</h2>
  <div class="grid4" style="margin-top:24px">
    <div class="card"><div class="big">108</div><p class="note">t C/ha local mean density (90 % CI 79–138), 24 field plots at 4 sites</p></div>
    <div class="card"><div class="big">247 kt</div><p class="note">carbon in the pilot area, 2,281 ha (90 % range 180–316)</p></div>
    <div class="card"><div class="big">82 %</div><p class="note">of it is in the soil (89 of 108 t C/ha): losing a stand exposes what is underneath</p></div>
    <div class="card dark"><div style="font-size:40px;font-weight:700">2.8–6.7 kt</div><p style="color:#BFDFFF;font-size:14px">carbon stock on the 26–62 ha converted in stand 5</p></div>
  </div>
  <p class="note" style="margin-top:12px">Carbon is area × field density (Schile et al. 2016, CC0), a stock with a range, never a sequestration rate. We tested whether Sentinel-2 indices predict field tree carbon: too weak (best ρ = 0.38).</p>
</div></section>

<section class="alt" id="offer"><div class="wrap">
  <div class="k">Who it is for</div>
  <h2>A monitoring service with honest unit economics</h2>
  <div class="grid3" style="margin-top:24px">
    <div class="card"><div class="pill">Environment agencies</div><p style="margin-top:10px"><b>Decision:</b> which stands to inspect this month?</p><p class="note">Today: periodic field surveys, one-off studies.</p></div>
    <div class="card"><div class="pill">Planting &amp; carbon developers</div><p style="margin-top:10px"><b>Decision:</b> is the carbon stock we report still there?</p><p class="note">Today: field plots and drone surveys, campaign by campaign.</p></div>
    <div class="card"><div class="pill">Coastal developers &amp; regulators</div><p style="margin-top:10px"><b>Decision:</b> did construction stay outside the mangrove line?</p><p class="note">Today: comparing two dated images by eye.</p></div>
  </div>
  <div class="grid4" style="margin-top:18px">
    <div class="card dark price"><div class="k" style="color:#8FD3FF">Monitor</div><b style="color:#fff">$12k</b><p style="color:#BFDFFF;font-size:14px">per site / year: alert, cell map, condition, carbon, monthly reports</p></div>
    <div class="card price"><div class="k">Evidence</div><b>$25k</b><p class="note">per site / year: + sub-metre check of every alert, audit pack</p></div>
    <div class="card price"><div class="k">Development watch</div><b>$8k</b><p class="note">per construction project / year</p></div>
    <div class="card price"><div class="k">Cost to serve</div><b>≈ $3.3k</b><p class="note">per site / year (compute &lt; $5 measured)</p></div>
  </div>
  <p class="note" style="margin-top:10px">Prices are hypotheses for a pilot. Global Mangrove Watch offers free monthly loss alerts; we are complementary (tide-aware, calibrated, cell level, carbon and reports). Full plan: <a href="https://github.com/Nahla-Nabil/blue-carbon-guardian/blob/main/docs/business_plan_draft.md">business plan</a>.</p>
</div></section>

<section><div class="wrap">
  <div class="k">Limits, stated honestly</div>
  <h2>What we do not claim</h2>
  <div class="grid3" style="margin-top:20px">
    <div class="card"><b>Detection, not early warning.</b><p class="note">Alerts fire as works happen.</p></div>
    <div class="card"><b>10 m pixels.</b><p class="note">Patches under ~0.6 ha and young plantings are missed, Bahrain's small stands included.</p></div>
    <div class="card"><b>Imagery, not site visits.</b><p class="note">Matching alerts to permits with a partner is the first pilot task.</p></div>
  </div>
</div></section>

<footer><div class="wrap" style="display:flex;flex-wrap:wrap;gap:28px;justify-content:space-between">
  <div><b style="color:#fff;font-size:16px">Blue Carbon Guardian</b><br>Team Blue Athar · <span style="font-family:'IBM Plex Sans Arabic'">الأثر الأزرق</span> · Nahla Nabil<br>Arab Youth Space Hackathon 2026 · Challenge 813</div>
  <div><a href="https://github.com/Nahla-Nabil/blue-carbon-guardian">Code &amp; notebook (GitHub)</a><br><a href="slides.pdf">Slides (PDF)</a> · <a href="summary_ar.pdf">ملخص عربي</a><br><a href="https://github.com/Nahla-Nabil/blue-carbon-guardian/blob/main/docs/api_alert_concept.md">Alert API concept</a></div>
  <div style="max-width:430px;font-size:12.5px">Contains modified Copernicus Sentinel data 2020–2026 · Contains modified EnMAP data © DLR 2022, 2025 · ESA WorldCover 2021 (CC BY 4.0) · Schile et al. 2016 (CC0) · sub-metre captures viewed via Esri World Imagery Wayback (Esri, Maxar, Earthstar Geographics, and the GIS User Community). Code: MIT.</div>
</div></footer>

<script>
const D = __DATA__, REPORTS = __REPORTS__;
const COL = {"stable":"#7FB6F5","improving":"#2E9E6B","decline":"#FFB020","severe decline":"#FF4D6D"};
const NS = "http://www.w3.org/2000/svg";
const ST = {}; D.status.forEach(s => ST[s.stand] = s);
const CELLS = {}; D.cells.forEach(c => (CELLS[c.s] = CELLS[c.s] || []).push(c));
D.status.forEach(s => s.cells_bad = (CELLS[s.stand] || []).filter(c => c.cond !== "stable" && c.cond !== "improving").length);
document.getElementById("lastobs").textContent = new Date(D.kpi.last_obs).toLocaleDateString("en-GB", {month: "short", year: "numeric"});
// ---------- map ----------
let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
const rings = g => g.type === "Polygon" ? g.coordinates : g.coordinates.flat();
D.features.forEach(f => rings(f.geometry).forEach(r => r.forEach(([x, y]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); })));
const W = 1000, K = Math.cos(24.5 * Math.PI / 180), H = W * (y1 - y0) / ((x1 - x0) * K), P = 12;
const px = ([x, y]) => [P + (x - x0) / (x1 - x0) * (W - 2 * P), P + (y1 - y) / (y1 - y0) * (H - 2 * P)];
const pathD = g => rings(g).map(r => "M" + r.map(p => px(p).map(v => v.toFixed(1)).join(",")).join("L") + "Z").join("");
const map = document.getElementById("map"); map.setAttribute("viewBox", `0 0 ${W} ${H}`);
let mode = "stands", sel = 5;
function drawMap() {
  map.innerHTML = "";
  if (mode === "stands") D.features.forEach(f => { const s = ST[f.properties.stand], p = document.createElementNS(NS, "path");
    p.setAttribute("d", pathD(f.geometry)); p.setAttribute("fill", COL[s.condition] || "#7FB6F5"); p.setAttribute("fill-opacity", ".8");
    p.setAttribute("stroke", s.alert_now ? "#7C4DFF" : (s.stand === sel ? "#06235A" : "#fff")); p.setAttribute("stroke-width", s.alert_now || s.stand === sel ? 3 : 1);
    p.onclick = () => select(s.stand); const t = document.createElementNS(NS, "title"); t.textContent = `Stand ${s.stand} · ${s.condition}`; p.appendChild(t); map.appendChild(p); });
  else { D.features.forEach(f => { const p = document.createElementNS(NS, "path"); p.setAttribute("d", pathD(f.geometry)); p.setAttribute("fill", "#DCE8F8");
      p.setAttribute("stroke", f.properties.stand === sel ? "#06235A" : "#B9CDEA"); p.setAttribute("stroke-width", f.properties.stand === sel ? 2.5 : 1); p.onclick = () => select(f.properties.stand); map.appendChild(p); });
    D.cells.forEach(c => { const p = document.createElementNS(NS, "path"); p.setAttribute("d", pathD(c.g)); p.setAttribute("fill", COL[c.cond] || "#7FB6F5");
      p.setAttribute("stroke", "#fff"); p.setAttribute("stroke-width", .6); p.onclick = () => select(c.s);
      const t = document.createElementNS(NS, "title"); t.textContent = `Stand ${c.s} · cell ${c.c} · ${c.cond} · ${c.ha} ha`; p.appendChild(t); map.appendChild(p); }); }
}
document.getElementById("bStands").onclick = e => { mode = "stands"; e.target.classList.add("on"); document.getElementById("bCells").classList.remove("on"); drawMap(); };
document.getElementById("bCells").onclick = e => { mode = "cells"; e.target.classList.add("on"); document.getElementById("bStands").classList.remove("on"); drawMap(); };
// ---------- charts ----------
function lineChart(months, lines, opts) {
  const w = 560, h = 210, l = 40, r = 8, t = 10, b = 24, n = months.length;
  const lo = opts.lo, hi = opts.hi, X = i => l + i / (n - 1) * (w - l - r), Y = v => t + (hi - Math.max(lo, Math.min(hi, v))) / (hi - lo) * (h - t - b);
  let s = `<svg class="chart" viewBox="0 0 ${w} ${h}" font-family="IBM Plex Sans">`;
  (opts.bands || []).forEach(([a, c]) => { const i = months.indexOf(a), j = months.indexOf(c); if (i >= 0) s += `<rect x="${X(i)}" y="${t}" width="${Math.max(3, X(j >= 0 ? j : n - 1) - X(i))}" height="${h - t - b}" fill="rgba(255,77,109,.14)"/>`; });
  opts.ticks.forEach(v => s += `<line x1="${l}" x2="${w - r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#E6EEF9"/><text x="${l - 6}" y="${Y(v) + 4}" font-size="10" fill="#4A5F86" text-anchor="end">${v}${opts.unit || ""}</text>`);
  (opts.refs || []).forEach(([v, c, lab]) => s += `<line x1="${l}" x2="${w - r}" y1="${Y(v)}" y2="${Y(v)}" stroke="${c}" stroke-dasharray="5 4"/><text x="${w - r - 2}" y="${Y(v) - 4}" font-size="10" fill="${c}" text-anchor="end">${lab}</text>`);
  months.forEach((m, i) => { if (m.endsWith("-01")) s += `<text x="${X(i)}" y="${h - 6}" font-size="10" fill="#4A5F86" text-anchor="middle">${m.slice(0, 4)}</text>`; });
  lines.forEach(([vals, c, wd]) => { let d = "", pen = false; vals.forEach((v, i) => { if (v === null || v === undefined) { pen = false; return; } d += (pen ? "L" : "M") + X(i).toFixed(1) + "," + Y(v).toFixed(1); pen = true; });
    s += `<path d="${d}" fill="none" stroke="${c}" stroke-width="${wd}" stroke-linejoin="round"/>`; });
  return s + "</svg>";
}
function select(k) {
  sel = k; const s = ST[k], se = D.series[k], cells = CELLS[k] || [], bad = cells.filter(c => c.cond === "severe decline" || c.cond === "decline");
  const badHa = bad.reduce((a, c) => a + c.ha, 0), eps = D.episodes.filter(e => e.stand === k);
  const i0 = se.months.indexOf("2022-01"), m2 = se.months.slice(i0);
  const bands = eps.map(e => [e.start.slice(0, 7), e.end.slice(0, 7)]);
  const pct = v => (v > 0 ? "+" : "") + Math.round(v) + " %";
  document.getElementById("det").innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><h3>Stand ${k}</h3><span class="badge" style="background:${COL[s.condition]}">${s.condition}</span></div>
    <p class="note">${s.alert_now ? "<b style='color:#7C4DFF'>Alert active now.</b> " : "No active alert. "}${s.alerts_2022_2026} alert episodes 2022–26 (combined stand + cell rule).</p>
    <div class="stats"><div class="stat"><b>${s.area_ha.toFixed(1)} ha</b><span>stand area</span></div>
      <div class="stat"><b>${(s.stock_tC_p50 / 1000).toFixed(1)} kt C</b><span>carbon stock (${(s.stock_tC_p10 / 1000).toFixed(1)}–${(s.stock_tC_p90 / 1000).toFixed(1)})</span></div>
      <div class="stat"><b>${pct(s.ndvi_change_pct)}</b><span>NDVI, last 12 months vs 2020–21</span></div>
      <div class="stat"><b>${bad.length} of ${cells.length} cells</b><span>in decline${bad.length ? " · " + badHa.toFixed(1) + " ha to inspect" : ""}</span></div></div>
    <div class="k" style="font-size:11px">Alert score, 2022–2026</div>
    ${lineChart(m2, [[se.zc.slice(i0), "#FF6B85", 1.8], [se.z.slice(i0), "#1E6FD9", 2.4]], {lo: -12, hi: 4, ticks: [-12, -8, -4, 0, 4], unit: "σ", bands,
      refs: [[-1.5, "#1E6FD9", "stand −1.5σ"], [-3.5, "#FF4D6D", "cell −3.5σ"]]})}
    <p class="note"><span style="color:#1E6FD9">━</span> stand average &nbsp; <span style="color:#FF6B85">━</span> worst 200 m cell &nbsp; <span style="background:rgba(255,77,109,.2);padding:0 6px">alert</span></p>
    <div class="k" style="font-size:11px;margin-top:10px">Tide-corrected NDVI, monthly 2020–2026</div>
    ${lineChart(se.months, [[se.ndvi, "#2E9E6B", 2]], {lo: Math.min(...se.ndvi.filter(v => v !== null)) - .03, hi: Math.max(...se.ndvi.filter(v => v !== null)) + .03, ticks: [], })}
    ${REPORTS.includes(k) ? `<a class="btn" style="background:var(--navy);color:#fff;margin-top:10px" href="reports/stand_${String(k).padStart(2, "0")}_report.html" target="_blank">Open the site report →</a>` : `<p class="note" style="margin-top:8px">Printable site reports are generated for any stand (examples: stands ${REPORTS.join(", ")}).</p>`}`;
  drawMap(); document.querySelectorAll("#tbl tbody tr").forEach(tr => tr.classList.toggle("sel", +tr.dataset.k === k));
}
// ---------- table ----------
let sortK = "condition", asc = true; const ORD = {"severe decline": 0, "decline": 1, "stable": 2, "improving": 3};
function drawTable() {
  const rows = [...D.status].sort((a, b) => { const va = sortK === "condition" ? ORD[a.condition] : a[sortK], vb = sortK === "condition" ? ORD[b.condition] : b[sortK]; return (va > vb ? 1 : va < vb ? -1 : 0) * (asc ? 1 : -1); });
  document.querySelector("#tbl tbody").innerHTML = rows.map(s => `<tr data-k="${s.stand}"><td><b>${s.stand}</b></td><td>${s.area_ha.toFixed(1)}</td><td><span class="badge" style="background:${COL[s.condition]};font-size:11px">${s.condition}</span></td><td>${Math.round(s.ndvi_change_pct)} %</td><td>${s.cells_bad} / ${(CELLS[s.stand] || []).length}</td><td>${s.alerts_2022_2026}</td><td>${(s.stock_tC_p50 / 1000).toFixed(1)}</td></tr>`).join("");
  document.querySelectorAll("#tbl tbody tr").forEach(tr => tr.onclick = () => { select(+tr.dataset.k); document.getElementById("monitor").scrollIntoView({behavior: "smooth"}); });
}
document.querySelectorAll("#tbl th").forEach(th => th.onclick = () => { const k = th.dataset.k; asc = sortK === k ? !asc : true; sortK = k; drawTable(); select(sel); });
// ---------- static charts ----------
document.getElementById("noise").innerHTML = [["NDVI", .0436, .0298, "−32 %"], ["NDRE (red edge)", .0283, .0183, "−35 %"], ["NDMI (moisture)", .0433, .0306, "−29 %"]].map(([n, a, b, p]) =>
  `<div style="margin-top:12px"><b style="font-size:14px">${n}</b><div class="cmp" style="grid-template-columns:90px 1fr;margin-top:4px;gap:4px 10px"><span class="note">raw</span><div class="bar" style="width:${a / .0436 * 90}%;background:#C9D3E3"></div><span class="note">tide model</span><div style="display:flex;align-items:center;gap:8px"><div class="bar" style="width:${b / .0436 * 90}%;background:linear-gradient(90deg,#0A3D91,#0EA5E9)"></div><b style="color:#1E6FD9;white-space:nowrap">${p}</b></div></div></div>`).join("");
document.getElementById("sim").innerHTML = [["A tenth of a stand loses half its canopy", "within 60 days", 73, 13], ["A whole stand loses 10 % of its canopy", "within 6 months", 63, 36], ["A whole stand loses 20 % of its canopy", "within 6 months", 83, 36]].map(([n, w, d, c]) =>
  `<div style="margin:14px 0"><b>${n}</b> <span class="note">· ${w}</span><div style="display:flex;align-items:center;gap:8px;margin-top:6px"><div class="bar" style="width:${d * .8}%;height:22px;background:linear-gradient(90deg,#0A3D91,#0EA5E9)"></div><b style="color:#1E6FD9">${d} %</b></div><div style="display:flex;align-items:center;gap:8px;margin-top:4px"><div class="bar" style="width:${c * .8}%;background:#C9D3E3"></div><span class="note">${c} % by chance</span></div></div>`).join("");
(function gantt() {
  const rows = [["Stand 5", "2022-03-28", "2023-02-22", "2022-10-25"], ["Stand 9", "2022-03-28", "2023-02-22", "2022-12-07"], ["Stand 12", "2022-03-28", "2023-02-22", "2022-12-17"], ["Stand 6", "2022-03-28", "2023-02-22", "2023-02-17"], ["Stand 18", "2023-11-14", "2025-01-06", "2024-10-29"]];
  const t = s => new Date(s).getTime(), a0 = t("2022-01-01"), a1 = t("2025-04-01"), w = 1000, l = 100, X = s => l + (t(s) - a0) / (a1 - a0) * (w - l - 20);
  let s = `<svg class="chart" viewBox="0 0 ${w} 290" font-family="IBM Plex Sans">`;
  [2022, 2023, 2024, 2025].forEach(y => { const x = X(y + "-01-01"); s += `<line x1="${x}" x2="${x}" y1="0" y2="262" stroke="#E1ECFB"/><text x="${x}" y="284" font-size="14" fill="#4A5F86" text-anchor="middle">${y}</text>`; });
  rows.forEach(([n, a, b, al], i) => { const y = 14 + i * 50; s += `<text x="0" y="${y + 20}" font-size="15" font-weight="700" fill="#06235A">${n}</text><rect x="${X(a)}" y="${y + 4}" width="${X(b) - X(a)}" height="22" rx="6" fill="#BFDDFF" stroke="#1E6FD9"/><path d="M${X(al)} ${y} l11 15 l-11 15 l-11 -15z" fill="#FF4D6D" stroke="#fff" stroke-width="2"/>`; });
  document.getElementById("gantt").innerHTML = s + "</svg>";
})();
drawTable(); select(5);
</script>
</body></html>"""

html = PAGE.replace("__DATA__", json.dumps(data, separators=(",", ":"))).replace("__REPORTS__", json.dumps(REPORTS))
(ROOT / "docs/index.html").write_text(html, encoding="utf-8")
(ROOT / "docs/.nojekyll").write_text("", encoding="utf-8")
print("docs/index.html", round(len(html) / 1024), "KB; reports for stands", REPORTS)
