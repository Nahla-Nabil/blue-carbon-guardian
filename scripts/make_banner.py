"""Render the README cover docs/assets/banner.png (1920 x 640): blue gradient, logo, title, four key numbers, and the real outlines of the 25 pilot
stands (the five confirmed conversions in coral). Run from the repository root: python scripts/make_banner.py   (needs Playwright + Chrome/Chromium)"""
import json, pathlib
from playwright.sync_api import sync_playwright

gj = json.load(open("analysis/data/stands.geojson"))
polys = lambda f: [f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]
pts = [c for f in gj["features"] for poly in polys(f) for r in poly for c in r]
x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
W = 400; H = W * (y1 - y0) / ((x1 - x0) * 0.911); pj = lambda p: ((p[0] - x0) / (x1 - x0) * W, (y1 - p[1]) / (y1 - y0) * H)
CONVERTED = {5, 6, 9, 12, 18}          # stands with a conversion confirmed on dated sub-metre imagery (analysis/34_vhr_summary.md)
dpath = lambda f: "".join("M" + "L".join(f"{pj(c)[0]:.1f},{pj(c)[1]:.1f}" for c in r) + "Z" for poly in polys(f) for r in poly)
paths = "".join(f'<path d="{dpath(f)}"/>' for f in gj["features"] if f["properties"]["stand"] not in CONVERTED)
hot = "".join(f'<path d="{dpath(f)}"/>' for f in gj["features"] if f["properties"]["stand"] in CONVERTED)

LOGO = """<svg width="150" height="150" viewBox="0 0 240 240"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#A9E4FF"/><stop offset="1" stop-color="#2F80ED"/></linearGradient></defs>
<circle cx="120" cy="120" r="104" fill="rgba(255,255,255,.05)" stroke="url(#lg)" stroke-width="6"/>
<path d="M120 52 C 160 80 168 128 120 170 C 72 128 80 80 120 52 Z" fill="none" stroke="#FFFFFF" stroke-width="7"/>
<path d="M120 70 L120 168 M120 120 L102 104 M120 140 L140 124" stroke="#6CC7FF" stroke-width="6" fill="none"/>
<path d="M40 188 Q 70 172 100 188 T 160 188 T 210 188" stroke="#6CC7FF" stroke-width="7" fill="none"/></svg>"""

CHIPS = [("&minus;29&ndash;35 %", "less noise with the tide model"), ("5 confirmed", "real mangrove conversions"),
         ("73 % vs 13 %", "partial loss caught vs chance"), ("&asymp; 247 kt C", "carbon stock, pilot area")]

HTML = f"""<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Sans+Arabic:wght@600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>*{{margin:0;box-sizing:border-box}} body{{width:1920px;height:640px;overflow:hidden;font-family:'IBM Plex Sans',sans-serif;color:#fff;
background:radial-gradient(900px 520px at 80% 30%, rgba(76,169,255,.32), transparent 70%),linear-gradient(120deg,#030B26 0%,#06235A 40%,#0B4A9E 75%,#1477D6 100%)}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);background-size:64px 64px}}
.mono{{font-family:'IBM Plex Mono',monospace;letter-spacing:4px;text-transform:uppercase}}
.chip{{width:300px;height:118px;padding:18px 22px;border-radius:18px;background:linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.05));border:1px solid rgba(169,228,255,.35)}}
.chip b{{display:block;font-size:38px;font-weight:700;white-space:nowrap;background:linear-gradient(90deg,#FFFFFF,#A9E4FF);-webkit-background-clip:text;color:transparent}}
.chip span{{display:block;margin-top:6px;font-size:18px;color:#BFDFFF}}
.tag{{display:inline-block;padding:7px 16px;border-radius:999px;font-size:18px;margin-right:10px;background:rgba(108,199,255,.14);border:1px solid rgba(108,199,255,.4);color:#D8EEFF}}
.sw{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:7px;vertical-align:-1px}}
</style>
<div class="grid"></div>
<div style="position:absolute;left:96px;top:78px;display:flex;gap:40px;align-items:center">{LOGO}<div>
  <div class="mono" style="font-size:18px;color:#8FD3FF">Arab Youth Space Hackathon 2026 · Challenge 813</div>
  <div style="font-size:84px;font-weight:700;line-height:1.05;margin:8px 0 6px;background:linear-gradient(90deg,#FFFFFF 0%,#CBEBFF 60%,#7FD3FF 100%);-webkit-background-clip:text;color:transparent">Blue Carbon Guardian</div>
  <div style="font-size:28px;color:#D8EEFF">Tide-aware satellite monitoring for Gulf mangroves &mdash; from alert to evidence</div>
  <div style="margin-top:18px"><span class="tag" style="background:rgba(255,255,255,.16);border-color:rgba(255,255,255,.5);color:#fff;font-weight:600">Team Blue Athar · <span style="font-family:'IBM Plex Sans Arabic',sans-serif">الأثر الأزرق</span></span><span class="tag">Ecosystem Health &amp; Blue Carbon</span><span class="tag">by Nahla Nabil</span></div></div></div>
<div style="position:absolute;left:96px;bottom:70px;display:flex;gap:18px">{"".join(f'<div class="chip"><b>{a}</b><span>{b}</span></div>' for a, b in CHIPS)}</div>
<div style="position:absolute;right:70px;top:56px;bottom:56px;width:{W + 52}px;padding:18px 26px;border-radius:22px;background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.03));border:1px solid rgba(169,228,255,.35);display:flex;flex-direction:column;justify-content:space-between">
  <div class="mono" style="font-size:13px;letter-spacing:3px;color:#A9E4FF;white-space:nowrap">Abu Dhabi pilot · 25 stands</div>
  <svg width="{W}" height="{H:.0f}" viewBox="-6 -6 {W + 12} {H + 12:.0f}"><defs><linearGradient id="mg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7FD3FF"/><stop offset="1" stop-color="#2F80ED"/></linearGradient></defs>
  <g fill="url(#mg)" fill-opacity=".55" stroke="#BFE7FF" stroke-width="1.2" stroke-opacity=".8">{paths}</g>
  <g fill="#FF6B85" fill-opacity=".7" stroke="#FFC2CE" stroke-width="1.4">{hot}</g></svg>
  <div style="font-size:14px;color:#D8EEFF;white-space:nowrap"><i class="sw" style="background:#4FA8F0"></i>monitored stand &nbsp; <i class="sw" style="background:#FF6B85"></i>conversion confirmed (0.3&ndash;0.5 m)</div></div>
<div style="position:absolute;left:0;right:0;bottom:0;height:6px;background:linear-gradient(90deg,#00D4FF,#2F80ED,#7FD3FF)"></div>"""
f = pathlib.Path("docs/assets/_banner.html"); f.write_text(HTML, encoding="utf-8")
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 640}); pg.goto(f.resolve().as_uri()); pg.wait_for_timeout(1500)
    pg.screenshot(path="docs/assets/banner.png"); b.close()
f.unlink(); print("docs/assets/banner.png")
