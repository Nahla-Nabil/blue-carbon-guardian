"""Videos for the PowerPoint deck (deck_pptx/build/media/*.mp4 + poster frames *.png):
  cover_scan   8 s seamless loop: a satellite scan line sweeps the 25 pilot stands; the five confirmed conversions ping as it passes.
  website      ~20 s screen recording of the live website (monitor -> 200 m cells -> stand 9), with a visible cursor and click ripples.
  alert_story  docs/assets/alert_story.gif (real stand-5 data) re-encoded as H.264.
  demo         video/build/demo_video_github.mp4 (720p version of docs/demo_video.mp4) for the backup slide.
Run from the repository root: python deck_pptx/media.py   (needs ffmpeg on PATH and playwright)
"""
import json, math, pathlib, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "deck_pptx" / "build" / "media"; OUT.mkdir(parents=True, exist_ok=True)
FONT = lambda size, bold=True: ImageFont.truetype("C:/Windows/Fonts/" + ("seguisb.ttf" if bold else "segoeui.ttf"), size)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def poster(mp4, t, png):
    ffmpeg("-ss", str(t), "-i", str(mp4), "-frames:v", "1", str(png))


# ---------------------------------------------------------------- cover scan
def cover_scan(W=1280, fps=30, secs=8):
    gj = json.load(open(ROOT / "analysis/data/stands.geojson"))
    rings = lambda f: [r for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]) for r in poly]
    pts = [c for f in gj["features"] for r in rings(f) for c in r]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    pad = 70; mw = W - 2 * pad; mh = int(mw * (y1 - y0) / ((x1 - x0) * 0.911)); H = mh + 2 * pad + 40; H += H % 2
    pj = lambda c: (pad + (c[0] - x0) / (x1 - x0) * mw, pad + 30 + (y1 - c[1]) / (y1 - y0) * mh)
    conv = {5, 6, 9, 12, 18}
    S = 2
    def layer(hot):
        im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        for f in gj["features"]:
            if (f["properties"]["stand"] in conv) == hot:
                for r in rings(f):
                    dr.polygon([(pj(c)[0] * S, pj(c)[1] * S) for c in r], fill=(255, 255, 255, 255))
        return np.asarray(im.resize((W, H), Image.LANCZOS))[..., 3].astype(np.float32) / 255
    normal, hot = layer(False), layer(True)
    edge = lambda m: np.clip(np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES)).astype(np.float32) / 255 * 2, 0, 1)
    en, eh = edge(normal), edge(hot)
    glow = lambda m, r: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255
    gn, gh = glow(normal, 10), glow(hot, 14)
    cent = {}
    for f in gj["features"]:
        k = f["properties"]["stand"]
        if k in conv:
            r = rings(f)[0]; cent[k] = (sum(pj(c)[0] for c in r) / len(r), sum(pj(c)[1] for c in r) / len(r))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32)
    base[:] = np.array([6, 18, 38]) * (1 - yy / H)[..., None] + np.array([10, 36, 78]) * (yy / H)[..., None]
    grid = ((xx % 64) < 1.2) | ((yy % 64) < 1.2); base[grid] += 9
    BLUE, BLUE_L, CORAL = np.array([120, 160, 210]), np.array([196, 214, 236]), np.array([222, 151, 161])
    n = fps * secs; trail = 260; frames = OUT / "_scan"; shutil.rmtree(frames, ignore_errors=True); frames.mkdir()
    f_hud, f_small, f_lab = FONT(26), FONT(20, False), FONT(22)
    for i in range(n):
        t = i / n
        sx = -trail + t * (W + 2 * trail)                       # scan line x
        lit = np.clip(1 - (sx - xx) / trail, 0, 1) * (xx <= sx)  # trail behind the line
        lit = lit ** 1.6
        img = base.copy()
        a_n = normal * (0.42 + 0.58 * lit); a_h = hot * (0.55 + 0.45 * lit)
        img += gn[..., None] * BLUE * 0.35 * (0.4 + lit[..., None])
        img = img * (1 - a_n[..., None]) + BLUE * a_n[..., None]
        img += gh[..., None] * CORAL * 0.45
        img = img * (1 - a_h[..., None]) + CORAL * a_h[..., None]
        img = np.maximum(img, (en * (0.5 + 0.5 * lit))[..., None] * BLUE_L)
        img = np.maximum(img, eh[..., None] * np.array([240, 205, 210]))
        beam = np.exp(-((xx - sx) / 3.0) ** 2); halo = np.exp(-((xx - sx) / 40.0) ** 2) * 0.35
        img += (beam + halo)[..., None] * np.array([170, 200, 232])
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im, "RGBA")
        for k, (cx, cy) in cent.items():                         # ping rings after the beam passes
            age = (sx - cx) / (W + 2 * trail) * secs
            if 0 <= age < 2.2:
                for j in range(2):
                    a2 = age - j * 0.45
                    if 0 <= a2 < 1.6:
                        r = 14 + a2 * 70; al = int(220 * (1 - a2 / 1.6))
                        dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(230, 170, 178, al), width=4)
            dr.ellipse([cx - 19, cy - 19, cx + 19, cy + 19], fill=(255, 255, 255, 240))
            dr.text((cx, cy), str(k), font=f_lab, fill=(8, 26, 46, 255), anchor="mm")
        dr.text((pad - 30, 26), "SENTINEL-2  ·  LIVE SCAN  ·  ABU DHABI PILOT", font=f_hud, fill=(196, 214, 236, 255))
        dot = 255 if (i // 15) % 2 == 0 else 90
        dr.ellipse([W - pad - 10, 34, W - pad + 4, 48], fill=(222, 151, 161, dot))
        dr.text((W - pad - 18, 41), "REC", font=f_small, fill=(255, 180, 190, 255), anchor="rm")
        dr.text((pad - 30, H - 34), "25 stands · 2,281 ha   ·   coral = 5 conversions confirmed on sub-metre imagery", font=f_small, fill=(160, 190, 225, 255), anchor="lm")
        im.save(frames / f"f{i:04d}.png")
    mp4 = OUT / "cover_scan.mp4"
    ffmpeg("-framerate", str(fps), "-i", str(frames / "f%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(mp4))
    poster(mp4, 5.2, OUT / "cover_scan.png")
    shutil.rmtree(frames)
    print("cover_scan", W, H)


# ---------------------------------------------------------------- website recording
CURSOR_JS = """
(() => { const c = document.createElement('div');
  c.style.cssText = 'position:fixed;left:0;top:0;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:rgba(77,163,255,.35);border:3px solid #1E6FD9;z-index:99999;pointer-events:none;transition:transform .08s';
  document.body.appendChild(c);
  document.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; });
  document.addEventListener('mousedown', e => { c.style.transform = 'scale(.7)';
    const r = document.createElement('div'); r.style.cssText = `position:fixed;left:${e.clientX}px;top:${e.clientY}px;width:20px;height:20px;margin:-10px 0 0 -10px;border-radius:50%;border:3px solid #1E6FD9;z-index:99998;pointer-events:none;transition:all .6s ease-out;opacity:1`;
    document.body.appendChild(r); requestAnimationFrame(() => { r.style.transform = 'scale(4)'; r.style.opacity = '0'; }); setTimeout(() => r.remove(), 700); });
  document.addEventListener('mouseup', () => c.style.transform = 'scale(1)'); })();
"""


def website(url="https://nahla-nabil.github.io/blue-carbon-guardian/"):
    from playwright.sync_api import sync_playwright
    vdir = OUT / "_rec"; shutil.rmtree(vdir, ignore_errors=True)
    with sync_playwright() as p:
        try: b = p.chromium.launch(channel="chrome")
        except Exception: b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1600, "height": 1000}, record_video_dir=str(vdir), record_video_size={"width": 1600, "height": 1000})
        pg = ctx.new_page()
        pg.goto(url, wait_until="networkidle"); pg.evaluate(CURSOR_JS); pg.mouse.move(800, 500)
        pg.wait_for_timeout(2200)
        def glide(sel, steps=30):
            bb = pg.locator(sel).first.bounding_box(); pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2, steps=steps)
        def scroll_to(sel, off=0):
            pg.evaluate(f"(() => {{ const e = document.querySelector('{sel}'); window.scrollTo({{top: e.getBoundingClientRect().top + window.scrollY - {off}, behavior: 'smooth'}}); }})()")
            pg.wait_for_timeout(1500)
        scroll_to("#monitor", 10); pg.wait_for_timeout(1800)
        glide("#bCells"); pg.wait_for_timeout(300); pg.mouse.down(); pg.mouse.up(); pg.click("#bCells"); pg.wait_for_timeout(2600)
        scroll_to("#tbl", 160); glide('#tbl tbody tr[data-k="9"]'); pg.wait_for_timeout(300)
        pg.mouse.down(); pg.mouse.up(); pg.click('#tbl tbody tr[data-k="9"]'); pg.wait_for_timeout(900)
        scroll_to("#monitor", 10); pg.wait_for_timeout(1200)
        pg.mouse.move(1150, 560, steps=40); pg.wait_for_timeout(1400); pg.mouse.move(1180, 800, steps=40); pg.wait_for_timeout(2600)
        ctx.close(); b.close()
    webm = next(vdir.glob("*.webm")); mp4 = OUT / "website.mp4"
    ffmpeg("-ss", "1.2", "-i", str(webm), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-r", "30", "-movflags", "+faststart", "-an", str(mp4))
    poster(mp4, 18.0, OUT / "website.png"); shutil.rmtree(vdir)
    print("website ok")


def alert_story():
    mp4 = OUT / "alert_story.mp4"
    ffmpeg("-i", str(ROOT / "docs/assets/alert_story.gif"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", str(mp4))
    poster(mp4, 6.0, OUT / "alert_story.png"); print("alert_story ok")


def demo():
    src = ROOT / "video/build/demo_video_github.mp4"
    if not src.exists(): src = ROOT / "docs/demo_video.mp4"
    shutil.copy(src, OUT / "demo.mp4"); poster(OUT / "demo.mp4", 4.0, OUT / "demo.png"); print("demo ok")


if __name__ == "__main__":
    cover_scan(); website(); alert_story(); demo()
