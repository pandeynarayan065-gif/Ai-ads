#!/usr/bin/env python3
"""Spraymax "What's bro carrying": cut the reel on the reference's beat grid (30 fps, 1080x1920, 11.93 s).

  0.00-4.43   hook: real phone footage (--hook clip.mp4), or a labelled animatic until it's shot
  4.43-11.93  the nine Blender shots (video/blender/carry_shots.py renders), one per beat
  10.90-      end card over C9: wordmark, BORN IN HIMACHAL, spraymax.in

The caption bar ("What's bro carrying") sits over the hook like a Snapchat caption. Two exports:
  <out>.mp4         SFX only (+ the hook's own phone audio): post this, adding the music inside Instagram
  <out>-temp.mp4    with a temp music track (--music, e.g. the reference's audio) to judge timing; never post

  python3 ads/spraymax/bro-carrying/assemble.py --renders DIR --out OUT [--hook clip.mp4] [--hook-end S]
         [--music track.wav] [--caption "What's bro carrying"]
--hook-end: time in the clip of the frame that should land on the cut (the bottle held to the lens);
default: the clip's end.
"""
import argparse
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
FONTS = ROOT / "video/fonts"
FPS, W, H = 30, 1080, 1920
N = 358                                                    # 11.93 s, as the reference
CUT_HOOK = 133                                             # 4.43 s: the drop
# the reference's cuts, on its beat grid (s) -> frames
CUTS = [round(t * FPS) for t in (4.43, 5.13, 5.80, 7.07, 7.80, 8.47, 9.13, 9.80, 10.50)] + [N]
SHOTS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]
END_IN = 10.90

ap = argparse.ArgumentParser()
ap.add_argument("--renders", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--hook")
ap.add_argument("--hook-end", type=float)
ap.add_argument("--music")
ap.add_argument("--caption", default="What's bro carrying")
args = ap.parse_args()
renders = Path(args.renders)
out = Path(args.out)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def rgba_text(txt, f, fill=(255, 255, 255), tracking=0.0):
    widths = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else f.size * 0.28 for c in txt]
    tw = int(sum(widths) + tracking * f.size * (len(txt) - 1)) + 24
    asc, desc = f.getmetrics()
    img = Image.new("RGBA", (tw, asc + desc + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 12
    for c, w in zip(txt, widths):
        if c != " ":
            d.text((x - f.getbbox(c)[0], 12), c, font=f, fill=fill + (255,))
        x += w + tracking * f.size
    return np.asarray(img).astype(np.float32)


def over(canvas, rgba, cx, cy, alpha=1.0):
    if alpha <= 0.002:
        return
    h, w = rgba.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0]
    a = src[..., 3:4] / 255.0 * alpha
    canvas[ya:yb, xa:xb] = canvas[ya:yb, xa:xb] * (1 - a) + src[..., [2, 1, 0]] * a


# ---- caption bar: translucent black band across the frame at ~44% height, white text (Snapchat style)
CAP = rgba_text(args.caption, font("InterTight-600.ttf", 38))
BAR_Y, BAR_H = 850, 74


def caption(c):
    c[BAR_Y - BAR_H // 2:BAR_Y + BAR_H // 2] *= 0.42
    over(c, CAP, W / 2, BAR_Y + 2)


# ---- end card (as the K2 end screen): white wordmark, BORN IN HIMACHAL, spraymax.in
logo = cv2.imread(str(ROOT / "brand/spraymax/assets/logo-wide.png"), cv2.IMREAD_UNCHANGED)
ys, xs = np.nonzero(logo[..., 3] > 10)
logo = logo[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
logo = cv2.resize(logo, (560, int(560 * logo.shape[0] / logo.shape[1])), interpolation=cv2.INTER_AREA)
WORD = np.dstack([np.full(logo.shape[:2] + (3,), 255, np.float32), logo[..., 3].astype(np.float32)])
LINE = rgba_text("BORN IN HIMACHAL", font("Outfit-500.ttf", 32), (210, 214, 232), tracking=0.42)
URL = rgba_text("spraymax.in", font("Outfit-300.ttf", 40), (236, 238, 244), tracking=0.06)


def ramp(t, t0, d):
    x = float(np.clip((t - t0) / d, 0, 1))
    return 1 - (1 - x) ** 3


def end_card(c, t):
    over(c, WORD, W / 2, 380 + 10 * (1 - ramp(t, END_IN, 0.3)), ramp(t, END_IN, 0.3))
    over(c, LINE, W / 2, 495, ramp(t, END_IN + 0.25, 0.3))
    over(c, URL, W / 2, 575, ramp(t, END_IN + 0.4, 0.3))


# ---- hook: phone footage, or an animatic until it's shot
HOOK_BEATS = [(0.00, 1.10, "H1", "Guy in a black tee walks", "across a busy street with a duffel"),
              (1.10, 2.30, "H2", "POV: a hand comes in", "and stops him"),
              (2.30, 3.90, "H3", "He unzips the bag:", "it's packed with Spraymax"),
              (3.90, 4.43, "H4", "The hand pulls one out,", "tilted, label to the lens")]


def hook_frames():
    if args.hook:
        cap = cv2.VideoCapture(args.hook)
        fps = cap.get(cv2.CAP_PROP_FPS)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        end = args.hook_end if args.hook_end is not None else (n - 1) / fps
        frames = []
        for k in range(CUT_HOOK):
            t = end - (CUT_HOOK - 1 - k) / FPS
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(round(t * fps))))
            ok, f = cap.read()
            if not ok:
                f = frames[-1].astype(np.uint8) if frames else np.zeros((H, W, 3), np.uint8)
            fh, fw = f.shape[:2]                                   # cover-crop to 9:16
            s = max(W / fw, H / fh)
            f = cv2.resize(f, (int(round(fw * s)), int(round(fh * s))), interpolation=cv2.INTER_AREA)
            y0, x0 = (f.shape[0] - H) // 2, (f.shape[1] - W) // 2
            frames.append(f[y0:y0 + H, x0:x0 + W].astype(np.float32))
        return frames
    big, small = font("Outfit-600.ttf", 64), font("Outfit-300.ttf", 40)
    tag = rgba_text("HOOK: REAL PHONE FOOTAGE (TO SHOOT)", font("Outfit-500.ttf", 30), (150, 150, 160), tracking=0.15)
    frames = []
    for k in range(CUT_HOOK):
        t = k / FPS
        c = np.full((H, W, 3), 28, np.float32)
        for t0, t1, lab, l1, l2 in HOOK_BEATS:
            if t0 <= t < t1:
                over(c, tag, W / 2, 330)
                over(c, rgba_text(lab, big, (255, 255, 255)), W / 2, 1120)
                over(c, rgba_text(l1, small, (220, 220, 225)), W / 2, 1230)
                over(c, rgba_text(l2, small, (220, 220, 225)), W / 2, 1290)
        frames.append(c)
    return frames


def render_frames(shot, n):
    files = sorted(renders.glob(f"{shot}_*.png"))
    if not files:
        raise SystemExit(f"no renders for {shot} in {renders}")
    seq = []
    for k in range(n):
        im = cv2.imread(str(files[min(k, len(files) - 1)]))
        if im.shape[:2] != (H, W):
            im = cv2.resize(im, (W, H), interpolation=cv2.INTER_LANCZOS4)
        seq.append(im.astype(np.float32))
    return seq


# ---- picture
tmp = out.with_suffix(".video.mp4")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                        "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
count = 0
for f in hook_frames():
    caption(f)
    enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    count += 1
for shot, a, b in zip(SHOTS, CUTS[:-1], CUTS[1:]):
    for k, f in enumerate(render_frames(shot, b - a)):
        if shot == "C9":
            end_card(f, (a + k) / FPS)
        enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
        count += 1
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")

# ---- sound: synthesised SFX (whoosh into the drop, the pump hiss, bubbles) + the hook's phone audio
SR = 48000
rng = np.random.default_rng(1)
sfx = np.zeros(int(N / FPS * SR) + SR, np.float32)


def band_noise(dur, lo, hi):
    n = int(dur * SR)
    spec = np.fft.rfft(rng.normal(0, 1, n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    spec[(fr < lo) | (fr > hi)] = 0
    x = np.fft.irfft(spec, n)
    return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)


def add(t, x, gain):
    i = int(t * SR)
    sfx[i:i + len(x)] += x[:len(sfx) - i] * gain


w = band_noise(0.6, 300, 6000)                               # whoosh: rising then cut on the drop
add(4.43 - 0.6, w * np.linspace(0, 1, len(w)) ** 2, 0.35)
p_t = CUTS[2] / FPS + 8 / FPS                                 # pump press in C3 (frame 6 + 2 to the burst)
h = band_noise(0.45, 2500, 12000)
add(p_t, h * np.exp(-np.linspace(0, 4, len(h))) * np.minimum(1, np.linspace(0, 30, len(h))), 0.5)
for k in range(9):                                            # bubble blips under C5
    d = int(0.05 * SR)
    tt = np.arange(d) / SR
    fq = rng.uniform(500, 1100)
    blip = np.sin(2 * np.pi * (fq * tt + 2500 * tt ** 2)) * np.exp(-tt * 60)
    add(CUTS[4] / FPS + k * 0.07 + rng.uniform(0, 0.03), blip.astype(np.float32), 0.12)
sfx_path = out.with_suffix(".sfx.wav")
pcm = (np.clip(sfx[:int(N / FPS * SR)], -1, 1) * 32767).astype(np.int16)
import wave  # noqa: E402
with wave.open(str(sfx_path), "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())

dur = N / FPS
inputs = ["-i", str(tmp), "-i", str(sfx_path)]
mix = "[1:a]aresample=48000,apad,atrim=0:%.3f[s]" % dur
labels = "[s]"
nin = 1
if args.hook:
    he = args.hook_end if args.hook_end is not None else None
    st = (he - (CUT_HOOK - 1) / FPS) if he is not None else None
    inputs += ["-i", args.hook]
    trim = f"atrim={max(st, 0):.3f}:{st + CUT_HOOK / FPS:.3f}," if st is not None else ""
    mix += f";[2:a]{trim}asetpts=N/SR/TB,aresample=48000,afade=t=out:st={CUT_HOOK / FPS - 0.15:.3f}:d=0.15,apad,atrim=0:{dur:.3f},volume=0.8[h]"
    labels += "[h]"
    nin += 1
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
                f"{mix};{labels}amix=inputs={nin}:normalize=0,loudnorm=I=-14:TP=-1.0[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest",
                "-movflags", "+faststart", str(out)], check=True)
if args.music:
    temp = out.with_name(out.stem + "-temp.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-i", args.music, "-filter_complex",
                    f"[1:a]aresample=48000,atrim=0:{dur:.3f},asetpts=N/SR/TB[m];[0:a]volume=0.6[x];"
                    f"[m][x]amix=inputs=2:normalize=0,loudnorm=I=-12:TP=-1.0[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest",
                    "-movflags", "+faststart", str(temp)], check=True)
    print("temp-music version (timing only, never post):", temp)
tmp.unlink()
sfx_path.unlink()
print(f"{count} frames ({count / FPS:.2f} s) -> {out}")
