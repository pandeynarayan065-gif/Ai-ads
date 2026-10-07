#!/usr/bin/env python3
"""Spraymax "Beach hair, bottled." 19 s combo ad (9:16).

Desire first, then the offer: four slow-motion B-roll shots from the Gemini clips
(motion-interpolated with ffmpeg minterpolate, frame-checked windows only), soft
dissolves, text that holds until the shot ends, one calm offer screen held for 4.5 s,
and an end card. Warm ~90 BPM bed instead of the fast combo beat.

  python3 video/render_beach.py <slowmo_dir> [--preview]
<slowmo_dir> holds hair.mp4 sea.mp4 spray.mp4 splash.mp4 (see brief for windows/speeds).
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_combo as rc  # noqa: E402
from render_brand import ease_out_quint, reveal  # noqa: E402
from render_typo import ease_in_out, prog  # noqa: E402

W, H, FPS = rc.W, rc.H, rc.FPS
OUT = rc.OUT
WHITE = (255, 255, 255)
SOFT = (215, 215, 255)
CROP_W = int(round(720 * W / H))
XF = 0.35                                       # dissolve length

# key: crop centre x start -> end, push-in amount
SHOTS = {"hair": (400, 400, 0.08), "sea": (880, 860, 0.05), "spray": (800, 640, 0.04), "splash": (620, 620, 0.06)}
FR = {}
LEAK = None


def load(d):
    for k in SHOTS:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(Path(d) / f"{k}.mp4"), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        FR[k] = np.frombuffer(raw, np.uint8).reshape(-1, 720, 1280, 3)


def grade(a):
    x = a.astype(np.float32) / 255
    x = np.clip((x - 0.5) * 1.06 + 0.5, 0, 1)
    lum = x.mean(2, keepdims=True)
    x = lum + (x - lum) * 0.95
    x += (1 - lum) ** 2 * np.array([-0.025, -0.02, 0.05])
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def footage(key, lt, dur):
    fr = FR[key]
    img = Image.fromarray(grade(fr[min(len(fr) - 1, int(lt * FPS))]))
    cx0, cx1, push = SHOTS[key]
    p = ease_in_out(min(1, lt / dur))
    z = 1.0 + push * min(1, lt / dur)
    cw, ch = CROP_W / z, 720 / z
    cx = min(max(cx0 + (cx1 - cx0) * p, cw / 2), 1280 - cw / 2)
    c = img.crop((int(cx - cw / 2), int((720 - ch) / 2), int(cx + cw / 2), int((720 + ch) / 2))).resize((W, H), Image.LANCZOS)
    c = c.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2)).convert("RGBA")
    y = np.arange(H, dtype=np.float32)[:, None]
    g = (np.clip(1 - np.abs(y - 640) / 560, 0, 1) ** 1.5 * 0.5 + np.clip((y - 1250) / 500, 0, 1) * 0.6)
    shade = Image.new("RGBA", (W, H), (6, 4, 40, 0))
    shade.putalpha(Image.fromarray((np.repeat(g, W, 1) * 255).astype(np.uint8)))
    c.alpha_composite(shade)
    lk = LEAK.copy()
    lk[..., 3] = (lk[..., 3].astype(np.float32) * (0.25 + 0.2 * np.sin(lt * 1.3 + len(key)))).astype(np.uint8)
    c.alpha_composite(Image.fromarray(lk, "RGBA"))
    c.alpha_composite(rc.LOGO_WHITE, (int(W / 2 - rc.LOGO_WHITE.width / 2), 130))
    return c


def broll(key, lines, sub=None, sub_t=0.9, sub_y=905):
    def scene(lt, dur):
        c = footage(key, lt, dur)
        for txt, y, size, t0 in lines:
            reveal(c, rc.txt(txt, "InterTight-800", size, WHITE), W / 2, y, lt, t0, 0.6)
        if sub:
            q = ease_out_quint(prog(lt, sub_t, 0.6))
            rc.put(c, rc.txt(sub, "InterTight-600", 46, SOFT), W / 2, sub_y + 14 * (1 - q), alpha=q)
        return c, "indigo"
    return scene


def card(c, x0, x1, y0, y1, n, lt, t0):
    p = ease_out_quint(prog(lt, t0, 0.8))
    if p <= 0:
        return
    dy = 260 * (1 - p)
    rc.glass(c, (x0, y0 + dy, x1, y1 + dy), radius=34, tint=0.12, blur=20)
    cx = (x0 + x1) / 2
    old, new, save = rc.PRICES[n]
    rc.put(c, rc.txt(f"PACK OF {n}", "InterTight-800", 64, WHITE), cx, y0 + 80 + dy, alpha=p)
    if n == 2:
        its = [dict(x=cx - 64, base=y0 + 650 + dy, h=530, angle=-8), dict(x=cx + 64, base=y0 + 650 + dy, h=530, angle=8)]
    else:
        its = [dict(x=cx - 112, base=y0 + 640 + dy, h=480, angle=-12), dict(x=cx + 112, base=y0 + 640 + dy, h=480, angle=12),
               dict(x=cx, base=y0 + 650 + dy, h=515, angle=0)]
    rc.bottles(c, its, floor=False, wrap=(1, 1))
    o = rc.txt(old, "InterTight-800", 50, SOFT)
    rc.put(c, o, cx, y0 + 720 + dy, alpha=p)
    s = ease_in_out(prog(lt, t0 + 0.7, 0.35))
    if s > 0:
        ox0 = cx - o.width / 2 - 8
        ImageDraw.Draw(c).line((ox0, y0 + 732 + dy, ox0 + (o.width + 16) * s, y0 + 712 + dy), fill=(255, 90, 100, 255), width=6)
    q = prog(lt, t0 + 0.95, 0.4)
    if q > 0:
        sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
        rc.put(c, rc.pill(rc.txt(new, "InterTight-800", 92, rc.INDIGO), WHITE, pad=(24, 8), radius=20), cx, y0 + 830 + dy, alpha=min(1, q * 3), scale=sc)
    r = ease_out_quint(prog(lt, t0 + 1.25, 0.5))
    each = "Under ₹400 each" if n == 2 else "Just ₹333 each"
    rc.put(c, rc.txt(each, "InterTight-600", 44, WHITE), cx, y0 + 945 + dy, alpha=r)
    rc.put(c, rc.pill(rc.txt(f"SAVE {save}", "InterTight-800", 36, WHITE, tracking=2), None, pad=(22, 9), outline=WHITE),
           cx, y0 + 1025 + dy, alpha=r)


def s_offer(lt, dur):
    c = rc.INDIGO_SET.copy()
    reveal(c, rc.txt("PICK YOUR PACK.", "InterTight-800", 116, WHITE), W / 2, 250, lt, 0.1, 0.6)
    card(c, 50, 525, 400, 1500, 2, lt, 0.3)
    card(c, 555, 1030, 400, 1500, 3, lt, 0.55)
    q = prog(lt, 1.9, 0.4)
    if q > 0:
        sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
        rc.put(c, rc.pill(rc.txt("BEST VALUE", "InterTight-800", 36, rc.INDIGO, tracking=2), (205, 225, 255), pad=(22, 10)),
               950, 400, alpha=min(1, q * 3), scale=sc)
    r = ease_out_quint(prog(lt, 2.2, 0.6))
    rc.put(c, rc.txt("Free shipping across India", "InterTight-600", 44, SOFT), W / 2, 1640 + 12 * (1 - r), alpha=r)
    return c, "indigo"


def s_end(lt, dur):
    c = rc.PAPER_PLAIN.copy()
    p = ease_out_quint(prog(lt, 0.1, 0.7))
    rc.put(c, rc.LOGO, W / 2, 330 + 24 * (1 - p), alpha=p)
    reveal(c, rc.txt("Beach hair, bottled.", "InterTight-800", 72, rc.INK), W / 2, 470, lt, 0.3, 0.6)
    k = ease_out_quint(prog(lt, 0.15, 0.8))
    its = [dict(x=W / 2 - 150, base=1262 + 60 * (1 - k), h=600, angle=-12, alpha=k),
           dict(x=W / 2 + 150, base=1262 + 60 * (1 - k), h=600, angle=12, alpha=k),
           dict(x=W / 2, base=1272 + 60 * (1 - k), h=650, angle=0, alpha=k)]
    rc.bottles(c, its)
    q = ease_out_quint(prog(lt, 0.6, 0.5))
    rc.put(c, rc.pill(rc.txt("Shop now  ·  spraymax.in", "InterTight-800", 46, WHITE), rc.INDIGO, pad=(48, 24)), W / 2, 1450 + 18 * (1 - q), alpha=q)
    r = ease_out_quint(prog(lt, 0.8, 0.5))
    rc.put(c, rc.txt("Pack of 2  ·  ₹799        Pack of 3  ·  ₹999", "InterTight-600", 38, (70, 70, 90)), W / 2, 1580 + 10 * (1 - r), alpha=r)
    rc.put(c, rc.txt("Free shipping across India", "InterTight-600", 34, (110, 110, 130)), W / 2, 1650 + 10 * (1 - r), alpha=r)
    return c, "paper"


TL = [
    (broll("hair", [("THAT BEACH-DAY", 560, 100, 0.3), ("HAIR?", 700, 170, 0.6)]), 3.0),
    (broll("sea", [("WE BOTTLED IT.", 640, 124, 0.25)]), 2.5),
    (broll("spray", [("SHAKE.", 480, 140, 0.15), ("SPRAY.", 630, 140, 0.55), ("STYLE.", 780, 140, 0.95)],
           sub="Done in under 10 seconds.", sub_t=1.5), 3.0),
    (broll("splash", [("HIMALAYAN", 1430, 130, 0.2), ("SEA SALT.", 1570, 130, 0.4)], sub="Matte texture. Zero grease.", sub_t=0.9, sub_y=1700), 3.0),
    (s_offer, 4.5),
    (s_end, 3.0),
]
DUR = sum(d for _, d in TL)


def render_t(t, i):
    acc = 0.0
    for k, (fn, dur) in enumerate(TL):
        if t < acc + dur or k == len(TL) - 1:
            lt = t - acc
            c, kind = fn(lt, dur)
            if k > 0 and lt < XF:                        # dissolve from the previous shot (which holds its text)
                pfn, pdur = TL[k - 1]
                prev, _ = pfn(pdur + lt, pdur)
                a = ease_in_out(lt / XF)
                c = Image.blend(prev.convert("RGB"), c.convert("RGB"), a).convert("RGBA")
            return rc.grain(c, i, 9.0 if kind == "indigo" else 4.0)
        acc += dur


def audio(path, sr=44100):
    n = int(sr * DUR)
    out = np.zeros(n)
    tt = np.arange(n) / sr
    rng = np.random.default_rng(5)

    def add(t0, sig):
        i = int(t0 * sr)
        if i < n:
            out[i:i + len(sig)] += sig[: n - i]

    def sm(x, k):
        return np.convolve(x, np.ones(k) / k, mode="same")

    # warm pad: Am - F - C - G, 2.67 s per chord, slow swell
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 261.6, 329.6), (196.0, 246.9, 293.7)]
    bar = 60 / 90 * 4
    for k in range(int(DUR / bar) + 1):
        L = int(bar * sr)
        x = np.arange(L) / sr
        env = np.minimum(1, x / 0.6) * np.minimum(1, (bar - x) / 0.6)
        sig = sum(np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2 * f * x) for f in chords[k % 4]) * env * 0.035
        add(k * bar, sig)
    # soft pulse from "We bottled it." on: kick on 1 and 3, shaker on 8ths
    beat = 60 / 90
    t = 3.0
    while t < 16.0:
        x = np.arange(int(0.3 * sr)) / sr
        add(t, np.sin(2 * np.pi * np.cumsum(50 + 70 * np.exp(-x * 30)) / sr) * np.exp(-x * 10) * 0.5)
        for h in (0.0, 0.5):
            L = int(0.05 * sr)
            w = rng.standard_normal(L)
            add(t + h * beat, (w - sm(w, 3)) * np.exp(-np.arange(L) / sr * 70) * 0.035)
        t += 2 * beat
    # spray "tss" as the mist hits, splash swell, riser into the offer, end chime
    for t0, d in ((6.1, 0.7),):
        L = int(d * sr)
        w = rng.standard_normal(L)
        w = w - sm(w, 4)
        x = np.linspace(0, 1, L)
        add(t0, w * np.minimum(x * 20, 1) * np.exp(-x * 3) * 0.16)
    L = int(1.4 * sr)
    w = rng.standard_normal(L)
    w = sm(w, 3) - sm(w, 40)
    add(8.3, w * np.sin(np.linspace(0, np.pi, L)) ** 2 * 0.14)
    L = int(1.2 * sr)
    w = rng.standard_normal(L)
    w = sm(w, 2) - sm(w, 20)
    add(10.3, w * np.linspace(0, 1, L) ** 3 * 0.1)
    x = np.arange(int(2.5 * sr)) / sr
    add(16.0, (np.sin(2 * np.pi * 880 * x) * 0.08 + np.sin(2 * np.pi * 1318.5 * x) * 0.05) * np.exp(-x * 1.6))
    out *= np.clip(tt / 0.8, 0, 1) * np.clip((DUR - tt) / 1.2, 0, 1)
    out = np.tanh(out * 1.2)
    out *= 0.8 / np.max(np.abs(out))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    global LEAK
    rc.setup()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.exp(-(((xx - W * 1.05) / (W * 0.7)) ** 2 + ((yy - H * 0.15) / (H * 0.45)) ** 2) * 1.6)
    LEAK = np.dstack([np.zeros((H, W, 3)) + np.array([255, 150, 90]), a * 255]).astype(np.uint8)
    logo = rc.LOGO
    white = Image.new("RGBA", logo.size, WHITE + (255,))
    white.putalpha(logo.getchannel("A"))
    rc.LOGO_WHITE = white.resize((260, int(260 * logo.height / logo.width)), Image.LANCZOS)
    load(sys.argv[1])
    if "--preview" in sys.argv:
        (OUT / "preview").mkdir(parents=True, exist_ok=True)
        for t in (2.8, 5.3, 8.3, 11.3, 15.8, 18.8, 3.15):
            render_t(t, int(t * FPS)).save(OUT / "preview" / f"beach_{t:05.2f}.jpg", quality=90)
        print("previews written")
        return
    wav = OUT / "_beach.wav"
    audio(wav)
    mp4 = OUT / "combo-beach-hair-19s.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(DUR * FPS))):
        p.stdin.write(render_t(i / FPS, i).tobytes())
    p.stdin.close()
    p.wait()
    wav.unlink()
    print("wrote", mp4, DUR)


if __name__ == "__main__":
    main()
