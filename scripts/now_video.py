"""Short silent website video (~30 s) for the slide before the close: what the live site shows today after the Bahrain Space
Agency feedback (risk register -> click a case -> monitor; regional context; expert evaluation). Captioned, no sound.
Output: deck_pptx/build/media/website_now.mp4 (+ .png poster), 1920x1080. Run from the repository root:  python scripts/now_video.py
"""
import functools, http.server, shutil, subprocess, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "deck_pptx")); sys.path.insert(0, str(ROOT / "scripts"))
from media import CURSOR_JS
from demo_paced import CAPTION_JS

OUT = ROOT / "deck_pptx" / "build" / "media"


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def main():
    from playwright.sync_api import sync_playwright
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8772), functools.partial(Quiet, directory=str(ROOT / "docs")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    vdir = OUT / "_rec_now"; shutil.rmtree(vdir, ignore_errors=True)
    with sync_playwright() as p:
        try: b = p.chromium.launch(channel="chrome")
        except Exception: b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=str(vdir), record_video_size={"width": 1280, "height": 720},
                            color_scheme="light")
        ctx.add_init_script("try{localStorage.setItem('bcg-lang','en');localStorage.setItem('bcg-theme','light')}catch(e){}")
        pg = ctx.new_page()
        pg.goto("http://127.0.0.1:8772/index.html", wait_until="networkidle"); pg.evaluate(CURSOR_JS); pg.mouse.move(900, 300)
        cap = lambda t: pg.evaluate(CAPTION_JS, t)
        wait = pg.wait_for_timeout

        def go(sel, off=70, ms=1300):
            pg.evaluate(f"window.scrollTo({{top: document.querySelector('{sel}').getBoundingClientRect().top + scrollY - {off}, behavior: 'smooth'}})"); wait(ms)

        def glide(sel, steps=35):
            bb = pg.locator(sel).first.bounding_box(); pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2, steps=steps)

        wait(800)
        go("#risks"); cap("Risk register: every flag becomes a ranked case"); wait(3500)
        go("#riskcount", 90); wait(2500)
        glide(".risk[data-k='9']"); cap("Date · likely cause · confidence · inspector action"); wait(2500)
        pg.mouse.down(); pg.mouse.up(); wait(1500)                                   # opens stand 9 in the monitor
        cap("One click: the stand and its flagged cells"); wait(1200)
        pg.locator("#bCells").click(); wait(3000)
        go("#region"); cap("Why it matters: national pledges, a coast changing fast"); wait(4500)
        go("#region .grid2", 160); wait(2500)
        go("#expert", 120); cap("Expert Evaluation and Feedback · Bahrain Space Agency"); wait(4000)
        cap("nahla-nabil.github.io/blue-carbon-guardian"); wait(2500)
        ctx.close(); b.close()
    srv.shutdown()
    webm = next(vdir.glob("*.webm")); mp4 = OUT / "website_now.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.2", "-i", str(webm), "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "21", "-r", "30", "-movflags", "+faststart", "-an", str(mp4)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2", "-i", str(mp4), "-frames:v", "1", str(OUT / "website_now.png")], check=True)
    shutil.rmtree(vdir)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout
    print("ok", mp4, d.strip(), "s")


if __name__ == "__main__":
    main()
