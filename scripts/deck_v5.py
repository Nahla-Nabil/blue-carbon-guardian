"""Deck v5 (blue design): rewrites deck_source/slides/*.html (16 slides, the submission guide's order) with charts and diagrams drawn as inline SVG
from the project's own numbers, and real images from deck_source/images/. Speaker notes (<aside>) are kept from the previous version.
Every number here is one already approved in the analysis summaries (README section 8). Run from the repository root, then export the PDF:
    python scripts/deck_v5.py && python scripts/export_slides_pdf.py
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent; SL = ROOT / "deck_source" / "slides"
ORDER = json.load(open(ROOT / "deck_source" / "deck.json", encoding="utf-8"))["order"]
NOTES = {}
for s in ORDER:
    m = re.search(r"<aside>.*?</aside>", (SL / f"{s}.html").read_text(encoding="utf-8"), re.S)
    NOTES[s] = m.group(0) if m else ""

NAVY, BLUE, SKY, CYAN, ICE, CORAL, AMBER, MUTED, INK = "#06235A", "#1E6FD9", "#2F80ED", "#0EA5E9", "#E8F2FF", "#FF4D6D", "#FFB020", "#4A5F86", "#0B1B3F"

CSS = """<style>
.k{font-family:'IBM Plex Mono',monospace;font-size:22px;letter-spacing:3px;text-transform:uppercase;color:#1E6FD9;font-weight:600}
.h{font-size:58px;font-weight:700;color:#06235A;line-height:1.08;margin-top:10px}
.lede{font-size:26px;color:#4A5F86;line-height:1.45;margin-top:14px}
.card{background:#fff;border:1px solid #D6E6FF;border-radius:22px;box-shadow:0 12px 32px rgba(10,61,145,.08);padding:26px 30px}
.dk{background:linear-gradient(135deg,#06235A 0%,#0B4A9E 100%);color:#fff;border:none}
.big{font-size:64px;font-weight:700;line-height:1;background:linear-gradient(90deg,#0A3D91,#1E6FD9 60%,#0EA5E9);-webkit-background-clip:text;color:transparent}
.bigw{font-size:64px;font-weight:700;line-height:1;background:linear-gradient(90deg,#FFFFFF,#A9E4FF);-webkit-background-clip:text;color:transparent}
.t{font-size:24px;color:#0B1B3F;line-height:1.4} .s{font-size:20px;color:#4A5F86;line-height:1.4} .w{color:#fff} .ws{color:#BFDFFF}
.b{font-weight:700} .lab{font-family:'IBM Plex Mono',monospace;font-size:17px;letter-spacing:2px;text-transform:uppercase;font-weight:600}
.pill{display:inline-block;padding:7px 16px;border-radius:999px;font-size:19px;font-weight:600;background:#E8F2FF;color:#0A3D91;border:1px solid #C3DDFF}
.ic{width:64px;height:64px;border-radius:18px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1E6FD9,#0EA5E9);flex:none}
.row{display:flex;gap:26px} .col{display:flex;flex-direction:column;gap:20px}
.mono{font-family:'IBM Plex Mono',monospace}
</style>"""

ICONS = {  # 24x24 stroke icons
    "sat": '<rect x="9" y="9" width="6" height="6" rx="1"/><path d="M3 7l4 4M17 13l4 4M7 3L3 7l3 3 4-4zM17 21l4-4-3-3-4 4zM14 10l2-2"/>',
    "wave": '<path d="M2 12c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/><path d="M2 18c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/><path d="M2 6c2-3 4-3 6 0s4 3 6 0 4-3 6 0"/>',
    "grid": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M15 3v18M3 9h18M3 15h18"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    "map": '<path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4z"/><path d="M8 2v16M16 6v16"/>',
    "leaf": '<path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15"/><path d="M5 19l7-7"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
    "build": '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    "check": '<circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "layers": '<path d="M12 2l10 5-10 5L2 7l10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>',
    "dollar": '<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1zM4 22v-7"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
    "alert": '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "pixel": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
    "spectrum": '<path d="M2 18c3-12 5-12 7-6s4 6 6-2 4-6 7 2"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
}


def icon(name, size=34, color="#fff", box=True, bg=None):
    svg = f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    if not box:
        return svg
    st = f' style="background:{bg}"' if bg else ""
    return f'<div class="ic"{st}>{svg}</div>'


def light(sid, n, kicker, title, body, lede=""):
    led = f'<p class="lede">{lede}</p>' if lede else ""
    return f"""<section id="{sid}" data-transition="fade" style="background:radial-gradient(900px 500px at 100% 0%, rgba(47,128,237,.10), transparent 70%),linear-gradient(180deg,#FFFFFF 0%,#F2F7FF 100%); color:{INK}; font-family:'IBM Plex Sans', Arial, sans-serif; padding:60px 96px 100px 96px; display:flex; flex-direction:column">
{CSS}
  <div style="position:absolute;left:0;top:0;width:12px;height:100%;background:linear-gradient(180deg,#0EA5E9,#1E6FD9 50%,#06235A)"></div>
  <p class="k">{kicker}</p>
  <h2 class="h">{title}</h2>{led}
  <div style="margin-top:30px;flex:1;min-height:0;display:flex;flex-direction:column">{body}</div>
  <div style="position:absolute;left:96px;right:96px;bottom:30px;display:flex;justify-content:space-between;align-items:center">
    <p class="s" style="font-size:19px">Blue Carbon Guardian &#183; Team Blue Athar</p>
    <p class="mono" style="font-size:18px;font-weight:600;color:#fff;background:{BLUE};padding:5px 14px;border-radius:999px">{n:02d} / 16</p></div>
  {NOTES[sid]}
</section>
"""


def dark(sid, body):
    return f"""<section id="{sid}" data-transition="fade" style="background:radial-gradient(1000px 600px at 82% 25%, rgba(76,169,255,.35), transparent 70%),radial-gradient(800px 600px at 8% 110%, rgba(0,212,255,.22), transparent 70%),linear-gradient(120deg,#030B26 0%,#06235A 38%,#0B4A9E 72%,#1477D6 100%); color:#fff; font-family:'IBM Plex Sans', Arial, sans-serif; padding:0">
{CSS}
  <div style="position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);background-size:64px 64px"></div>
  <div style="position:absolute;width:1300px;height:1300px;left:1050px;top:-650px;border:1.5px solid rgba(169,228,255,.18);border-radius:50%"></div>
  <div style="position:absolute;width:900px;height:900px;left:1260px;top:-450px;border:1.5px solid rgba(169,228,255,.14);border-radius:50%"></div>
  <div style="position:absolute;left:0;right:0;bottom:0;height:8px;background:linear-gradient(90deg,#00D4FF,#2F80ED,#7FD3FF)"></div>
{body}
  {NOTES[sid]}
</section>
"""


# ---------- shared SVG builders ----------
def stand_map(w, dark_bg=False, label=True):
    gj = json.load(open(ROOT / "analysis/data/stands.geojson"))
    pts = [c for f in gj["features"] for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]) for r in poly for c in r]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    h = w * (y1 - y0) / ((x1 - x0) * 0.911)
    pj = lambda p: ((p[0] - x0) / (x1 - x0) * w, (y1 - p[1]) / (y1 - y0) * h)
    conv = {5, 6, 9, 12, 18}
    def d(f):
        polys = [f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]
        return "".join("M" + "L".join(f"{pj(c)[0]:.1f},{pj(c)[1]:.1f}" for c in r) + "Z" for poly in polys for r in poly)
    fill, stroke = ("#4FA8F0", "#BFE7FF") if dark_bg else ("#7FB6F5", "#1E6FD9")
    norm = "".join(f'<path d="{d(f)}"/>' for f in gj["features"] if f["properties"]["stand"] not in conv)
    hot = "".join(f'<path d="{d(f)}"/>' for f in gj["features"] if f["properties"]["stand"] in conv)
    labs = ""
    if label:
        for f in gj["features"]:
            k = f["properties"]["stand"]
            if k in conv:
                ring = f["geometry"]["coordinates"][0] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"][0][0]
                cx = sum(pj(c)[0] for c in ring) / len(ring); cy = sum(pj(c)[1] for c in ring) / len(ring)
                labs += (f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="15" fill="{"#fff" if dark_bg else NAVY}"/>'
                         f'<text x="{cx:.0f}" y="{cy + 6:.0f}" font-size="16" font-weight="700" text-anchor="middle" fill="{NAVY if dark_bg else "#fff"}" font-family="IBM Plex Sans">{k}</text>')
    return (f'<svg width="{w}" height="{h:.0f}" viewBox="-8 -8 {w + 16} {h + 16:.0f}">'
            f'<g fill="{fill}" fill-opacity=".55" stroke="{stroke}" stroke-width="1.3">{norm}</g>'
            f'<g fill="{CORAL}" fill-opacity=".7" stroke="#C8384F" stroke-width="1.5">{hot}</g>{labs}</svg>'), h


def bars_before_after():
    rows = [("NDVI", .0436, .0298, "−32 %"), ("NDRE (red edge)", .0283, .0183, "−35 %"), ("NDMI (canopy moisture)", .0433, .0306, "−29 %")]
    W, X0, sc = 760, 300, 9000
    s = f'<svg width="{W}" height="400" viewBox="0 0 {W} 400" font-family="IBM Plex Sans">'
    for i, (n, a, b, p) in enumerate(rows):
        y = 20 + i * 128
        s += f'<text x="0" y="{y + 30}" font-size="24" font-weight="600" fill="{NAVY}">{n}</text>'
        s += f'<rect x="{X0}" y="{y + 4}" width="{a * sc:.0f}" height="36" rx="8" fill="#B9C7DE"/><text x="{X0 + a * sc + 10:.0f}" y="{y + 30}" font-size="20" fill="{MUTED}">{a:.3f} raw</text>'
        s += f'<rect x="{X0}" y="{y + 50}" width="{b * sc:.0f}" height="36" rx="8" fill="url(#gb)"/><text x="{X0 + b * sc + 10:.0f}" y="{y + 76}" font-size="20" font-weight="700" fill="{BLUE}">{b:.3f}  {p}</text>'
    s += f'<defs><linearGradient id="gb"><stop offset="0" stop-color="#0A3D91"/><stop offset="1" stop-color="#0EA5E9"/></linearGradient></defs>'
    s += f'<rect x="0" y="388" width="16" height="12" fill="#B9C7DE"/><text x="24" y="399" font-size="18" fill="{MUTED}">without tide model</text>'
    s += f'<rect x="230" y="388" width="16" height="12" fill="{BLUE}"/><text x="254" y="399" font-size="18" fill="{MUTED}">with tide model (robust residual noise)</text></svg>'
    return s


def tide_illustration():
    def panel(x, lvl, title, ndvi, col):
        trees = "".join(f'<rect x="{x + 40 + i * 52}" y="150" width="6" height="90" fill="#5B6B5E"/><circle cx="{x + 43 + i * 52}" cy="140" r="26" fill="#2E8B57"/>' for i in range(6))
        return (f'<g><rect x="{x}" y="60" width="360" height="250" rx="18" fill="#F4F8FF" stroke="#D6E6FF"/>'
                f'<text x="{x + 20}" y="96" font-size="22" font-weight="700" fill="{NAVY}">{title}</text>{trees}'
                f'<rect x="{x + 1}" y="{lvl}" width="358" height="{309 - lvl}" fill="{SKY}" fill-opacity=".45"/>'
                f'<path d="M{x + 1} {lvl} q 30 -10 60 0 t 60 0 t 60 0 t 60 0 t 60 0 t 58 0" stroke="{BLUE}" stroke-width="3" fill="none"/>'
                f'<text x="{x + 20}" y="350" font-size="22" fill="{MUTED}">satellite NDVI</text><text x="{x + 200}" y="350" font-size="26" font-weight="700" fill="{col}">{ndvi}</text></g>')
    return ('<svg width="780" height="370" viewBox="0 0 780 370" font-family="IBM Plex Sans">' + panel(0, 270, "Low tide", "0.30", BLUE)
            + panel(410, 185, "High tide", "0.18", CORAL)
            + '<text x="385" y="40" font-size="20" fill="#4A5F86" text-anchor="middle">same trees, same day of the year</text></svg>')


def gantt():
    rows = [("Stand 5", "2022-03-28", "2023-02-22", "2022-10-25"), ("Stand 9", "2022-03-28", "2023-02-22", "2022-12-07"),
            ("Stand 12", "2022-03-28", "2023-02-22", "2022-12-17"), ("Stand 6", "2022-03-28", "2023-02-22", "2023-02-17"),
            ("Stand 18", "2023-11-14", "2025-01-06", "2024-10-29")]
    import datetime as dt
    D = lambda s: dt.date.fromisoformat(s); a0, a1 = D("2022-01-01"), D("2025-04-01")
    W, L = 640, 120; X = lambda s: L + (D(s) - a0).days / (a1 - a0).days * (W - L - 10)
    s = f'<svg width="{W}" height="430" viewBox="0 0 {W} 430" font-family="IBM Plex Sans">'
    for yr in (2022, 2023, 2024, 2025):
        x = X(f"{yr}-01-01"); s += f'<line x1="{x:.0f}" x2="{x:.0f}" y1="10" y2="372" stroke="#D6E6FF"/><text x="{x:.0f}" y="398" font-size="19" fill="{MUTED}" text-anchor="middle">{yr}</text>'
    for i, (n, a, b, al) in enumerate(rows):
        y = 26 + i * 70
        s += f'<text x="0" y="{y + 26}" font-size="22" font-weight="700" fill="{NAVY}">{n}</text>'
        s += f'<rect x="{X(a):.0f}" y="{y + 6}" width="{X(b) - X(a):.0f}" height="30" rx="8" fill="#BFDDFF" stroke="{BLUE}"/>'
        cx = X(al); s += f'<path d="M{cx:.0f} {y + 2} l14 19 l-14 19 l-14 -19z" fill="{CORAL}" stroke="#fff" stroke-width="2"/>'
    s += (f'<rect x="{L}" y="410" width="26" height="14" rx="4" fill="#BFDDFF" stroke="{BLUE}"/><text x="{L + 34}" y="423" font-size="17" fill="{MUTED}">last intact → first capture with works</text>'
          f'<path d="M{L + 390} 410 l8 8 l-8 8 l-8 -8z" fill="{CORAL}"/><text x="{L + 404}" y="423" font-size="17" fill="{MUTED}">our alert starts</text></svg>')
    return s


def sim_chart():
    rows = [("A tenth of a stand loses half its canopy", "within 60 days", 73, 13), ("A whole stand loses 10 % of its canopy", "within 6 months", 63, 36),
            ("A whole stand loses 20 % of its canopy", "within 6 months", 83, 36)]
    W = 1000; X0 = 440; sc = 5.2
    s = f'<svg width="{W}" height="420" viewBox="0 0 {W} 420" font-family="IBM Plex Sans"><defs><linearGradient id="gs"><stop offset="0" stop-color="#0A3D91"/><stop offset="1" stop-color="#0EA5E9"/></linearGradient></defs>'
    for i, (n, w, d, c) in enumerate(rows):
        y = 10 + i * 132
        s += f'<text x="0" y="{y + 34}" font-size="23" font-weight="600" fill="{NAVY}">{n}</text><text x="0" y="{y + 64}" font-size="20" fill="{MUTED}">{w}</text>'
        s += f'<rect x="{X0}" y="{y + 8}" width="{d * sc:.0f}" height="44" rx="10" fill="url(#gs)"/><text x="{X0 + d * sc + 12:.0f}" y="{y + 40}" font-size="30" font-weight="700" fill="{BLUE}">{d} %</text>'
        s += f'<rect x="{X0}" y="{y + 60}" width="{c * sc:.0f}" height="30" rx="8" fill="#C9D3E3"/><text x="{X0 + c * sc + 12:.0f}" y="{y + 82}" font-size="21" fill="{MUTED}">{c} % by chance</text>'
    s += '</svg>'
    return s


def data_timeline():
    import datetime as dt
    D = lambda s: dt.date.fromisoformat(s); a0, a1 = D("2013-01-01"), D("2026-12-31"); W, L = 1700, 250
    X = lambda s: L + (D(s) - a0).days / (a1 - a0).days * (W - L - 20)
    s = f'<svg width="{W}" height="236" viewBox="0 0 {W} 236" font-family="IBM Plex Sans">'
    for yr in range(2013, 2027):
        x = X(f"{yr}-01-01"); s += f'<line x1="{x:.0f}" x2="{x:.0f}" y1="0" y2="196" stroke="#E1ECFB"/><text x="{x + 4:.0f}" y="226" font-size="18" fill="{MUTED}">{yr}</text>'
    lanes = [("Sentinel-2 · 778 dates", 18), ("EnMAP · 224 bands", 66), ("Sub-metre captures", 114), ("Field carbon plots", 162)]
    for n, y in lanes:
        s += f'<text x="0" y="{y + 22}" font-size="21" font-weight="600" fill="{NAVY}">{n}</text>'
    s += f'<rect x="{X("2020-01-01"):.0f}" y="18" width="{X("2026-09-19") - X("2020-01-01"):.0f}" height="30" rx="8" fill="url(#gt)"/>'
    s += f'<defs><linearGradient id="gt"><stop offset="0" stop-color="#1E6FD9"/><stop offset="1" stop-color="#0EA5E9"/></linearGradient></defs>'
    s += f'<text x="{X("2020-03-01") + 6:.0f}" y="39" font-size="17" font-weight="600" fill="#fff">every ~5 days, Jan 2020 – Sep 2026, read in place (no downloads)</text>'
    for d in ("2022-11-01", "2025-04-14"):
        x = X(d); s += f'<path d="M{x:.0f} 66 l13 15 l-13 15 l-13 -15z" fill="#7C4DFF"/>'
    s += f'<text x="{X("2025-04-14") + 20:.0f}" y="88" font-size="17" fill="{MUTED}">Nov 2022 · Apr 2025</text>'
    for d in ("2016-08-13", "2018-09-19", "2019-10-19", "2020-05-24", "2021-06-08", "2022-03-28", "2023-02-22", "2023-11-14", "2025-01-06"):
        s += f'<circle cx="{X(d):.0f}" cy="129" r="10" fill="{CORAL}" stroke="#fff" stroke-width="2"/>'
    s += f'<rect x="{X("2013-01-15"):.0f}" y="162" width="{X("2014-03-01") - X("2013-01-15"):.0f}" height="30" rx="8" fill="#2E8B57"/>'
    s += f'<text x="{X("2014-03-01") + 10:.0f}" y="184" font-size="17" fill="{MUTED}">24 plots near the stands (Schile et al. 2016)</text></svg>'
    return s


def scenario_chart():
    rows = [("2027", 32), ("2028", 142), ("2029", 309)]
    s = '<svg width="430" height="290" viewBox="0 -40 430 290" font-family="IBM Plex Sans"><defs><linearGradient id="gr" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#1E6FD9"/><stop offset="1" stop-color="#0EA5E9"/></linearGradient></defs>'
    for i, (y, v) in enumerate(rows):
        h = v * 0.62; x = 30 + i * 135
        s += f'<rect x="{x}" y="{210 - h:.0f}" width="90" height="{h:.0f}" rx="10" fill="url(#gr)"/><text x="{x + 45}" y="{200 - h:.0f}" font-size="24" font-weight="700" fill="{NAVY}" text-anchor="middle">${v}k</text>'
        s += f'<text x="{x + 45}" y="240" font-size="20" fill="{MUTED}" text-anchor="middle">{y}</text>'
    return s + '</svg>'


def flow(steps, dark_bg=False):
    out = []
    for i, (ic, t1, t2) in enumerate(steps):
        out.append(f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;text-align:center;gap:12px">{icon(ic, 34)}'
                   f'<p class="t b" style="font-size:22px{";color:#fff" if dark_bg else ""}">{t1}</p><p class="s" style="font-size:19px{";color:#BFDFFF" if dark_bg else ""}">{t2}</p></div>')
        if i < len(steps) - 1:
            out.append(f'<div style="flex:none;padding-top:18px;font-size:34px;color:{CYAN}">&#10142;</div>')
    return '<div style="display:flex;gap:8px;align-items:flex-start">' + "".join(out) + "</div>"


S = {}
# 1 ---------------------------------------------------------------------------------------------------------------------
m, mh = stand_map(560, dark_bg=True)
S["cover"] = dark("cover", f"""
  <div style="position:absolute;left:110px;top:215px;width:1080px">
    <p class="mono" style="font-size:22px;letter-spacing:4px;text-transform:uppercase;color:#8FD3FF;font-weight:600">Arab Youth Space Hackathon 2026 &#183; Challenge 813</p>
    <h1 style="font-size:100px;white-space:nowrap;font-weight:700;line-height:1.02;margin:22px 0 18px;background:linear-gradient(90deg,#FFFFFF 0%,#CBEBFF 60%,#7FD3FF 100%);-webkit-background-clip:text;color:transparent">Blue Carbon Guardian</h1>
    <p style="font-size:34px;color:#D8EEFF;line-height:1.35">Tide-aware satellite monitoring for Gulf mangroves &#8212; from alert to evidence.</p>
    <div style="display:flex;gap:12px;margin-top:26px;flex-wrap:wrap">
      <span class="pill" style="background:rgba(255,255,255,.16);color:#fff;border-color:rgba(255,255,255,.5)">Team Blue Athar &#183; <span style="font-family:'IBM Plex Sans Arabic',sans-serif">&#1575;&#1604;&#1571;&#1579;&#1585; &#1575;&#1604;&#1571;&#1586;&#1585;&#1602;</span></span>
      <span class="pill" style="background:rgba(108,199,255,.16);color:#D8EEFF;border-color:rgba(108,199,255,.4)">Theme: Ecosystem Health, Biodiversity &amp; Blue Carbon</span></div>
    <div style="display:flex;gap:18px;margin-top:56px">
      {"".join(f'<div style="padding:20px 26px;border-radius:18px;background:linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.05));border:1px solid rgba(169,228,255,.35)"><p class="bigw" style="font-size:42px;white-space:nowrap">{a}</p><p style="font-size:20px;color:#BFDFFF;margin-top:8px">{b}</p></div>' for a, b in [("91 stands", "Abu Dhabi + Tarut Bay"), ("5 confirmed", "real conversions, 0.3&#8211;0.5 m"), ("73 % vs 13 %", "partial loss caught vs chance"), ("&#8776;1", "false alarm / stand-year")])}
    </div>
    <p style="font-size:26px;color:#BFDFFF;margin-top:64px">Nahla Nabil &#183; Bahrain</p>
  </div>
  <div style="position:absolute;right:90px;top:200px;padding:22px 26px;border-radius:24px;background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.03));border:1px solid rgba(169,228,255,.35)">
    <p class="mono" style="font-size:16px;letter-spacing:3px;color:#A9E4FF;margin-bottom:10px">LIVE MONITOR &#183; ABU DHABI PILOT</p>{m}
    <p style="font-size:18px;color:#D8EEFF;margin-top:8px"><span style="display:inline-block;width:14px;height:14px;border-radius:3px;background:{CORAL};margin-right:8px"></span>conversion confirmed on sub-metre imagery</p></div>""")

# 2 ---------------------------------------------------------------------------------------------------------------------
img = lambda f, st="": f'<img src="images/{f}" style="display:block;{st}">'
S["problem"] = light("problem", 2, "The problem", "Restoration is scaling faster than monitoring", f"""
<div class="row" style="gap:40px;flex:1">
  <div class="col" style="width:880px;gap:18px;justify-content:space-between">
    {"".join(f'<div class="card" style="display:flex;gap:26px;align-items:center;padding:22px 28px">{icon(i)}<div style="width:270px;flex:none"><p class="big" style="font-size:54px;white-space:nowrap">{a}</p></div><div><p class="t b">{b}</p><p class="s">{c}</p></div></div>' for i, a, b, c in [("leaf", "100 M", "mangroves pledged by the UAE by 2030", "COP26, 2021 &#183; Abu Dhabi Mangrove Initiative, 2022"), ("leaf", "100 M+", "mangroves pledged by Saudi Arabia by 2030", "Saudi Green Initiative"), ("file", "Feb 2026", "first GCC mangrove monitoring guide", "EAD + IUCN Mangrove Specialist Group")])}
    <div class="card dk" style="padding:24px 30px"><p class="lab" style="color:#8FD3FF">Today</p><p class="t w" style="margin-top:8px">Periodic field surveys and one-off studies; a 2025 regional review calls Gulf monitoring <b>&#8220;uneven&#8221;</b>. No standing alert for each stand, no independent check of carbon claims.</p></div>
  </div>
  <div class="card" style="flex:1;padding:20px 22px;display:flex;flex-direction:column;justify-content:space-between">
    <p class="lab" style="color:{CORAL}">This is happening now &#183; stand 5, Abu Dhabi</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px 14px;margin-top:12px">{"".join(f'<div style="position:relative">{img(f, "width:100%;height:232px;object-fit:cover;border-radius:12px")}<span style="position:absolute;left:10px;top:10px;background:{c};color:#fff;font-weight:700;font-size:17px;padding:4px 10px;border-radius:8px">{d}</span></div>' for f, d, c in [("s2_stand5_2021-11.png", "Nov 2021 &#183; intact", NAVY), ("s2_stand5_2022-10.png", "Oct 2022 &#183; works start, alert fires", CORAL), ("s2_stand5_2023-06.png", "Jun 2023 &#183; canals cut", NAVY), ("s2_stand5_2026-05.png", "May 2026 &#183; development", NAVY)])}</div>
    <p class="s" style="font-size:17px;margin-top:10px">Sentinel-2 true colour, contains modified Copernicus Sentinel data. Our alert began on 25 Oct 2022, during the works.</p>
    <div style="display:flex;gap:10px;margin-top:14px"><span class="pill" style="background:#E6F4EA;color:#2E7D32;border-color:#BFE3C6">SDG 13</span><span class="pill">SDG 14</span><span class="pill" style="background:#EEF8E6;color:#3D7A1F;border-color:#CBE8B5">SDG 15</span></div>
  </div>
</div>
<p class="s" style="font-size:16px;margin-top:16px">Sources: ead.gov.ae &#183; admangroves.ae &#183; spa.gov.sa &#183; Frontiers in Marine Science 2025 (doi:10.3389/fmars.2025.1695426)</p>""")

# 3 ---------------------------------------------------------------------------------------------------------------------
pers = [("shield", "Environment agencies", "EAD, MOCCAE, Saudi NCVC", "Which stands do we inspect this month? Is a protected stand intact?", "Periodic field surveys, one-off studies", "Monthly alert + 200 m cell map: inspect only the flagged cells"),
        ("leaf", "Planting &amp; carbon-project developers", "ADNOC, Red Sea Global, carbon developers", "Is the carbon stock we report still there?", "Field plots and drone surveys, campaign by campaign", "Condition + carbon stock with a range per stand, a site report for verification"),
        ("build", "Coastal developers &amp; regulators", "EIA consultants, permit offices", "Did construction stay outside the mangrove line?", "Comparing two dated images by eye", "An alert when works enter mangrove cells, with dated evidence")]
cards = "".join(f"""<div class="card" style="flex:1;display:flex;flex-direction:column;gap:14px;justify-content:space-between">
  <div style="display:flex;gap:18px;align-items:center">{icon(i)}<div><p class="t b" style="font-size:26px">{n}</p><p class="s" style="font-size:18px">{w}</p></div></div>
  <div style="background:{ICE};border-radius:14px;padding:16px 18px"><p class="lab" style="color:{BLUE}">Their decision</p><p class="t" style="margin-top:6px">{d}</p></div>
  <p class="s"><b style="color:{MUTED}">Today:</b> {t}</p>
  <div style="border-left:5px solid {CYAN};padding-left:14px"><p class="lab" style="color:{CYAN}">With Blue Carbon Guardian</p><p class="t b" style="margin-top:6px;font-size:22px;color:{NAVY}">{g}</p></div></div>""" for i, n, w, d, t, g in pers)
S["usecase"] = light("usecase", 3, "Business use case &amp; end users", "Who uses it, and for which decision", f"""
<div class="row" style="flex:1">{cards}</div>
<div class="card dk" style="margin-top:24px;padding:22px 34px">{flow([("sat", "New scene", "every ~5 days"), ("bell", "Alert", "~1 false alarm / stand-yr"), ("grid", "Cell map", "where to look"), ("search", "Inspection", "only flagged cells"), ("file", "Site report", "carbon at stake")], dark_bg=True)}</div>""")

# 4 ---------------------------------------------------------------------------------------------------------------------
m2, _ = stand_map(400, label=False)
srcs = [("sat", "Sentinel-2 L2A", "ESA / Copernicus", "time series, 10&#8211;20 m", "free &#183; 778 dates"), ("spectrum", "EnMAP", "DLR &#183; 224 bands", "independent hyperspectral check", "free &#183; 2 scenes"),
        ("layers", "ESA WorldCover 2021", "10 m land cover", "stand outlines", "CC BY 4.0"), ("leaf", "Field carbon plots", "Schile et al. 2016", "carbon density", "CC0 &#183; 24 plots"),
        ("search", "Sub-metre captures", "WorldView-2/3, Legion-1", "confirming conversions", "viewed only (Esri Wayback)")]
srcc = "".join(f'<div class="card" style="display:flex;gap:16px;align-items:center;padding:10px 20px">{icon(i, 28)}<div style="flex:1"><p class="t b" style="font-size:22px">{a}</p><p class="s" style="font-size:17px">{b} &#183; {c}</p></div><span class="pill" style="font-size:16px">{d}</span></div>' for i, a, b, c, d in srcs)
S["data"] = light("data", 4, "Data &amp; study area, incl. hyperspectral", "91 mangrove stands, six years of free imagery", f"""
<div class="row" style="gap:30px">
  <div class="card" style="width:470px;padding:16px 22px"><p class="lab" style="color:{BLUE}">Pilot: 25 stands &#183; 2,281 ha &#183; Abu Dhabi</p>{m2}
    <p class="s" style="font-size:17px">Outlines: WorldCover 2021 patches &#8805; 3 ha. Red: the five confirmed conversions. <b>+66 unseen stands</b> (Abu Dhabi N/W, Saudi Tarut Bay) test transfer.</p></div>
  <div class="col" style="flex:1;gap:12px">{srcc}</div>
</div>
<div class="card" style="margin-top:14px;padding:12px 24px">{data_timeline()}</div>""")

# 5 ---------------------------------------------------------------------------------------------------------------------
steps = [("grid", "1 &#183; Stands &amp; cells", "WorldCover 2021 patches &#8805; 3 ha, cut into 200 m cells; interior pixels only"),
         ("sat", "2 &#183; Sentinel-2 series", "778 dates 2020&#8211;26; cloud mask; NDVI, red edge, SWIR moisture, wetness"),
         ("wave", "3 &#183; Tide-aware model", "robust trend + season + tide terms, refitted every month"),
         ("bell", "4 &#183; Alert &amp; condition", "stand &#8804; &#8722;1.5&#963; OR any cell &#8804; &#8722;3.5&#963;; last 12 months vs 2020&#8211;21"),
         ("target", "5 &#183; Decision layer", "cell map, carbon at stake, dashboard, site reports")]
st = "".join(f'<div class="card" style="flex:1;display:flex;flex-direction:column;gap:18px;align-items:flex-start;justify-content:center;padding:34px 30px;{"background:linear-gradient(135deg,#06235A,#0B4A9E);border:none" if k == 4 else ""}">{icon(i)}<p class="t b" style="font-size:28px{";color:#fff" if k == 4 else ""}">{a}</p><p class="s" style="font-size:22px{";color:#BFDFFF" if k == 4 else ""}">{b}</p></div>'
             + ('' if k == 4 else f'<div style="flex:none;align-self:center;font-size:40px;color:{CYAN}">&#10142;</div>') for k, (i, a, b) in enumerate(steps))
chk = [("spectrum", "EnMAP hyperspectral", "same dates, r = 0.84&#8211;0.99"), ("search", "Sub-metre captures", "5 conversions confirmed"), ("chart", "Simulated losses", "every rate vs its chance rate"), ("map", "65 unseen stands", "0.79 false alarms / stand-yr")]
S["solution"] = light("solution", 5, "Approach &#183; workflow", "From satellite pixels to an inspection decision", f"""
<div style="display:flex;gap:12px;align-items:stretch;flex:1">{st}</div>
<div class="row" style="margin-top:24px;gap:24px">
  <div class="card" style="flex:1.25;padding:20px 26px"><p class="lab" style="color:{BLUE}">Checks built in, independent of the model</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px 26px;margin-top:14px">{"".join(f'<div style="display:flex;gap:14px;align-items:center">{icon(i, 26)}<div><p class="t b" style="font-size:21px">{a}</p><p class="s" style="font-size:17px">{b}</p></div></div>' for i, a, b in chk)}</div></div>
  <div class="card dk" style="flex:1;padding:22px 28px"><p class="lab" style="color:#8FD3FF">Problem statement</p>
    <p class="t w" style="margin-top:10px;font-size:23px">&#8220;We monitor mangrove condition and carbon stock in Abu Dhabi, 2020&#8211;2026, so that authorities and developers can decide where to inspect and verify carbon claims.&#8221;</p></div>
</div>""")

# 6 ---------------------------------------------------------------------------------------------------------------------
S["innovation"] = light("innovation", 6, "Technical innovation 1", "The tide looks like tree loss &#8212; until you correct for it", f"""
<div class="row" style="gap:34px;flex:1">
  <div class="card" style="padding:20px 24px;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{BLUE}">Why naive monitors fail on Gulf tidal flats</p>{tide_illustration()}
    <p class="s" style="font-size:18px">Illustration. Measured on our stands: index noise vs wetness, <b>r &#8776; &#8722;0.9</b>.</p></div>
  <div class="card" style="flex:1;padding:20px 26px;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{BLUE}">Date-to-date noise, 25 stands, 2020&#8211;2026</p>
    <div style="margin-top:12px">{bars_before_after()}</div></div>
</div>
<div class="card dk" style="margin-top:20px;padding:18px 30px;display:flex;gap:22px;align-items:center">{icon("wave", 30, bg="rgba(255,255,255,.15)")}
  <p class="t w" style="font-size:25px">We regress each index on trend, season <b>and tidal state</b> before flagging anything: <b>29&#8211;35 % less noise</b> on every index.</p></div>""")

# 7 ---------------------------------------------------------------------------------------------------------------------
S["cells"] = light("cells", 7, "Technical innovation 2", "A stand average hides partial loss. 200 m cells do not.", f"""
<div class="row" style="gap:30px;flex:1">
  <div class="card" style="width:1010px;padding:16px;display:flex;flex-direction:column;justify-content:center">{img("alert_story_2023-01.png", "width:100%;border-radius:14px")}
    <p class="s" style="font-size:17px;margin-top:8px">Stand 5, winter 2022&#8211;23 (real data): 200 m cells turn red while the stand average barely moves. Contains modified Copernicus Sentinel data.</p></div>
  <div class="col" style="flex:1;gap:16px;justify-content:space-between">
    <div class="card" style="padding:20px 24px"><p class="big">8 of 28</p><p class="t" style="margin-top:8px">cells of stand 9 in severe decline while its average reads <b>&#8220;stable&#8221;</b></p></div>
    <div class="card" style="padding:20px 24px"><p class="big">3 of 5</p><p class="t" style="margin-top:8px">real conversions found <b>only</b> by the cells (stands 12, 18, 6)</p></div>
    <div class="card dk" style="padding:18px 24px"><p class="lab" style="color:#8FD3FF">One alert rule</p>
      <div style="display:flex;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap"><span class="pill">stand &#8804; &#8722;1.5&#963;</span><b style="color:#8FD3FF;font-size:22px">OR</b><span class="pill">any cell &#8804; &#8722;3.5&#963;</span></div>
      <p class="s ws" style="margin-top:10px;font-size:18px">calibrated together: 0.96 false-alarm episodes per stand-year</p></div>
  </div>
</div>
<div class="card" style="margin-top:18px;padding:16px 28px;display:flex;gap:40px;align-items:center"><p class="t b" style="width:430px">Partial loss caught within 60 days (simulated)</p>
  {"".join(f'<div style="flex:1"><div style="height:24px;width:{v * 5.2}px;border-radius:8px;background:{c}"></div><p class="s" style="margin-top:6px"><b style="color:{NAVY}">{v} %</b> {n}</p></div>' for v, n, c in [(73, "stand + cells", "linear-gradient(90deg,#0A3D91,#0EA5E9)"), (25, "stand average alone", "#7FB6F5"), (13, "by chance", "#C9D3E3")])}</div>""")

# 8 ---------------------------------------------------------------------------------------------------------------------
feats = [("bell", "One alert", "stand average OR any 200 m cell, ~1 false alarm per stand-year"), ("grid", "Where to look", "a 200 m cell map for the inspector"),
         ("chart", "Condition", "last 12 months vs the stand's own 2020&#8211;21 baseline"), ("leaf", "Carbon at stake", "stock with a range, from field data"),
         ("file", "Site report", "one printable page per stand; every sentence traces back to a number")]
S["product"] = light("product", 8, "Example output &#183; the product", "From signal to decision, in one screen", f"""
<div class="row" style="gap:30px">
  <div style="width:1080px;border-radius:20px;overflow:hidden;box-shadow:0 24px 60px rgba(6,35,90,.25);border:1px solid #C3DDFF">
    <div style="background:#06235A;padding:10px 16px;display:flex;gap:8px;align-items:center"><span style="width:12px;height:12px;border-radius:50%;background:#FF5F57"></span><span style="width:12px;height:12px;border-radius:50%;background:#FEBC2E"></span><span style="width:12px;height:12px;border-radius:50%;background:#28C840"></span>
      <span class="mono" style="font-size:15px;color:#BFDFFF;margin-left:14px">dashboard/index.html &#183; Abu Dhabi pilot</span></div>
    {img("dashboard_full.png", "width:100%")}</div>
  <div class="col" style="flex:1;gap:14px;justify-content:space-between">{"".join(f'<div style="display:flex;gap:18px;align-items:flex-start">{icon(i, 30)}<div><p class="t b" style="font-size:27px">{a}</p><p class="s" style="font-size:21px">{b}</p></div></div>' for i, a, b in feats)}
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px"><span class="pill">dashboard</span><span class="pill">site reports</span><span class="pill">JSON alert API (concept)</span></div></div>
</div>""")

# 9 ---------------------------------------------------------------------------------------------------------------------
tiles = [("stand5_before_after_2021_2026.png", "Stand 5", "reclamation with finger canals"), ("stand9_before_after_2020_2026.png", "Stand 9", "canal development takes the south-east"),
         ("stand12_key_years.png", "Stand 12", "found only by the cells"), ("stand18_key_years.png", "Stand 18", "found only by the cells, 2025")]
tl = "".join(f'<div class="card" style="padding:12px;display:flex;flex-direction:column;gap:8px"><div style="flex:1;min-height:0;display:flex;align-items:center;justify-content:center;overflow:hidden;border-radius:10px;background:#F4F8FF">{img(f, "max-width:100%;max-height:230px")}</div><p class="s" style="font-size:18px"><b style="color:{NAVY}">{a}</b> &#183; {b}</p></div>' for f, a, b in tiles)
S["validation-real"] = light("validation-real", 9, "Validation 1 &#183; real events", "Five real conversions, confirmed on sub-metre imagery", f"""
<div class="row" style="gap:26px;flex:1">
  <div style="width:1000px;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:16px">{tl}</div>
  <div class="card" style="flex:1;padding:18px 22px;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{BLUE}">When did the alert start?</p>{gantt()}</div>
</div>
<div class="card dk" style="margin-top:18px;padding:16px 28px"><p class="t w" style="font-size:22px">Dated 0.3&#8211;0.5 m captures (WorldView-2/3, Legion-1) confirm all five, including stand 6 where a lagoon replaced part of the stand. At every site the alert began <b>between the last intact and the first disturbed capture</b>: detection of works as they happen, not advance warning.</p></div>""")

# 10 --------------------------------------------------------------------------------------------------------------------
S["hyperspectral"] = light("hyperspectral", 10, "Validation 2 &#183; hyperspectral (EnMAP)", "An independent check, and a material fingerprint", f"""
<div class="card" style="padding:16px 20px">{img("enmap_stand5_two_epochs.png", "width:100%")}</div>
<div class="row" style="margin-top:20px">
  {"".join(f'<div class="card" style="flex:1;display:flex;gap:20px;align-items:center">{icon(i)}<div><p class="big" style="font-size:50px">{a}</p><p class="s" style="margin-top:6px">{b}</p></div></div>' for i, a, b in [("check", "r = 0.84&#8211;0.99", "EnMAP vs our Sentinel-2 indices, same dates, 25 and 14 stands"), ("spectrum", "62 vs 26 ha", "stand 5 converted: EnMAP pixels vs our conservative Sentinel-2 flag"), ("target", "F1 0.74 vs 0.72", "full spectrum vs Sentinel-2-like bands as a classifier: no real gain, and we say so")])}
</div>
<p class="s" style="font-size:17px;margin-top:14px">Converted pixels change from a vegetation spectrum to a bright mineral-like one (sand and fill): reclamation, not dieback. Contains modified EnMAP data &#169; DLR 2022, 2025.</p>""")

# 11 --------------------------------------------------------------------------------------------------------------------
S["validation-sim"] = light("validation-sim", 11, "Validation 3 &#183; simulation and unseen stands", "Can we detect a loss? Tested against pure chance", f"""
<div class="row" style="gap:30px;flex:1">
  <div class="card" style="width:1080px;padding:22px 30px;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{BLUE}">Artificial loss injected into real stands with no known change</p>
    <p class="s" style="margin:8px 0 14px">A detection counts only if a <b>new</b> alert starts after the loss begins. The same test with <b>no</b> loss gives the chance rate. ~160&#8211;240 trials per row (&#177;7 points).</p>{sim_chart()}</div>
  <div class="col" style="flex:1;gap:18px;justify-content:space-between">
    <div class="card" style="padding:22px 26px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{MUTED}">Calibrated &#183; 25 pilot stands</p><p class="big" style="margin-top:8px">0.96</p><p class="s">false-alarm episodes per stand-year (117 stand-years)</p></div>
    <div class="card dk" style="padding:22px 26px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:#8FD3FF">Unseen &#183; 65 stands, thresholds fixed</p><p class="bigw" style="margin-top:8px">0.79</p><p class="s ws">per stand-year over 305 stand-years, incl. Saudi Tarut Bay</p></div>
  </div>
</div>
<div class="card" style="margin-top:18px;padding:14px 26px;display:flex;gap:18px;align-items:center;border-left:6px solid {AMBER}">{icon("alert", 26, bg="linear-gradient(135deg,#FFB020,#FF8A00)")}
  <p class="t" style="font-size:21px">We corrected our own first test: it counted alerts that were already running and had no chance baseline (it reported 58 % / 90 %). We withdrew it.</p></div>""")

# 12 --------------------------------------------------------------------------------------------------------------------
lim = [("clock", "Detection, not early warning", "Alerts fire as works happen. We never claim to see stress before it is visible."), ("pixel", "10 m pixels", "Patches under ~0.6 ha and young plantings are missed, Bahrain's small stands included."),
       ("search", "Imagery, not site visits", "Conversions confirmed on dated sub-metre captures, not yet on permits or field records."), ("chart", "Simulated losses", "Canopy-cover loss, not leaf stress; every rate next to its chance rate."),
       ("spectrum", "Hyperspectral", "EnMAP confirms our indices but was not a better classifier (F1 0.74 vs 0.72)."), ("leaf", "Carbon", "Area &#215; field density from four sites (2013&#8211;14): a stock with a range, never a sequestration rate.")]
S["limits"] = light("limits", 12, "Limitations", "Where it breaks &#8212; and what we do not claim", f"""
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;grid-template-rows:1fr 1fr;gap:22px;flex:1">{"".join(f'<div class="card" style="display:flex;flex-direction:column;gap:16px;padding:30px 32px;justify-content:center">{icon(i, bg="linear-gradient(135deg,#0A3D91,#2F80ED)")}<p class="t b" style="font-size:30px">{a}</p><p class="s" style="font-size:22px">{b}</p></div>' for i, a, b in lim)}</div>
<div class="card dk" style="margin-top:22px;padding:18px 30px"><p class="t w" style="font-size:23px"><b>Rule we kept:</b> no detection rate without its chance rate; no claim of advance warning, field verification or species discrimination.</p></div>""")

# 13 --------------------------------------------------------------------------------------------------------------------
S["carbon"] = light("carbon", 13, "Impact &#183; carbon", "Carbon stock, grounded in field measurements", f"""
<div class="row" style="gap:26px;flex:1">
  <div class="col" style="width:520px;gap:16px;justify-content:space-between">
    {"".join(f'<div class="card {c}" style="padding:20px 26px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="{k}">{a}</p><p class="s{w}" style="margin-top:8px">{b}</p></div>' for a, b, c, k, w in [("108 t C/ha", "local mean density (90 % CI 79&#8211;138), 24 plots at 4 sites", "", "big", ""), ("247 kt C", "pilot stock, 2,281 ha (90 % range 180&#8211;316)", "", "big", ""), ("&#8776; 907 kt CO&#8322;e", "pilot equivalent, median", "dk", "bigw", " ws")])}
  </div>
  <div class="card" style="width:430px;padding:22px 26px;display:flex;flex-direction:column"><p class="lab" style="color:{BLUE}">Where the carbon is</p>
    <div style="display:flex;gap:22px;align-items:flex-end;margin-top:16px;flex:1">
      <div style="width:130px;display:flex;flex-direction:column;border-radius:14px;overflow:hidden;height:560px">
        <div style="height:{19 / 108 * 560:.0f}px;background:#2E8B57;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:20px">19</div>
        <div style="flex:1;background:linear-gradient(180deg,#8D6E4A,#5B4632);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:30px">89</div></div>
      <div class="col" style="gap:14px"><p class="t"><b style="color:#2E8B57">Trees</b>: 19 t C/ha</p><p class="t"><b style="color:#7A5A3A">Soil</b> (top 1 m): 89 t C/ha</p>
        <p class="big" style="font-size:52px">82 %</p><p class="s">of the stock is in the soil: losing the stand releases what is underneath</p></div></div></div>
  <div class="col" style="flex:1;gap:16px;justify-content:space-between">
    <div class="card" style="padding:26px 28px;flex:1;display:flex;flex-direction:column;justify-content:center"><p class="lab" style="color:{CORAL}">Stand 5 conversion</p><p class="big" style="font-size:48px;margin-top:8px">2.8&#8211;6.7 kt C</p><p class="s">stock on the 26&#8211;62 ha converted (two methods); about USD 0.28&#8211;0.66 M at USD 27/t CO&#8322;e, illustration only</p></div>
    <div class="card" style="padding:26px 28px;border-left:6px solid {AMBER};flex:1;display:flex;flex-direction:column;justify-content:center"><p class="t b">Tested, and too weak</p><p class="s" style="margin-top:6px">Sentinel-2 indices vs field tree carbon (95 plots): best &#961; = 0.38. So carbon is <b>area &#215; field density</b>, not imagery biomass.</p></div>
  </div>
</div>""")

# 14 --------------------------------------------------------------------------------------------------------------------
tiers = [("Monitor", "$12k", "per site / year (&#8776; $5 / ha)", "alert, cell map, condition, carbon, monthly reports"), ("Evidence", "$25k", "per site / year", "+ sub-metre check of every alert, audit pack"), ("Development watch", "$8k", "per project / year", "for coastal developers and EIA consultants")]
S["business"] = light("business", 14, "Business viability", "A monitoring service with honest unit economics", f"""
<div class="row" style="gap:22px">
  {"".join(f'<div class="card{" dk" if k == 0 else ""}" style="flex:1;padding:22px 26px"><p class="lab" style="color:{"#8FD3FF" if k == 0 else BLUE}">{a}</p><p class="{"bigw" if k == 0 else "big"}" style="font-size:58px;margin-top:10px">{b}</p><p class="s{" ws" if k == 0 else ""}">{c}</p><p class="t{" w" if k == 0 else ""}" style="margin-top:12px;font-size:21px">{d}</p></div>' for k, (a, b, c, d) in enumerate(tiers))}
  <div class="card" style="flex:1.1;padding:22px 26px"><p class="lab" style="color:{BLUE}">Cost to serve &#8776; $3.3k / site / yr</p>
    <div style="display:flex;height:34px;border-radius:9px;overflow:hidden;margin-top:16px"><div style="width:2%;background:#0EA5E9"></div><div style="width:20%;background:#2F80ED"></div><div style="width:78%;background:#0A3D91"></div></div>
    <p class="s" style="margin-top:12px;font-size:18px"><b style="color:#0EA5E9">Compute</b> &lt; $5 (measured) &#183; <b style="color:#2F80ED">VHR on alert</b> $500&#8211;750 &#183; <b style="color:#0A3D91">Analyst</b> $2k (assumption)</p></div>
</div>
<div class="row" style="gap:22px;margin-top:20px;flex:1">
  <div class="card" style="width:520px;padding:18px 24px"><p class="lab" style="color:{BLUE}">Revenue scenario (hypothesis)</p>{scenario_chart()}</div>
  <div class="card" style="flex:1;padding:22px 26px"><p class="t b" style="font-size:26px">Customers</p><p class="s" style="margin-top:8px;font-size:22px">Agencies (EAD, MOCCAE, NCVC) &#183; planting programmes: ADNOC (10 M), Red Sea Global (50 M) &#183; carbon developers &#183; coastal developers and EIA consultants</p>
    <p class="t b" style="margin-top:20px;font-size:26px">Competition</p><p class="s" style="margin-top:8px;font-size:22px">Global Mangrove Watch: free monthly loss alerts (Gulf coverage not confirmed). We are complementary: tide-aware, calibrated, stand + cell, carbon and reports.</p></div>
  <div class="card dk" style="flex:1;padding:22px 26px"><p class="lab" style="color:#8FD3FF">The honest market</p><p class="t w" style="margin-top:14px;font-size:27px;line-height:1.5">Gulf + Red Sea &#8776; 16 sites &#8594; $0.2&#8211;0.4 M / yr: a niche. The real potential: a <b>national MRV contract</b>, a monitoring layer on <b>gIQ</b>, licensing.</p></div>
</div>
<p class="s" style="font-size:16px;margin-top:12px">Prices and analyst time are hypotheses for a pilot to test. All 13 sources: docs/business_plan_draft.md.</p>""")

# 15 --------------------------------------------------------------------------------------------------------------------
ph = [("check", "Now &#183; PoC", "Oct 2026", ["Stand + 200 m cell monitor", "dashboard &amp; site reports", "field-grounded carbon", "5 conversions confirmed", "EnMAP check", "0.79 false alarms on 65 unseen stands"], True),
      ("flag", "Incubation", "Oct 2026 &#8211; Jan 2027", ["Satellite 813 in the spectral step", "deployment on gIQ", "a pilot customer", "match alerts to permits &amp; site records", "more EnMAP dates per season"], False),
      ("target", "Scale", "2027 +", ["Saudi Arabia (Gulf &amp; Red Sea) and Bahrain", "very-high-resolution data for small stands", "national MRV contract", "licensing to platforms"], False)]
phc = ""
for k, (i, a, d, items, now) in enumerate(ph):
    phc += (f'<div class="card{" dk" if now else ""}" style="flex:1;padding:24px 28px;position:relative"><div style="display:flex;gap:16px;align-items:center">{icon(i)}<div><p class="t b" style="font-size:28px{";color:#fff" if now else ""}">{a}</p><p class="lab" style="color:{"#8FD3FF" if now else BLUE}">{d}</p></div></div>'
            f'<div class="col" style="gap:10px;margin-top:18px">{"".join(f"<p class={chr(34)}t{chr(34)} style={chr(34)}font-size:25px{";color:#fff" if now else ""}{chr(34)}>&#8226; {x}</p>" for x in items)}</div></div>')
    if k < 2:
        phc += f'<div style="flex:none;align-self:center;font-size:44px;color:{CYAN}">&#10142;</div>'
S["roadmap"] = light("roadmap", 15, "Next steps", "From proof of concept to a national monitoring layer", f"""
<div style="display:flex;gap:14px;align-items:stretch;flex:1">{phc}</div>
<div class="card" style="margin-top:22px;padding:18px 28px;border-left:6px solid {BLUE}"><p class="t b">Two limits we are designing around, on purpose</p>
  <p class="s" style="margin-top:6px">Bahrain's own stands are too small for 10&#8211;30 m pixels (a case for VHR at incubation) &#183; our five events are confirmed on dated imagery, not yet on site records (the first pilot task).</p></div>""")

# 16 --------------------------------------------------------------------------------------------------------------------
S["team"] = dark("team", f"""
  <div style="position:absolute;left:110px;top:200px;width:1700px">
    <p class="mono" style="font-size:22px;letter-spacing:4px;color:#8FD3FF;font-weight:600">TEAM BLUE ATHAR &#183; <span style="font-family:'IBM Plex Sans Arabic',sans-serif;letter-spacing:0;word-spacing:8px;font-size:26px">&#1575;&#1604;&#1571;&#1579;&#1585;&nbsp;&#1575;&#1604;&#1571;&#1586;&#1585;&#1602;</span></p>
    <h2 style="font-size:84px;font-weight:700;line-height:1.08;margin-top:24px;background:linear-gradient(90deg,#FFFFFF,#CBEBFF 60%,#7FD3FF);-webkit-background-clip:text;color:transparent">Every lost mangrove leaves a trace.<br>We find it from space.</h2>
    <div style="display:flex;gap:26px;margin-top:60px">
      <div style="flex:1;padding:28px 32px;border-radius:22px;background:linear-gradient(135deg,rgba(255,255,255,.14),rgba(255,255,255,.04));border:1px solid rgba(169,228,255,.35)">
        <p class="lab" style="color:#8FD3FF">Built end to end by one engineer</p><p style="font-size:40px;font-weight:700;margin-top:12px">Nahla Nabil</p>
        <p style="font-size:22px;color:#D8EEFF;margin-top:10px;line-height:1.45">Bahrain &#183; idea, satellite pipeline, tide-aware model, validation, dashboard, business case. AI/LLM engineer; NASA Space Apps local lead.</p></div>
      <div style="flex:1;padding:28px 32px;border-radius:22px;background:linear-gradient(135deg,rgba(14,165,233,.35),rgba(30,111,217,.25));border:1px solid rgba(169,228,255,.45)">
        <p class="lab" style="color:#A9E4FF">What we are asking for</p>
        <p style="font-size:25px;color:#fff;margin-top:14px;line-height:1.45">Mentor feedback on hyperspectral reading of Gulf mangroves and sabkha vegetation, and a path into incubation to validate with a <b>real restoration partner</b>.</p></div>
    </div>
    <p class="mono" style="font-size:22px;color:#BFDFFF;margin-top:44px">nahla-nabil.github.io/blue-carbon-guardian &#183; github.com/Nahla-Nabil/blue-carbon-guardian</p>
  </div>""")

for sid in ORDER:
    (SL / f"{sid}.html").write_text(S[sid], encoding="utf-8")
print("wrote", len(ORDER), "slides")
