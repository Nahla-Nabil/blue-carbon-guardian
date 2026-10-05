"""Demo video, step 3: render video/build/video.html frame by frame (deterministic window.render(t)) at 1920x1080, 30 fps, pipe the frames to ffmpeg,
mux with video/build/audio.wav -> docs/demo_video.mp4 (H.264 + AAC). Run: python video/render.py   (needs Chrome or Playwright Chromium, and ffmpeg)"""
import json, pathlib, subprocess, time
from playwright.sync_api import sync_playwright

FPS = 30; B = pathlib.Path("video/build"); OUT = "docs/demo_video.mp4"
dur = json.load(open(B / "timeline.json", encoding="utf-8"))["duration"]; n = int(dur * FPS)
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", "-i", str(B / "audio.wav"),
                       "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                       "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
t0 = time.time()
with sync_playwright() as p:
    try: b = p.chromium.launch(channel="chrome")
    except Exception: b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto((B / "video.html").resolve().as_uri()); pg.evaluate("window.ready"); pg.wait_for_timeout(1500)
    for i in range(n):
        pg.evaluate(f"window.render({i / FPS})")
        ff.stdin.write(pg.screenshot(type="jpeg", quality=93))
        if i % 300 == 0: print(f"  frame {i}/{n}  {time.time() - t0:.0f}s", flush=True)
    b.close()
ff.stdin.close(); ff.wait()
print(f"done: {OUT}  {n} frames, {dur:.1f} s, {time.time() - t0:.0f}s render")
