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
END_Y = 680                                               # wordmark row: between C9's top shelf and the bottles

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
    over(c, WORD, W / 2, END_Y + 10 * (1 - ramp(t, END_IN, 0.3)), ramp(t, END_IN, 0.3))
    over(c, LINE, W / 2, END_Y + 115, ramp(t, END_IN + 0.25, 0.3))
    over(c, URL, W / 2, END_Y + 195, ramp(t, END_IN + 0.4, 0.3))


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


# ---- finishing pass on the 3D frames (the "editing tools"): bloom, streaks on specular points, chromatic
# fringing, a soft filmic shoulder and S-curve, vignette, film grain, and the reference's camera moves (below)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.30 * (((_xx - W / 2) / (W / 2)) ** 2 * 0.55 + ((_yy - H / 2) / (H / 2)) ** 2 * 0.45))[..., None]
_g = np.random.default_rng(7)
GRAIN = [cv2.GaussianBlur(_g.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7)[..., None] for _ in range(8)]
STREAK_TINT = np.array([1.0, 0.72, 0.9], np.float32)      # BGR: lilac


def scale_about_centre(img, s, dx=0.0, dy=0.0):
    A = np.float32([[s, 0, W / 2 - s * W / 2 + dx], [0, s, H / 2 - s * H / 2 + dy]])
    return cv2.warpAffine(img, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# Digital camera, copied from the reference's measured motion (optical flow, frame by frame): every shot keeps
# creeping (push-in, drift up, slide), the first shot after the drop does a quick pull-back on frames 3-7 that
# settles (their speed ramp), and inside three shots the zoom jumps on the half-beat, exactly where theirs does
# (6.45, 8.13, 11.15 s). Cuts themselves are hard, as theirs are.
DRIFT = {"C1": (0.0004, 0.0, 0.0), "C2": (0.0, 0.0, 0.0), "C3": (0.0004, 0.0, 0.0), "C4": (0.0006, 0.0, 0.0),
         "C5": (-0.0010, 0.0, -1.6), "C6": (0.0003, 0.0, 0.0), "C7": (0.0004, 0.0, 0.0), "C8": (0.0, 0.0, -1.2),
         "C9": (0.0004, 0.0, 0.0)}                          # (zoom per frame, dx px/frame, dy px/frame)
JUMPS = {"C3": 6.45, "C5": 8.13, "C9": 11.15}


def cam(shot, k, t_abs):
    zr, vx, vy = DRIFT[shot]
    s = 1.035 + zr * k
    if shot == "C1":                                        # their speed ramp: a quick pull-back on frames 3-7
        x = min(max((k - 3) / 4, 0), 1)
        s += 0.014 * (1 - x * x * (3 - 2 * x))
    if shot in JUMPS and t_abs >= JUMPS[shot]:
        s *= 1.04 if shot != "C3" else 1 / 1.04              # the zoom jumps on the half-beat (C3 jumps out)
    return s, vx * k, vy * k


def finish(f, k_in_shot, frame_no, shot):
    x = f / 255.0
    t_abs = frame_no / FPS
    s, dx, dy = cam(shot, k_in_shot, t_abs)
    x = scale_about_centre(x, s, dx, dy)
    lum = x.max(2)
    hi = np.clip((lum - 0.78) / 0.22, 0, 1)[..., None] * x
    small = cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    wide = cv2.resize(cv2.GaussianBlur(small, (0, 0), 9), (W, H), interpolation=cv2.INTER_LINEAR)
    x = x + 0.12 * cv2.GaussianBlur(hi, (0, 0), 6) + 0.16 * wide
    # streaks only from small specular points: brighter than their own surroundings, not whole white surfaces
    pt = np.clip((lum - cv2.GaussianBlur(lum, (0, 0), 10) - 0.10) / 0.2, 0, 1) * (lum > 0.85)
    hot = cv2.resize((pt[..., None] * x), (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    x = x + 1.4 * cv2.resize(cv2.blur(hot, (81, 1)), (W, H), interpolation=cv2.INTER_LINEAR) * STREAK_TINT
    b_, g_, r_ = cv2.split(x)                              # chromatic fringing toward the edges
    r_ = scale_about_centre(r_, 1.0011)
    b_ = scale_about_centre(b_, 0.9989)
    x = cv2.merge([b_, g_, r_])
    x = x / (1 + 0.06 * x)                                 # soft highlight shoulder
    x = np.clip(x * 1.06, 0, 1)
    x = x * 0.78 + (3 * x * x - 2 * x * x * x) * 0.22      # gentle S-curve
    x = x * VIG + GRAIN[frame_no % len(GRAIN)] * 0.014
    return np.clip(x * 255, 0, 255)


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
        f = finish(f, k, a + k, shot)
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
for c_i in (3, 6):                                            # pump sprays in C4 and C7 (press at frame 3)
    h = band_noise(0.4, 2500, 12000)
    add(CUTS[c_i] / FPS + 3 / FPS, h * np.exp(-np.linspace(0, 4, len(h))) * np.minimum(1, np.linspace(0, 30, len(h))), 0.45)
tt = np.arange(int(0.5 * SR)) / SR                            # low hit on the drop
add(4.43, (np.sin(2 * np.pi * (55 * tt - 20 * tt ** 2)) * np.exp(-tt * 7)).astype(np.float32), 0.6)
tt = np.arange(int(0.08 * SR)) / SR                           # the drip in C3 lets go
add(CUTS[2] / FPS + 0.75, (np.sin(2 * np.pi * (900 * tt + 4000 * tt ** 2)) * np.exp(-tt * 70)).astype(np.float32), 0.15)
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
