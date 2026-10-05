"""README 'alert story', step 2 (render): an animated GIF of stand 5 from 2022 to 2026: real Sentinel-2 chips, the 200 m cells coloured by their alert
state, and the stand-average / worst-cell alert scores drawn as the time runs. Every number comes from video/build/story/story.json (step 1).
Output: docs/assets/alert_story.gif. Run from the repository root: python scripts/make_alert_story.py   (needs Playwright + Chrome, and ffmpeg)
"""
import json, pathlib, subprocess, shutil
from playwright.sync_api import sync_playwright

B = pathlib.Path("video/build/story"); S = json.load(open(B / "story.json"))
FPS, MAIN, HOLD = 12, 11.0, 3.0                     # seconds of timeline, seconds of hold at the end
W, H = 1100, 520

HTML = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>*{margin:0;box-sizing:border-box} body{width:%(W)dpx;height:%(H)dpx;overflow:hidden;font-family:'IBM Plex Sans',sans-serif;color:#fff;
background:radial-gradient(600px 400px at 85%% 10%%,rgba(76,169,255,.30),transparent 70%%),linear-gradient(120deg,#030B26 0%%,#06235A 50%%,#0B4A9E 100%%)}
.mono{font-family:'IBM Plex Mono',monospace;letter-spacing:2px;text-transform:uppercase}
#map{position:absolute;left:28px;top:28px;width:440px;height:464px;border-radius:14px;overflow:hidden;border:1px solid rgba(169,228,255,.35);background:#06235A}
#map img{position:absolute;left:0;top:0;width:100%%;height:100%%;object-fit:cover}
#cells{position:absolute;left:0;top:0;width:100%%;height:100%%}
#date{position:absolute;left:14px;top:12px;padding:5px 12px;border-radius:8px;background:rgba(3,11,38,.75);font-size:20px;font-weight:700}
#src{position:absolute;left:14px;bottom:10px;font-size:11px;color:#CFE6FF;background:rgba(3,11,38,.6);padding:3px 8px;border-radius:6px}
#leg{position:absolute;right:12px;bottom:10px;font-size:12px;background:rgba(3,11,38,.7);padding:5px 9px;border-radius:6px;line-height:1.5}
.sw{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px;vertical-align:-1px}
#pill{position:absolute;right:14px;top:12px;padding:5px 12px;border-radius:999px;font-size:14px;font-weight:700}
#right{position:absolute;left:500px;top:28px;width:572px}
#cap{position:absolute;left:500px;top:404px;width:572px;height:88px;border-radius:12px;padding:12px 16px;
background:linear-gradient(135deg,rgba(255,255,255,.13),rgba(255,255,255,.04));border:1px solid rgba(169,228,255,.35);font-size:19px;line-height:1.35}
#cap b{color:#A9E4FF}
</style>
<div id="map"><img id="i0"><img id="i1"><svg id="cells"></svg><div id="date"></div><div id="pill"></div>
<div id="src">Sentinel-2 true colour · stand 5, Abu Dhabi</div>
<div id="leg"><span class="sw" style="background:#FF4D6D"></span>cell alert ≤ −3.5σ<br><span class="sw" style="background:#FFB020"></span>cell below −1.5σ</div></div>
<div id="right">
 <div class="mono" style="font-size:14px;color:#8FD3FF">Blue Carbon Guardian · real data, stand 5</div>
 <div style="font-size:30px;font-weight:700;margin:4px 0 2px">Watch the alert fire</div>
 <div style="font-size:15px;color:#BFDFFF">Tide-aware alert score, 2022 → 2026 (lower = further below expected)</div>
 <svg id="chart" width="572" height="270" style="margin-top:8px"></svg>
</div>
<div id="cap"></div>
<script>
const S = %(S)s, MAIN = %(MAIN)s, F = S.frames, N = F.length;
const ms = d => new Date(d + "T00:00:00Z").getTime();
const T0 = ms("2022-01-01"), T1 = ms("2026-09-15");
const CW = 572, CH = 270, L = 44, R = 10, TP = 10, BT = 26, YMIN = -12, YMAX = 4;
const X = t => L + (t - T0) / (T1 - T0) * (CW - L - R), Y = z => TP + (YMAX - Math.max(YMIN, Math.min(YMAX, z))) / (YMAX - YMIN) * (CH - TP - BT);
const eps = S.episodes.map(([a, b]) => [ms(a), ms(b)]);
const VHR = [["2022-03-28", "sub-metre: intact"], ["2023-02-22", "sub-metre: works"]];
const BEATS = [
 ["2022-01-01", "Every ~5 days the model checks each <b>200 m cell</b> against what tide, season and trend predict."],
 ["2022-05-01", "May 2022: a short stand-level alert, nothing visible on the ground (budget: about <b>1 false alarm per stand-year</b>)."],
 ["2022-10-20", "<b>25 Oct 2022: alert fires.</b> Cells drop below −3.5σ and stay there."],
 ["2023-02-10", "Feb 2023: sub-metre imagery shows works. The alert began between the last <b>intact</b> and first <b>disturbed</b> capture."],
 ["2023-06-01", "Mangrove fringe replaced by reclamation and canals. <b>26–62 ha</b> converted (Sentinel-2 and EnMAP estimates)."],
 ["2024-06-01", "Evidence for the regulator: <b>≈2.8–6.7 kt C</b> of stock in the converted area · cell map shows <b>where</b> to inspect."]];
const scale = 440 / S.size[0], mapH = S.size[1] * scale, off = (464 - mapH) / 2;
const cellsSvg = document.getElementById("cells");
cellsSvg.innerHTML = S.ids.map((c, k) => { const b = S.cellbox[c];
  return `<rect id="c${k}" x="${b[0]*scale}" y="${b[1]*scale+off}" width="${(b[2]-b[0])*scale}" height="${(b[3]-b[1])*scale}" rx="2" stroke-width="1.2"/>`; }).join("");
document.querySelectorAll("#map img").forEach(i => { i.style.height = mapH + "px"; i.style.top = off + "px"; i.style.objectFit = "fill"; });
const ch = document.getElementById("chart");
let grid = "";
for (let z = -12; z <= 4; z += 4) grid += `<line x1="${L}" x2="${CW-R}" y1="${Y(z)}" y2="${Y(z)}" stroke="rgba(255,255,255,.08)"/><text x="${L-8}" y="${Y(z)+4}" font-size="11" fill="#9CC8F0" text-anchor="end">${z}σ</text>`;
for (let y = 2022; y <= 2026; y++) grid += `<text x="${X(ms(y+"-01-01"))}" y="${CH-6}" font-size="12" fill="#9CC8F0" text-anchor="middle">${y}</text>`;
function render(t) {
  const p = Math.min(1, t / MAIN), now = T0 + p * (T1 - T0);
  let k = 0; while (k < N - 1 && ms(F[k + 1].date) <= now) k++;
  const fr = F[k];
  // satellite chip: the latest chip not after 'now', cross-fading into the next one
  const cd = S.chips.map(ms); let j = 0; while (j < cd.length - 1 && cd[j + 1] <= now) j++;
  const i0 = document.getElementById("i0"), i1 = document.getElementById("i1");
  i0.src = "chip_" + S.chips[j] + ".png";
  if (j < cd.length - 1) { const a = Math.max(0, Math.min(1, (now - (cd[j + 1] - 40*864e5)) / (40*864e5))); i1.src = "chip_" + S.chips[j + 1] + ".png"; i1.style.opacity = a; }
  else i1.style.opacity = 0;
  fr.cells.forEach((z, c) => { const e = document.getElementById("c" + c);
    if (z <= -S.cell_thr) { e.setAttribute("fill", "rgba(255,77,109,.55)"); e.setAttribute("stroke", "#FF4D6D"); }
    else if (z <= -S.stand_thr) { e.setAttribute("fill", "rgba(255,176,32,.35)"); e.setAttribute("stroke", "#FFB020"); }
    else { e.setAttribute("fill", "rgba(127,211,255,.06)"); e.setAttribute("stroke", "rgba(220,240,255,.55)"); } });
  document.getElementById("date").textContent = new Date(now).toLocaleDateString("en-GB", {month: "short", year: "numeric", timeZone: "UTC"});
  const pill = document.getElementById("pill");
  if (fr.alert) { pill.textContent = "● ALERT"; pill.style.background = "#FF4D6D"; pill.style.boxShadow = `0 0 ${10 + 10*Math.abs(Math.sin(t*5))}px #FF4D6D`; }
  else { pill.textContent = "● MONITORING"; pill.style.background = "#1E6FD9"; pill.style.boxShadow = "none"; }
  // chart
  let s = grid;
  eps.forEach(([a, b]) => { if (a < now) s += `<rect x="${X(a)}" y="${TP}" width="${Math.max(2, X(Math.min(b, now)) - X(a))}" height="${CH-TP-BT}" fill="rgba(255,77,109,.16)"/>`; });
  VHR.forEach(([d, lab], q) => { if (ms(d) < now) s += `<line x1="${X(ms(d))}" x2="${X(ms(d))}" y1="${TP}" y2="${CH-BT}" stroke="#A9E4FF" stroke-dasharray="3 3"/>
     <text x="${X(ms(d))+5}" y="${TP+14+q*16}" font-size="11" fill="#A9E4FF">${lab}</text>`; });
  [[S.stand_thr, "#7FD3FF", "stand −1.5σ"], [S.cell_thr, "#FF8FA3", "cell −3.5σ"]].forEach(([v, c, lab]) =>
    s += `<line x1="${L}" x2="${CW-R}" y1="${Y(-v)}" y2="${Y(-v)}" stroke="${c}" stroke-dasharray="6 4" opacity=".8"/><text x="${CW-R-4}" y="${Y(-v)-5}" font-size="11" fill="${c}" text-anchor="end">${lab}</text>`);
  const line = (key, col, w) => { const pts = F.slice(0, k + 1).map(f => `${X(ms(f.date)).toFixed(1)},${Y(f[key]).toFixed(1)}`).join(" ");
    return `<polyline points="${pts}" fill="none" stroke="${col}" stroke-width="${w}" stroke-linejoin="round"/>
            <circle cx="${X(ms(fr.date))}" cy="${Y(fr[key])}" r="4.5" fill="${col}"/>`; };
  s += line("worst", "#FF6B85", 2.2) + line("stand", "#7FD3FF", 2.6);
  s += `<text x="${CW-R-262}" y="${TP+12}" font-size="12" fill="#7FD3FF">━ stand average</text><text x="${CW-R-140}" y="${TP+12}" font-size="12" fill="#FF6B85">━ worst 200 m cell</text>`;
  ch.innerHTML = s;
  let b = 0; BEATS.forEach(([d], q) => { if (ms(d) <= now) b = q; });
  document.getElementById("cap").innerHTML = BEATS[b][1];
}
window.pre = S.chips.map(c => { const im = new Image(); im.src = "chip_" + c + ".png"; return im; });
window.render = render; render(0);
</script>"""

page = B / "story.html"
page.write_text(HTML % dict(W=W, H=H, S=json.dumps(S), MAIN=MAIN), encoding="utf-8")
frames = B / "frames"; shutil.rmtree(frames, ignore_errors=True); frames.mkdir()
n = int((MAIN + HOLD) * FPS)
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_page(viewport={"width": W, "height": H}); pg.goto(page.resolve().as_uri()); pg.wait_for_timeout(2000)
    for i in range(n):
        pg.evaluate(f"window.render({i / FPS})"); pg.wait_for_timeout(15)
        pg.screenshot(path=str(frames / f"f{i:04d}.png"))
    b.close()
out = "docs/assets/alert_story.gif"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(frames / "f%04d.png"), "-filter_complex",
                "[0:v]scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                "-loop", "0", out], check=True)
print(out, round(pathlib.Path(out).stat().st_size / 1e6, 2), "MB,", n, "frames")
