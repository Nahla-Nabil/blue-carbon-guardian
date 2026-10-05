"""Demo video, step 2: build video/build/video.html, a deterministic motion-graphics page. window.render(t) draws the frame at time t (seconds).
Uses our own outputs only: stand outlines, cell conditions, Sentinel-2 / EnMAP figures, dashboard screenshots. Run: python video/build_page.py"""
import json, shutil, os
import pandas as pd

B = "video/build"; A = f"{B}/assets"; os.makedirs(A, exist_ok=True)
for src in ["analysis/figures/stand5_before_after_2021_2026.png", "analysis/figures/stand9_before_after_2020_2026.png", "analysis/figures/stand12_key_years.png",
            "analysis/figures/stand18_key_years.png", "analysis/figures/enmap_stand5_two_epochs.png", "deck_source/images/dash_top_cells.png",
            "deck_source/images/dash_stand9_cells_chart.png"]:
    shutil.copy(src, A)
TL = json.load(open(f"{B}/timeline.json", encoding="utf-8"))

# stand outlines (25 pilot stands) projected to an SVG box, coloured by condition
gj = json.load(open("analysis/data/stands.geojson")); cond = pd.read_csv("analysis/data/stand_status.csv").set_index("stand").condition
pts = [c for f in gj["features"] for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]) for r in poly for c in r]
x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
W, H = 900, int(900 * (y1 - y0) / ((x1 - x0) * 0.911)); pj = lambda p: ((p[0] - x0) / (x1 - x0) * W, (y1 - p[1]) / (y1 - y0) * H)
paths = []
for f in gj["features"]:
    polys = [f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]
    d = "".join("M" + "L".join(f"{pj(c)[0]:.1f},{pj(c)[1]:.1f}" for c in r) + "Z" for poly in polys for r in poly)
    k = f["properties"]["stand"]; paths.append(dict(d=d, k=k, c=cond.get(k, "stable")))
# stand-9 cells
cm = pd.read_csv("data/sample_input/cells_stands_9_12_18.csv"); cs = pd.read_csv("results/03_cell_condition.csv")
c9 = cm[cm.stand == 9].merge(cs[["cell", "condition"]], on="cell")
cx0, cy0 = c9.col.min(), c9.row.min(); cells9 = [dict(x=float(r.col - cx0), y=float(r.row - cy0), bad=r.condition in ("decline", "severe decline")) for r in c9.itertuples()]
DATA = dict(tl=TL, paths=paths, mapW=W, mapH=H, cells=cells9)

HTML = r"""<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans+Arabic:wght@500;600&display=swap">
<style>
*{margin:0;box-sizing:border-box} html,body{width:1920px;height:1080px;overflow:hidden;background:#071716}
body{font-family:'IBM Plex Sans',sans-serif;color:#EAF3F0}
#bg{position:absolute;inset:0;background:radial-gradient(1200px 700px at 70% 30%, #12403A 0%, #0A2321 45%, #061312 100%)}
.L{position:absolute;opacity:0;will-change:transform,opacity}
.mono{font-family:'IBM Plex Mono',monospace;letter-spacing:3px;text-transform:uppercase;color:#3FC0A4}
.big{font-weight:700;letter-spacing:-1px}
.card{background:rgba(255,255,255,.06);border:1px solid rgba(159,193,187,.25);border-radius:22px;padding:28px 34px;backdrop-filter:blur(6px)}
#sub{position:absolute;left:50%;bottom:58px;transform:translateX(-50%);max-width:1500px;text-align:center;direction:rtl;font-family:'IBM Plex Sans Arabic',sans-serif;
     font-size:40px;font-weight:600;line-height:1.5;color:#fff;padding:14px 34px;border-radius:16px;background:rgba(3,14,13,.72);opacity:0}
#bar{position:absolute;left:0;top:0;height:5px;background:linear-gradient(90deg,#3FC0A4,#9FE7D5)}
#brand{position:absolute;left:70px;top:46px;font-size:22px;color:#9FC1BB;letter-spacing:2px;opacity:.0}
img{display:block}
</style>
<div id="bg"></div><canvas id="stars" width="1920" height="1080" style="position:absolute;inset:0"></canvas>
<div id="bar"></div><div id="brand" class="mono">Blue Carbon Guardian · Challenge 813</div>
<div id="stage"></div><div id="sub"></div>
<script>
const D = __DATA__;
const $ = id => document.getElementById(id), stage = $("stage");
const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x)), ease = x => 1 - Math.pow(1 - clamp(x), 3), easeIO = x => (x=clamp(x), x<.5 ? 4*x*x*x : 1-Math.pow(-2*x+2,3)/2);
const S = Object.fromEntries(D.tl.scenes.map(s => [s.id, s]));
function el(id, html, css){ const e = document.createElement("div"); e.id = id; e.className = "L"; e.innerHTML = html; Object.assign(e.style, css||{}); stage.appendChild(e); return e; }
function vis(sc, t, fin=.7, fout=.6){ const s=S[sc]; return clamp((t-s.start)/fin) * clamp((s.end-t)/fout); }
function loc(sc, t){ return t - S[sc].start; }
function set(e, o, tx=0, ty=0, sc=1, extra=""){ e.style.opacity = o; e.style.transform = `translate(${tx}px,${ty}px) scale(${sc}) ${extra}`; }
const fmt = n => Math.round(n).toLocaleString("en-US");

// ---- logo (svg) ----
const LOGO = `<svg width="240" height="240" viewBox="0 0 240 240"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9FE7D5"/><stop offset="1" stop-color="#0B7A66"/></linearGradient></defs>
<circle id="orb" cx="120" cy="120" r="104" fill="none" stroke="url(#g)" stroke-width="4" stroke-dasharray="654" stroke-dashoffset="654"/>
<path id="leaf" d="M120 52 C 160 80 168 128 120 170 C 72 128 80 80 120 52 Z" fill="none" stroke="#EAF3F0" stroke-width="5" stroke-dasharray="380" stroke-dashoffset="380"/>
<path id="vein" d="M120 70 L120 168 M120 120 L102 104 M120 140 L140 124" stroke="#3FC0A4" stroke-width="4" fill="none" stroke-dasharray="200" stroke-dashoffset="200"/>
<path id="wave" d="M40 188 Q 70 172 100 188 T 160 188 T 210 188" stroke="#3FC0A4" stroke-width="5" fill="none" stroke-dasharray="260" stroke-dashoffset="260"/>
<circle id="sat" cx="120" cy="16" r="9" fill="#9FE7D5"/></svg>`;
function drawLogo(root, p){ const q = s => root.querySelector(s);
  q("#orb").style.strokeDashoffset = 654*(1-ease(p*1.4)); q("#leaf").style.strokeDashoffset = 380*(1-ease(p*1.4-.25));
  q("#vein").style.strokeDashoffset = 200*(1-ease(p*1.4-.5)); q("#wave").style.strokeDashoffset = 260*(1-ease(p*1.4-.7));
  const a = -Math.PI/2 + p*Math.PI*1.2; q("#sat").setAttribute("cx", 120+104*Math.cos(a)); q("#sat").setAttribute("cy", 120+104*Math.sin(a)); }

// ---- scene elements ----
const intro1 = el("intro1", `<div class="mono" style="font-size:26px">Mangrove pledges by 2030</div><div class="big" id="cnt" style="font-size:190px;line-height:1.05">0</div>
  <div style="font-size:40px;color:#9FC1BB">mangroves · UAE <span style="color:#3FC0A4">+</span> Saudi Arabia</div>`, {left:"160px", top:"300px"});
const intro2 = el("intro2", `<div style="font-size:64px;font-weight:300;line-height:1.25;max-width:1500px">Who checks, <b style="font-weight:700;color:#9FE7D5">stand by stand</b>, that they survive &mdash;<br>and how much carbon they hold?</div>`, {left:"160px", top:"360px"});
const title = el("title", `<div style="display:flex;align-items:center;gap:60px"><div id="logoT">${LOGO}</div><div>
  <div class="mono" style="font-size:24px">Arab Youth Space Hackathon 2026 · Challenge 813 · Team Blue Athar</div>
  <div class="big" style="font-size:132px;line-height:1.02;margin:14px 0">Blue Carbon<br>Guardian</div>
  <div style="font-size:40px;color:#9FC1BB">Tide-aware satellite monitoring for Gulf mangroves</div></div></div>`, {left:"170px", top:"250px"});
const tideL = el("tideL", `<svg width="760" height="520" viewBox="0 0 760 520"><defs><linearGradient id="wg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2FA9C8" stop-opacity=".85"/><stop offset="1" stop-color="#0B3B4A" stop-opacity=".9"/></linearGradient></defs>
  <g id="trees"></g><path id="water" fill="url(#wg)"/><text x="10" y="40" fill="#9FC1BB" font-size="26" font-family="IBM Plex Mono">TIDE</text></svg>`, {left:"130px", top:"280px"});
const tideR = el("tideR", `<div class="mono" style="font-size:24px;margin-bottom:24px">Date-to-date noise, 25 stands</div><div id="bars"></div>
  <div style="font-size:30px;margin-top:22px;color:#9FC1BB"><span style="display:inline-block;width:22px;height:22px;background:#C98A10;border-radius:5px;vertical-align:-3px"></span> without tide model &nbsp;&nbsp;
  <span style="display:inline-block;width:22px;height:22px;background:#3FC0A4;border-radius:5px;vertical-align:-3px"></span> with tide model</div>`, {left:"1000px", top:"300px", width:"800px"});
const NOISE = [["NDVI", .0436, .0298], ["Red edge", .0283, .0183], ["Moisture", .0432, .0306]];
$("bars").innerHTML = NOISE.map((n,i) => `<div style="margin:22px 0"><div style="font-size:30px;margin-bottom:8px">${n[0]} <b id="red${i}" style="color:#9FE7D5;float:right"></b></div>
  <div id="b0${i}" style="height:26px;background:#C98A10;border-radius:7px;width:0"></div><div id="b1${i}" style="height:26px;background:#3FC0A4;border-radius:7px;width:0;margin-top:8px"></div></div>`).join("");
const STEPS = [["01","Stands & 200 m cells"],["02","Sentinel-2, every 5 days"],["03","Tide-aware model"],["04","Alert & condition"],["05","Carbon, dashboard, reports"]];
const pipe = el("pipe", `<div class="mono" style="font-size:26px;margin-bottom:40px">Approach</div><div style="display:flex;gap:26px;align-items:center">` +
  STEPS.map((s,i) => `<div id="st${i}" class="card" style="width:262px;height:230px;opacity:0;padding:26px 26px"><div class="mono" style="font-size:24px">${s[0]}</div><div style="font-size:33px;font-weight:600;margin-top:16px;line-height:1.2">${s[1]}</div></div>`).join(`<div style="font-size:44px;color:#3FC0A4">&rarr;</div>`) +
  `</div><div id="dot" style="position:absolute;width:22px;height:22px;border-radius:50%;background:#9FE7D5;box-shadow:0 0 30px #3FC0A4;top:262px;left:0"></div>`, {left:"100px", top:"330px"});
const mapE = el("mapE", `<svg height="660" width="${Math.round(660*D.mapW/D.mapH)}" viewBox="-10 -10 ${D.mapW+20} ${D.mapH+20}">` + D.paths.map((p,i) =>
  `<path id="mp${i}" d="${p.d}" fill="${p.c==='severe decline'?'#E2566E':'#3FC0A4'}" fill-opacity=".85" stroke="#9FE7D5" stroke-width="1" opacity="0"/>`).join("") + `</svg>`, {left:"140px", top:"160px"});
const mapT = el("mapT", `<div class="mono" style="font-size:26px">Monitored</div><div class="big" style="font-size:170px;line-height:1"><span id="n91">0</span></div>
  <div style="font-size:44px">mangrove stands</div><div style="font-size:32px;color:#9FC1BB;margin-top:20px;line-height:1.5">25 near Abu Dhabi (shown)<br>+ 66 unseen test stands in<br>Abu Dhabi &amp; Tarut Bay, Saudi Arabia</div>`, {left:"1220px", top:"300px"});
const SZ = 46, cells = el("cells", `<svg width="760" height="640" viewBox="-30 -30 ${Math.max(...D.cells.map(c=>c.x))*SZ/20+80} ${Math.max(...D.cells.map(c=>c.y))*SZ/20+80}">` +
  D.cells.map((c,i) => `<rect id="c${i}" x="${c.x*SZ/20}" y="${c.y*SZ/20}" width="${SZ-4}" height="${SZ-4}" rx="6" fill="#2E8B78" opacity="0"/>`).join("") + `</svg>`, {left:"240px", top:"170px"});
const cellsT = el("cellsT", `<div class="mono" style="font-size:26px">Stand 9</div><div style="font-size:54px;margin-top:20px">Stand average:</div>
  <div class="big" style="font-size:80px;color:#3FC0A4">stable</div><div style="font-size:54px;margin-top:36px">200 m cells:</div>
  <div class="big" id="badn" style="font-size:66px;color:#E2566E;max-width:760px">0 of 28 in severe decline</div>`, {left:"1080px", top:"230px"});
const EV = [["stand5_before_after_2021_2026.png","Stand 5 · 2021 → 2026 · reclamation with finger canals"],["stand9_before_after_2020_2026.png","Stand 9 · 2020 → 2026 · canal development takes the south-east"],
            ["stand12_key_years.png","Stand 12 · 2022 → 2023 → 2026 · found only by the cells"],["stand18_key_years.png","Stand 18 · 2020 → 2023 → 2026 · found only by the cells"]];
EV.forEach((e,i) => el("ev"+i, `<div style="width:1500px;height:590px;overflow:hidden;border-radius:22px;border:1px solid rgba(159,193,187,.35);background:#0b1f1e"><img id="evi${i}" src="assets/${e[0]}" style="width:1500px;height:590px;object-fit:contain"></div>
  <div style="font-size:34px;margin-top:20px;color:#EAF3F0">${e[1]}</div>`, {left:"210px", top:"190px"}));
const evBadge = el("evBadge", `<div class="card" style="padding:18px 30px"><span class="big" style="font-size:44px;color:#9FE7D5">5</span> <span style="font-size:32px">real conversions · confirmed at 0.3–0.5 m · 3 found only by cells</span></div>`, {left:"210px", top:"96px"});
const val = el("val", `<div class="mono" style="font-size:26px;margin-bottom:30px">Partial loss caught within 60 days (simulation)</div>
  <div style="display:flex;gap:80px;align-items:flex-end"><div><div class="big" style="font-size:200px;color:#9FE7D5;line-height:1"><span id="p73">0</span>%</div><div style="font-size:38px">with our alert</div></div>
  <div><div class="big" style="font-size:140px;color:#7E9B97;line-height:1"><span id="p13">0</span>%</div><div style="font-size:38px;color:#9FC1BB">by pure chance</div></div></div>
  <div id="oos" class="card" style="margin-top:56px;font-size:38px;opacity:0">65 unseen stands, thresholds fixed: <b style="color:#9FE7D5">0.79</b> false alarms per stand-year (vs 0.96 calibrated)</div>`, {left:"170px", top:"230px"});
const hyp = el("hyp", `<div style="width:1150px;height:560px;overflow:hidden;border-radius:22px;background:#fff"><img id="hypi" src="assets/enmap_stand5_two_epochs.png" style="width:1150px;height:560px;object-fit:contain"></div>
  <div style="font-size:24px;color:#9FC1BB;margin-top:14px">Contains modified EnMAP data © DLR 2022, 2025</div>`, {left:"110px", top:"220px"});
const hypT = el("hypT", `<div class="mono" style="font-size:26px">EnMAP · 224 bands</div><div class="big" style="font-size:120px;line-height:1.05;margin-top:20px">r = <span id="r99">0.00</span></div>
  <div style="font-size:36px;color:#9FC1BB;line-height:1.45;margin-top:14px">agreement with our<br>Sentinel-2 indices</div><div style="font-size:36px;margin-top:36px;line-height:1.45">Stand 5: vegetation<br>→ <b style="color:#E9C46A">sand</b></div>`, {left:"1340px", top:"280px"});
const prodC = el("prodC", `<div class="mono" style="font-size:26px">Carbon stock, pilot area (field-measured)</div><div class="big" style="font-size:150px;line-height:1.05"><span id="kt">0</span> <span style="font-size:60px">t C</span></div>
  <div style="font-size:34px;color:#9FC1BB">range 180,000–316,000 · stock, not a sequestration rate</div>`, {left:"150px", top:"200px"});
const prodI = el("prodI", `<div style="width:1080px;height:640px;overflow:hidden;border-radius:20px;box-shadow:0 40px 120px rgba(0,0,0,.6)"><img src="assets/dash_top_cells.png" style="width:1080px;height:640px;object-fit:cover;object-position:top"></div>`, {left:"720px", top:"200px"});
const NX = [["Pilot partner","validate with real records"],["Satellite 813 on gIQ","hyperspectral at incubation"],["The whole Gulf coast","UAE · Saudi Arabia · beyond"]];
const nx = el("nx", `<div class="mono" style="font-size:26px;margin-bottom:34px">Next steps</div><div style="display:flex;gap:30px">` + NX.map((n,i) =>
  `<div id="nx${i}" class="card" style="width:500px;opacity:0"><div class="big" style="font-size:46px;color:#9FE7D5">${n[0]}</div><div style="font-size:30px;color:#9FC1BB;margin-top:10px">${n[1]}</div></div>`).join("") +
  `</div><div style="font-size:34px;margin-top:50px;color:#EAF3F0">Free satellite data · compute &lt; USD 5 per site-year (measured) · cost to serve ≈ USD 3.3k</div>`, {left:"150px", top:"330px"});
const outro = el("outro", `<div style="display:flex;flex-direction:column;align-items:center;text-align:center"><div id="logoO">${LOGO}</div>
  <div class="big" style="font-size:110px;margin-top:20px">Blue Carbon Guardian</div><div style="font-size:48px;color:#9FE7D5;font-style:italic;margin-top:10px">From light to insight.</div>
  <div style="font-size:32px;color:#EAF3F0;margin-top:40px">Nahla Nabil · Team Blue Athar · Arab Youth Space Hackathon 2026 · Challenge 813</div>
  <div style="font-size:22px;color:#7E9B97;margin-top:30px">Contains modified Copernicus Sentinel data 2020–2026 · Contains modified EnMAP data © DLR 2022, 2025 · ESA WorldCover 2021 (CC BY 4.0) · Schile et al. 2016 (CC0)</div></div>`,
  {left:"0", top:"170px", width:"1920px"});

// ---- starfield ----
const cv = $("stars"), cx = cv.getContext("2d"); let seed = 7; const rnd = () => (seed = (seed*16807) % 2147483647) / 2147483647;
const STARS = Array.from({length:220}, () => [rnd()*1920, rnd()*1080, rnd()*1.6+.3, rnd()*6.28]);
function stars(t){ cx.clearRect(0,0,1920,1080); for (const s of STARS){ cx.globalAlpha = .25+.35*Math.sin(t*.8+s[3])**2; cx.fillStyle="#BFEDE2"; cx.beginPath(); cx.arc((s[0]+t*6)%1920, s[1], s[2], 0, 6.29); cx.fill(); } }

// ---- trees + water for the tide scene ----
(function(){ let g = ""; for (let i=0;i<14;i++){ const x=30+i*52, h=120+((i*37)%60); g += `<path d="M${x} 400 L${x} ${400-h}" stroke="#2E5E52" stroke-width="7"/><ellipse cx="${x}" cy="${400-h}" rx="40" ry="34" fill="#2E8B78" opacity=".9"/>
  <path d="M${x} 400 Q ${x-18} 430 ${x-30} 460 M${x} 400 Q ${x+18} 430 ${x+30} 460" stroke="#2E5E52" stroke-width="4" fill="none"/>`; } document.getElementById("trees").innerHTML = g; })();

window.render = function(t){
  stars(t); $("bar").style.width = (t / D.tl.duration * 1920) + "px"; $("brand").style.opacity = clamp((t-S.title.end)) * .8 * clamp((S.outro.start - t)/.6);
  // intro
  let v = vis("intro", t), l = loc("intro", t), half = (S.intro.end - S.intro.start) * .48;
  set(intro1, v * clamp((half - l)/.6), 0, 30*(1-ease(l)), 1); $("cnt").textContent = fmt(200000000 * easeIO(l/3.2));
  set(intro2, v * clamp((l-half)/.6), 0, 40*(1-ease(l-half)));
  // title
  v = vis("title", t); l = loc("title", t); set(title, v, 0, 20*(1-ease(l)), .97 + .03*ease(l)); drawLogo($("logoT"), l/2.6);
  // tide
  v = vis("tide", t); l = loc("tide", t); set(tideL, v, -40*(1-ease(l))); set(tideR, v, 40*(1-ease(l)));
  const lvl = 300 + 90*Math.sin(l*1.6); let wd = `M0 ${lvl}`; for (let x=0;x<=760;x+=20) wd += ` L${x} ${lvl + 10*Math.sin(x/40 + l*3)}`; $("water").setAttribute("d", wd + " L760 520 L0 520 Z");
  NOISE.forEach((n,i) => { const p0 = ease((l-1-i*.4)/1.2), p1 = ease((l-4.5-i*.4)/1.2);
    $("b0"+i).style.width = (n[1]/.0436*640*p0)+"px"; $("b1"+i).style.width = (n[2]/.0436*640*p1)+"px";
    $("red"+i).textContent = p1 > .05 ? "−" + Math.round(100*(1-n[2]/n[1])*p1) + "%" : ""; });
  // pipeline
  v = vis("pipe" && "pipeline", t); l = loc("pipeline", t); set(pipe, v);
  STEPS.forEach((s,i) => { const p = ease((l-.3-i*.9)/.7); const e = $("st"+i); e.style.opacity = p; e.style.transform = `translateY(${30*(1-p)}px)`;
    e.style.borderColor = (l > .3+i*.9+.7 && l < .3+(i+1)*.9+.7) ? "#3FC0A4" : "rgba(159,193,187,.25)"; });
  $("dot").style.left = (Math.min(1, clamp(l/6.2)) * 1680) + "px"; $("dot").style.opacity = clamp(l-.5)*clamp(7.5-l);
  // map
  v = vis("map", t); l = loc("map", t); set(mapE, v, 0, 0, .96+.04*ease(l/3)); set(mapT, v, 30*(1-ease(l)));
  D.paths.forEach((p,i) => $("mp"+i).setAttribute("opacity", ease((l - .2 - i*.08)/.5)));
  $("n91").textContent = Math.round(91 * easeIO((l-.3)/2.4));
  // cells
  v = vis("cells", t); l = loc("cells", t); set(cells, v); set(cellsT, v, 30*(1-ease(l)));
  let nb = 0; D.cells.forEach((c,i) => { const r = $("c"+i); r.setAttribute("opacity", ease((l-.2-i*.04)/.4));
    const turn = c.bad && l > 3.6 + (nb++)*.25; r.setAttribute("fill", turn ? "#E2566E" : "#2E8B78"); });
  const nbad = D.cells.filter(c=>c.bad).length; $("badn").textContent = `${Math.min(nbad, Math.max(0, Math.floor((l-3.6)/.25)+1))} of 28 in severe decline`;
  $("badn").style.opacity = clamp((l-3.4)/.5);
  // events (4 images, Ken Burns)
  v = vis("events", t); l = loc("events", t); const dur = S.events.end - S.events.start, seg = dur / 4;
  EV.forEach((e,i) => { const a = l - i*seg, o = v * clamp(a/.6) * clamp((seg - a)/.6 + (i==3 ? 9 : 0)); set($("ev"+i), o, 0, 0, 1);
    $("evi"+i).style.transform = `scale(${1.0 + .06*clamp(a/seg)})`; });
  set(evBadge, v * clamp((l-1)/.6), 0, -20*(1-ease(l-1)));
  // validation
  v = vis("validation", t); l = loc("validation", t); set(val, v);
  $("p73").textContent = Math.round(73 * easeIO((l-.8)/2.2)); $("p13").textContent = Math.round(13 * easeIO((l-1.6)/1.6));
  $("oos").style.opacity = clamp((l - (S.validation.end - S.validation.start) * .62)/.6);
  // hyperspectral
  v = vis("hyper", t); l = loc("hyper", t); set(hyp, v, -30*(1-ease(l))); $("hypi").style.transform = `scale(${1+.05*clamp(l/10)})`;
  set(hypT, v, 30*(1-ease(l))); $("r99").textContent = (.99*easeIO((l-.6)/2.4)).toFixed(2);
  // product
  v = vis("product", t); l = loc("product", t); set(prodC, v * clamp((6.4-l)/.6 + (l<6.4?0:0)), 0, 0); $("kt").textContent = fmt(247000*easeIO((l-.4)/2.6));
  const pi = clamp((l-5.6)/1.2); set(prodI, v*ease(pi), 0, 120*(1-ease(pi)), .92+.08*ease(pi), `perspective(1600px) rotateX(${12*(1-ease(pi))}deg)`);
  prodC.style.opacity = v * (l < 5.6 ? 1 : clamp(1-(l-5.6)/.8) * .0 + clamp(1-(l-5.6)/.8));
  // next
  v = vis("next", t); l = loc("next", t); set(nx, v); NX.forEach((n,i) => { const p = ease((l-.6-i*.8)/.7); $("nx"+i).style.opacity = p; $("nx"+i).style.transform = `translateY(${30*(1-p)}px)`; });
  // outro
  v = vis("outro", t, .9, 1.2); l = loc("outro", t); set(outro, v, 0, 20*(1-ease(l))); drawLogo($("logoO"), l/2.8);
  // subtitles (Arabic)
  const sb = D.tl.subs.find(s => t >= s.start - .15 && t <= s.end + .35); const sub = $("sub");
  if (sb){ if (sub.dataset.k !== sb.start+"") { sub.textContent = sb.ar; sub.dataset.k = sb.start; } sub.style.opacity = clamp((t-sb.start+.15)/.25) * clamp((sb.end+.35-t)/.25); }
  else sub.style.opacity = 0;
};
window.ready = (async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => i.onload = i.onerror = r))); return true; })();
</script>"""
open(f"{B}/video.html", "w", encoding="utf-8").write(HTML.replace("__DATA__", json.dumps(DATA)))
print("video/build/video.html written;", len(paths), "stand outlines,", len(cells9), "cells")
