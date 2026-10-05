"""Render the README cover docs/assets/banner.png (1920 x 720): blue gradients, logo, title, key numbers, data sources, and the real outlines of the
25 pilot stands. Run from the repository root: python scripts/make_banner.py   (needs Playwright + Chrome/Chromium)"""
import json, pathlib
from playwright.sync_api import sync_playwright

gj = json.load(open("analysis/data/stands.geojson"))
pts = [c for f in gj["features"] for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]) for r in poly for c in r]
x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
W = 380; H = W * (y1 - y0) / ((x1 - x0) * 0.911); pj = lambda p: ((p[0] - x0) / (x1 - x0) * W, (y1 - p[1]) / (y1 - y0) * H)
CONVERTED = {5, 6, 9, 12, 18}          # stands with a conversion confirmed on dated sub-metre imagery (analysis/34_vhr_summary.md)
dpath = lambda f: "".join("M" + "L".join(f"{pj(c)[0]:.1f},{pj(c)[1]:.1f}" for c in r) + "Z"
                          for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]) for r in poly)
paths = "".join(f'<path d="{dpath(f)}"/>' for f in gj["features"] if f["properties"]["stand"] not in CONVERTED)
hot = "".join(f'<path d="{dpath(f)}"/>' for f in gj["features"] if f["properties"]["stand"] in CONVERTED)

LOGO = """<svg width="200" height="200" viewBox="0 0 240 240"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#A9E4FF"/><stop offset="1" stop-color="#2F80ED"/></linearGradient></defs>
<circle cx="120" cy="120" r="104" fill="rgba(255,255,255,.04)" stroke="url(#lg)" stroke-width="5"/>
<path d="M120 52 C 160 80 168 128 120 170 C 72 128 80 80 120 52 Z" fill="none" stroke="#FFFFFF" stroke-width="6"/>
<path d="M120 70 L120 168 M120 120 L102 104 M120 140 L140 124" stroke="#6CC7FF" stroke-width="5" fill="none"/>
<path d="M40 188 Q 70 172 100 188 T 160 188 T 210 188" stroke="#6CC7FF" stroke-width="6" fill="none"/>
<circle cx="47" cy="68" r="10" fill="#A9E4FF"/></svg>"""

HTML = f"""<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Sans+Arabic:wght@600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>*{{margin:0;box-sizing:border-box}} body{{width:1920px;height:720px;overflow:hidden;font-family:'IBM Plex Sans',sans-serif;color:#fff;
background:radial-gradient(900px 520px at 78% 30%, rgba(76,169,255,.35), transparent 70%), radial-gradient(700px 500px at 12% 110%, rgba(0,212,255,.22), transparent 70%),
linear-gradient(120deg,#030B26 0%,#06235A 38%,#0B4A9E 72%,#1477D6 100%)}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:64px 64px}}
.orbit{{position:absolute;border:1.5px solid rgba(169,228,255,.18);border-radius:50%}}
.mono{{font-family:'IBM Plex Mono',monospace;letter-spacing:3px;text-transform:uppercase}}
.chip{{background:linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.05));border:1px solid rgba(169,228,255,.35);border-radius:16px;padding:14px 20px;padding-right:42px}}
.chip b{{display:block;font-size:34px;font-weight:700;background:linear-gradient(90deg,#FFFFFF,#A9E4FF);-webkit-background-clip:text;color:transparent}}
.chip span{{font-size:17px;color:#BFDFFF}}
.step{{padding:8px 16px;border-radius:10px;border:1px solid rgba(169,228,255,.35)}} .arr{{color:#7FD3FF;font-size:22px}}
.card{{background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.03));border:1px solid rgba(169,228,255,.35);border-radius:20px;box-shadow:0 20px 60px rgba(0,10,40,.45)}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;background:#3DDC97;box-shadow:0 0 10px #3DDC97;margin-right:7px}}
.sw{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
.chip{{position:relative}} .ic{{position:absolute;right:14px;top:14px;opacity:.85}}
.tag{{display:inline-block;padding:6px 14px;border-radius:999px;font-size:17px;margin-right:8px;background:rgba(108,199,255,.16);border:1px solid rgba(108,199,255,.4);color:#D8EEFF}}
</style>
<div class="grid"></div>
<div style="position:absolute;left:-900px;right:-900px;bottom:-1180px;height:1200px;border-radius:50%;border-top:2px solid rgba(127,211,255,.45);box-shadow:0 -30px 90px rgba(0,180,255,.28)"></div>
<div class="orbit" style="width:1100px;height:1100px;left:1150px;top:-560px"></div><div class="orbit" style="width:760px;height:760px;left:1330px;top:-380px"></div>
<div style="position:absolute;left:1180px;top:0;width:260px;height:520px;background:linear-gradient(115deg,transparent 30%,rgba(127,211,255,.10) 55%,transparent 80%);
  clip-path:polygon(38% 9%,46% 9%,100% 30%,100% 86%)"></div>
<svg style="position:absolute;left:1300px;top:14px" width="110" height="80" viewBox="0 0 110 80"><g transform="rotate(-18 55 40)">
  <rect x="8" y="30" width="30" height="18" rx="2" fill="#2F80ED" stroke="#A9E4FF"/><line x1="16" y1="30" x2="16" y2="48" stroke="#A9E4FF"/><line x1="24" y1="30" x2="24" y2="48" stroke="#A9E4FF"/><line x1="32" y1="30" x2="32" y2="48" stroke="#A9E4FF"/>
  <rect x="72" y="30" width="30" height="18" rx="2" fill="#2F80ED" stroke="#A9E4FF"/><line x1="80" y1="30" x2="80" y2="48" stroke="#A9E4FF"/><line x1="88" y1="30" x2="88" y2="48" stroke="#A9E4FF"/><line x1="96" y1="30" x2="96" y2="48" stroke="#A9E4FF"/>
  <line x1="38" y1="39" x2="72" y2="39" stroke="#A9E4FF" stroke-width="2"/><rect x="45" y="27" width="20" height="24" rx="4" fill="#E8F4FF"/><circle cx="55" cy="56" r="4" fill="#6CC7FF"/></g></svg>
<div class="card" style="position:absolute;right:56px;top:34px;width:{W + 40}px;padding:14px 20px 12px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><span class="mono" style="font-size:12px;letter-spacing:2px;color:#A9E4FF;white-space:nowrap">Live monitor · Abu Dhabi</span>
  <span style="font-size:13px;color:#D8EEFF;white-space:nowrap"><span class="dot"></span>25 stands · 2,281 ha</span></div>
  <svg width="{W}" height="{H:.0f}" viewBox="-6 -6 {W + 12} {H + 12:.0f}"><defs><linearGradient id="mg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7FD3FF"/><stop offset="1" stop-color="#2F80ED"/></linearGradient>
  <filter id="gl"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
  <g fill="url(#mg)" fill-opacity=".55" stroke="#BFE7FF" stroke-width="1.2" stroke-opacity=".8">{paths}</g>
  <g fill="#FF6B85" fill-opacity=".6" stroke="#FFC2CE" stroke-width="1.4" filter="url(#gl)">{hot}</g></svg>
  <div style="display:flex;gap:14px;font-size:12.5px;color:#D8EEFF;margin-top:4px;white-space:nowrap"><span><i class="sw" style="background:#4FA8F0"></i>monitored stand</span>
  <span><i class="sw" style="background:#FF6B85"></i>conversion confirmed (0.3&ndash;0.5 m)</span></div></div>
<div style="position:absolute;left:90px;top:70px;display:flex;gap:44px;align-items:center">{LOGO}<div>
  <div class="mono" style="font-size:19px;color:#8FD3FF">Arab Youth Space Hackathon 2026 · Challenge 813</div>
  <div style="font-size:88px;font-weight:700;line-height:1.02;margin:10px 0 8px;background:linear-gradient(90deg,#FFFFFF 0%,#CBEBFF 60%,#7FD3FF 100%);-webkit-background-clip:text;color:transparent">Blue Carbon Guardian</div>
  <div style="font-size:30px;color:#D8EEFF">Tide-aware satellite monitoring for Gulf mangroves &mdash; from alert to evidence</div>
  <div style="margin-top:16px"><span class="tag">Theme: Ecosystem Health &amp; Blue Carbon</span><span class="tag" style="background:rgba(255,255,255,.16);border-color:rgba(255,255,255,.55);color:#fff;font-weight:600">Team Blue Athar · <span style="font-family:'IBM Plex Sans Arabic',sans-serif">الأثر الأزرق</span></span><span class="tag">by Nahla Nabil</span></div></div></div>
<div style="position:absolute;left:90px;top:440px;display:flex;gap:16px">
  <div class="chip"><b>&minus;29&ndash;35%</b><span>noise after tide model</span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7FD3FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/><path d="M2 18c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/></svg></div>
  <div class="chip"><b>91 stands</b><span>Abu Dhabi + Tarut Bay (KSA)</span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7FD3FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/></svg></div>
  <div class="chip"><b>5 confirmed</b><span>real conversions, 0.3&ndash;0.5 m</span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7FD3FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-6"/></svg></div>
  <div class="chip"><b>73% vs 13%</b><span>partial loss in 60 days vs chance</span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7FD3FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L4 14h7l-1 8 9-12h-7z"/></svg></div>
  <div class="chip"><b>&asymp; 247 kt C</b><span>carbon stock, pilot area</span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#7FD3FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15"/><path d="M5 19l7-7"/></svg></div></div>
<div style="position:absolute;left:90px;top:572px;display:flex;align-items:center;gap:12px;font-size:18px;color:#E6F3FF">
  <span class="step" style="background:rgba(10,61,145,.55)">1 · Sentinel-2 every ~5 days</span><span class="arr">&#10142;</span>
  <span class="step" style="background:rgba(20,95,200,.45)">2 · Tide-aware model</span><span class="arr">&#10142;</span>
  <span class="step" style="background:rgba(30,111,217,.45)">3 · Stand + 200 m cell alert</span><span class="arr">&#10142;</span>
  <span class="step" style="background:rgba(47,128,237,.45)">4 · Sub-metre evidence</span><span class="arr">&#10142;</span>
  <span class="step" style="background:rgba(14,165,233,.40)">5 · Carbon report + dashboard</span></div>
<div class="mono" style="position:absolute;left:90px;bottom:42px;font-size:16px;color:#9CC8F0">
  Data &nbsp;·&nbsp; Sentinel-2 L2A (778 dates) &nbsp;·&nbsp; EnMAP hyperspectral (224 bands) &nbsp;·&nbsp; ESA WorldCover &nbsp;·&nbsp; field carbon plots &nbsp;·&nbsp; dated sub-metre imagery</div>
<div style="position:absolute;left:0;right:0;bottom:0;height:6px;background:linear-gradient(90deg,#00D4FF,#2F80ED,#7FD3FF)"></div>"""
f = pathlib.Path("docs/assets/_banner.html"); f.write_text(HTML, encoding="utf-8")
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 720}); pg.goto(f.resolve().as_uri()); pg.wait_for_timeout(1500)
    pg.screenshot(path="docs/assets/banner.png"); b.close()
f.unlink(); print("docs/assets/banner.png")
