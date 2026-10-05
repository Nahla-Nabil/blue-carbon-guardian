"""Demo video, step 1: narration (Microsoft neural voice via edge-tts, one clip per sentence) + a generated ambient music bed (numpy, no
third-party music). Writes video/build/timeline.json (scene and subtitle timings) and video/build/audio.wav (voice + music, 48 kHz stereo).
Run from the repository root: python video/make_audio.py   (needs internet for the voice, and ffmpeg)"""
import asyncio, json, os, subprocess, wave
import numpy as np, edge_tts

B = "video/build"; os.makedirs(B, exist_ok=True); SR = 48000
N = json.load(open("video/narration.json", encoding="utf-8"))
GAP_LINE, GAP_SCENE, HEAD, TAIL = 0.35, 0.9, 1.6, 3.2           # seconds of silence


async def tts(text, path):
    await edge_tts.Communicate(text, N["voice"], rate=N["rate"]).save(path)


def load(path):
    """Decode an mp3 to mono float32 at SR with ffmpeg."""
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


clips, tl, t = [], {"scenes": [], "subs": []}, HEAD
for si, sc in enumerate(N["scenes"]):
    start = t
    for li, (en, ar) in enumerate(sc["lines"]):
        p = f"{B}/{sc['id']}_{li}.mp3"
        if not os.path.exists(p): asyncio.run(tts(en, p))
        a = load(p); a = a[np.argmax(np.abs(a) > 0.01):]; a = a[:len(a) - np.argmax(np.abs(a[::-1]) > 0.01)]   # trim silence
        clips.append((t, a)); tl["subs"].append(dict(start=round(t, 3), end=round(t + len(a) / SR, 3), en=en, ar=ar))
        t += len(a) / SR + GAP_LINE
    t += GAP_SCENE - GAP_LINE
    tl["scenes"].append(dict(id=sc["id"], start=round(start, 3), end=round(t, 3)))
total = t + TAIL; tl["scenes"][-1]["end"] = round(total, 3); tl["duration"] = round(total, 3)
voice = np.zeros(int(total * SR) + SR, np.float32)
for t0, a in clips: voice[int(t0 * SR):int(t0 * SR) + len(a)] += a

# ---- ambient music bed: slow evolving pad (Am - F - C - G), soft pulse, gentle fade; ducked under the voice ----------------------------------
n = len(voice); tt = np.arange(n) / SR
chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
music = np.zeros(n, np.float32); seg = 8.0
for k in range(int(np.ceil(total / seg)) + 1):
    f = chords[k % 4]; s0, s1 = int(k * seg * SR), int(min((k + 1.6) * seg, total + 1) * SR)
    if s0 >= n: break
    s1 = min(s1, n); x = tt[s0:s1] - k * seg; env = np.sin(np.pi * np.clip(x / (1.6 * seg), 0, 1)) ** 2
    for fr in f:
        for det, amp in ((0.0, 0.5), (0.7, 0.25), (-0.6, 0.25)):
            music[s0:s1] += amp * env * np.sin(2 * np.pi * (fr + det) * x) * 0.05
        music[s0:s1] += 0.012 * env * np.sin(2 * np.pi * fr / 2 * x)
pulse = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 4.0) ** 8
music *= (0.85 + 0.15 * pulse)
fade = np.minimum(1, np.minimum(tt / 3.0, (total + 1 - tt) / 4.0)).clip(0, 1); music *= fade
act = (np.abs(voice) > 0.02).astype(np.float64); k = int(0.4 * SR)                  # moving average via cumulative sums (fast)
cs = np.concatenate([[0], np.cumsum(act)]); lo = np.clip(np.arange(n) - k // 2, 0, n); hi = np.clip(np.arange(n) + k // 2, 0, n)
duck = ((cs[hi] - cs[lo]) / k).astype(np.float32)
music *= 1 - 0.55 * np.clip(duck * 3, 0, 1)
mix = voice * 0.95 + music
mix /= max(1e-6, np.abs(mix).max()) / 0.9
left = mix; right = np.roll(mix, int(0.004 * SR)) * 0.98                     # tiny stereo width
pcm = (np.stack([left, right], 1) * 32767).astype("<i2")
with wave.open(f"{B}/audio.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
json.dump(tl, open(f"{B}/timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"duration {total:.1f} s; scenes:", [(s["id"], round(s["end"] - s["start"], 1)) for s in tl["scenes"]])
