"""Design assets for the PowerPoint deck (deck_pptx/build.js): dark ocean backgrounds, soft glow sprites (moved between slides by Morph),
a dark-theme map of the 25 pilot stands with the five confirmed conversions in coral, and a screenshot of the live website's monitor.
Run from the repository root: python deck_pptx/assets.py   -> deck_pptx/build/assets/*.png
"""
import json, math, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "deck_pptx" / "build" / "assets"; OUT.mkdir(parents=True, exist_ok=True)
W, H = 2667, 1500  # 13.333 x 7.5 in at 200 dpi


def background(name, glow_xy, seed):
    """Deep-ocean gradient, faint bathymetry contour lines and a vignette."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    t = (x / W * 0.55 + y / H * 0.45)
    top, bot = np.array([5, 14, 26]), np.array([9, 33, 58])
    img = top[None, None, :] * (1 - t[..., None]) + bot[None, None, :] * t[..., None]
    gx, gy = glow_xy
    d = np.sqrt((x - gx * W) ** 2 + (y - gy * H) ** 2) / W
    img += np.array([25, 75, 165])[None, None, :] * np.exp(-(d / 0.33) ** 2)[..., None] * 0.55
    rng = np.random.default_rng(seed)
    field = np.zeros((H, W), np.float32)
    for _ in range(5):  # smooth pseudo-terrain for contour lines
        fx, fy, ph = rng.uniform(1.2, 3.2), rng.uniform(0.8, 2.4), rng.uniform(0, 6.28)
        field += np.sin(x / W * fx * 6.28 + ph) * np.cos(y / H * fy * 6.28 + ph * 0.7)
    lines = np.abs((field * 3.2) % 1 - 0.5) < 0.018
    img[lines] += np.array([45, 105, 200]) * 0.22
    v = np.sqrt(((x / W - 0.5) * 1.1) ** 2 + ((y / H - 0.5) * 1.3) ** 2)
    img *= (1 - 0.45 * np.clip(v - 0.25, 0, 1))[..., None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)).save(OUT / f"{name}.png", optimize=True)


def glow(name, rgb, size=900):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    d = np.sqrt((x - size / 2) ** 2 + (y - size / 2) ** 2) / (size / 2)
    a = np.clip(np.exp(-(d / 0.55) ** 2) * 150, 0, 255)
    im = np.zeros((size, size, 4), np.uint8); im[..., :3] = rgb; im[..., 3] = a.astype(np.uint8)
    Image.fromarray(im).save(OUT / f"{name}.png")


def stand_map(name, w=1600, pad=40, labels=True):
    gj = json.load(open(ROOT / "analysis/data/stands.geojson"))
    rings = lambda f: [r for poly in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"]) for r in poly]
    pts = [c for f in gj["features"] for r in rings(f) for c in r]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts); y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    h = int(w * (y1 - y0) / ((x1 - x0) * 0.911))
    S = 2  # supersample
    im = Image.new("RGBA", ((w + 2 * pad) * S, (h + 2 * pad) * S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    pj = lambda c: ((pad + (c[0] - x0) / (x1 - x0) * w) * S, (pad + (y1 - c[1]) / (y1 - y0) * h) * S)
    conv = {5, 6, 9, 12, 18}
    for hot in (False, True):
        for f in gj["features"]:
            if (f["properties"]["stand"] in conv) != hot:
                continue
            fill, line = ((255, 107, 129, 200), (255, 170, 185, 255)) if hot else ((77, 163, 255, 130), (165, 212, 255, 235))
            for r in rings(f):
                dr.polygon([pj(c) for c in r], fill=fill, outline=line, width=2 * S)
    im = im.resize((w + 2 * pad, h + 2 * pad), Image.LANCZOS)
    base = im.copy()
    halo = im.filter(ImageFilter.GaussianBlur(14))  # soft neon halo
    out = Image.alpha_composite(halo, base)
    if labels:
        dr = ImageDraw.Draw(out)
        from PIL import ImageFont
        try: fnt = ImageFont.truetype("C:/Windows/Fonts/seguisb.ttf", 26)
        except OSError: fnt = ImageFont.load_default()
        for f in gj["features"]:
            k = f["properties"]["stand"]
            if k in conv:
                r = rings(f)[0]; cx = sum(pj(c)[0] for c in r) / len(r) / S; cy = sum(pj(c)[1] for c in r) / len(r) / S
                dr.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(255, 255, 255, 240))
                dr.text((cx, cy), str(k), font=fnt, fill=(8, 26, 46, 255), anchor="mm")
    out.save(OUT / f"{name}.png")
    print(name, out.size)


def website_shot():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try: b = p.chromium.launch(channel="chrome")
        except Exception: b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5)
        pg.goto("https://nahla-nabil.github.io/blue-carbon-guardian/#monitor", wait_until="networkidle"); pg.wait_for_timeout(2500)
        pg.evaluate("document.getElementById('monitor').scrollIntoView()"); pg.wait_for_timeout(1200)
        pg.screenshot(path=str(OUT / "website_monitor.png"))
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(1200)
        pg.screenshot(path=str(OUT / "website_hero.png"))
        b.close()


if __name__ == "__main__":
    background("bg_a", (0.85, 0.15), 1)
    background("bg_b", (0.12, 0.85), 2)
    background("bg_c", (0.5, 0.5), 3)
    glow("glow_cyan", (56, 189, 248)); glow("glow_blue", (56, 140, 248)); glow("glow_gold", (242, 193, 78))
    stand_map("stand_map")
    stand_map("stand_map_plain", labels=False)
    website_shot()
    print("assets ->", OUT)
