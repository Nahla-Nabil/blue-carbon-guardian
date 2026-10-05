"""Render deck_source/ (Slides Artifact format) slide by slide at 1920 x 1080 in Chrome, check that no slide overflows, and export docs/slides.pdf
(the PDF attached to the submission form). Images referenced as /_blob/<id> are mapped to deck_source/images/; <x-icon> is drawn as a simple glyph.
Run from the repository root: python scripts/export_slides_pdf.py   (needs: pip install playwright; python -m playwright install chromium, or Chrome)"""
import json, pathlib, sys
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent; DECK = ROOT / "deck_source"; OUT = ROOT / "docs"; TMP = OUT / "_slide_png"; TMP.mkdir(parents=True, exist_ok=True)
BLOB = {"5288132c4311e6fcdd211802c53d8052": "stand5_before_after_2021_2026.png", "cdb6f513d7b5b62df43f149147663260": "stand9_before_after_2020_2026.png",
        "4f7aa84e740446007eb703059f094f76": "enmap_stand5_two_epochs.png", "1d8e15d4b42a2099938d3a16c7d394b2": "dash_map_only.png"}
ICON = {"CheckCircle": "&#10003;", "Activity": "&#8767;", "Search": "&#9906;", "Database": "&#9636;", "Chart": "&#9638;"}
HEAD = ('<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700'
        '&family=IBM+Plex+Mono:wght@400;500;600&display=swap"><style>*{margin:0;box-sizing:border-box} body{width:1920px;height:1080px}'
        ' section{width:1920px;height:1080px;position:relative;overflow:hidden} aside{display:none}'
        ' x-icon{display:inline-flex;align-items:center;justify-content:center;flex:none;font-weight:700;font-size:26px}'
        ' table{border-collapse:collapse;width:100%} th,td{padding:14px 20px;text-align:left} h1,h2,h3,p{margin:0}</style>')

order = json.load(open(DECK / "deck.json", encoding="utf-8"))["order"]; pngs, bad = [], []
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    for sid in order:
        html = (DECK / "slides" / f"{sid}.html").read_text(encoding="utf-8")
        for k, v in BLOB.items(): html = html.replace(f"/_blob/{k}", (DECK / "images" / v).as_uri())
        html = html.replace('src="images/', f'src="{(DECK / "images").as_uri()}/')
        for name, glyph in ICON.items(): html = html.replace(f'<x-icon name="{name}"', f'<x-icon name="{name}"').replace(f'name="{name}" style="', f'name="{name}" data-g="{glyph}" style="')
        html = html.replace("></x-icon>", "></x-icon>")
        f = TMP / f"{sid}.html"; f.write_text(HEAD + html, encoding="utf-8")
        pg.goto(f.as_uri()); pg.wait_for_timeout(900)
        pg.evaluate("document.querySelectorAll('x-icon').forEach(e => e.innerHTML = e.dataset.g || '&#8226;')")
        low = pg.evaluate("""() => { let m = 0; document.querySelectorAll('section *').forEach(e => { if (getComputedStyle(e).position === 'absolute' || e.closest('aside')) return;
                 const r = e.getBoundingClientRect(); if (r.height > 0) m = Math.max(m, r.bottom); }); return [Math.round(m), [...document.images].every(i => i.complete && i.naturalWidth > 0)]; }""")
        png = TMP / f"{sid}.png"; pg.screenshot(path=str(png)); pngs.append(png)
        ok = low[0] <= 920 and low[1]; bad += [] if ok else [sid]
        print(f"{sid:16s} lowest content {low[0]:4d}px  images ok {low[1]}  {'ok' if ok else 'CHECK'}")
    b.close()
imgs = [Image.open(x).convert("RGB") for x in pngs]
imgs[0].save(OUT / "slides.pdf", save_all=True, append_images=imgs[1:], resolution=144)
print(f"docs/slides.pdf: {len(imgs)} pages" + (f" | CHECK: {bad}" if bad else " | all slides fit"))
sys.exit(1 if bad else 0)
