#!/usr/bin/env python3
"""Spraymax end screen for Narayan's CapCut cut of the K2 film (lv_0_20261015211615.mp4, 1080x1920, 30 fps).

His cut ends on 46 black frames (7.433-8.967 s). The music under it is the K2 reel's track from 5.434 s, so the
black starts right on a low hit of the outro (track 12.85 s); the next ones fall 0.34 s and 0.95 s in.

The screen (Narayan: "i js want the spraymax born in Himachal screen with spraymax.in text overlay"): near-black,
the white Spraymax wordmark, BORN IN HIMACHAL under it, spraymax.in below; centred, inside the Reels safe area.
The wordmark settles in on the cut, the line and the URL on the next hit (0.34 s), then a slow drift in.

  python3 ads/spraymax/k2-15s/end_screen.py - end-screen.mp4 [frames=46] [fps=30]
  python3 ads/spraymax/k2-15s/end_screen.py - end-screen.mp4 46 30 --into his-cut.mp4 out.mp4
"""
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

out_path = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 46
FPS = int(sys.argv[4]) if len(sys.argv) > 4 and not sys.argv[4].startswith("--") else 30
INTO = sys.argv[sys.argv.index("--into") + 1:sys.argv.index("--into") + 3] if "--into" in sys.argv else None
W, H = 1080, 1920
FONTS = "video/fonts/"


def text_img(txt, font, size, tracking=0.0, fill=(255, 255, 255)):
    f = ImageFont.truetype(FONTS + font, size)
    widths = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else size * 0.3 for c in txt]
    tw = int(sum(widths) + tracking * size * (len(txt) - 1)) + 24
    asc, desc = f.getmetrics()
    img = Image.new("RGBA", (tw, asc + desc + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 12
    for c, w in zip(txt, widths):
        if c != " ":
            d.text((x - f.getbbox(c)[0], 12), c, font=f, fill=fill + (255,))
        x += w + tracking * size
    return np.asarray(img).astype(np.float32)


def over(canvas, rgba, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.002:
        return
    if abs(scale - 1) > 1e-3:
        rgba = cv2.resize(rgba, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    h, w = rgba.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0]
    a = src[..., 3:4] / 255.0 * alpha
    canvas[ya:yb, xa:xb] = canvas[ya:yb, xa:xb] * (1 - a) + src[..., :3] * a


def ease_out(x):
    x = float(np.clip(x, 0, 1))
    return 1 - (1 - x) ** 3


# ---- assets ----
logo = cv2.imread("brand/spraymax/assets/logo-wide.png", cv2.IMREAD_UNCHANGED)
ys, xs = np.nonzero(logo[..., 3] > 10)
logo = logo[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
LW = 600
logo = cv2.resize(logo, (LW, int(LW * logo.shape[0] / logo.shape[1])), interpolation=cv2.INTER_AREA)
WORD = np.dstack([np.full(logo.shape[:2] + (3,), 255, np.float32), logo[..., 3].astype(np.float32)])
LINE = text_img("BORN IN HIMACHAL", "Outfit-500.ttf", 34, tracking=0.42, fill=(206, 212, 226))
URL = text_img("spraymax.in", "Outfit-300.ttf", 40, tracking=0.06, fill=(236, 238, 244))

# ---- backdrop: near-black with a touch of the studio's blue, soft vignette ----
gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
BG = np.empty((H, W, 3), np.float32)
BG[:] = (14, 10, 8)
vig = np.hypot((gx - W / 2) / W, (gy - H * 0.47) / H)
BG *= (1.2 - 0.7 * vig)[..., None]
rng = np.random.default_rng(3)
GRAIN = [cv2.GaussianBlur(rng.normal(0, 2.2, (H, W)).astype(np.float32), (0, 0), 0.7) for _ in range(4)]


def frame(i):
    t = i / FPS
    c = BG.copy()
    kw = ease_out(t / 0.28)                                       # wordmark settles in on the cut
    over(c, WORD, W / 2, 880 + 10 * (1 - kw), kw, 1.06 - 0.06 * kw)
    kl = ease_out((t - 0.20) / 0.28)                              # line and URL on the next hit
    over(c, LINE, W / 2, 1012 + 8 * (1 - kl), kl)
    ku = ease_out((t - 0.34) / 0.30)
    over(c, URL, W / 2, 1120 + 8 * (1 - ku), ku)
    # grain, then a slow drift in over the whole screen
    c += GRAIN[i % 4][..., None]
    z = 1.0 + 0.03 * (t / max(N / FPS, 1e-6))
    A = np.float32([[z, 0, W / 2 - z * W / 2], [0, z, H / 2 - z * 900]])
    A[1, 2] = 900 - z * 900
    c = cv2.warpAffine(np.clip(c, 0, 255), A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.clip(c, 0, 255).round().astype(np.uint8)


frames = [frame(i) for i in range(N)]


def encode(path, seq, audio_from=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-"]
    if audio_from:
        cmd += ["-i", audio_from, "-map", "0:v", "-map", "1:a?", "-c:a", "copy", "-shortest"]
    cmd += ["-c:v", "libx264", "-crf", "15", "-preset", "slow", "-pix_fmt", "yuv420p", path]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in seq:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("ffmpeg failed")


encode(out_path, frames)
print(f"end screen: {N} frames at {FPS} fps ({N / FPS:.2f} s) -> {out_path}")

if INTO:
    src, dst = INTO
    cap = cv2.VideoCapture(src)
    seq = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        seq.append(f)
    means = np.array([f.mean() for f in seq])
    first_black = int(np.flatnonzero(means >= 3)[-1]) + 1                         # the black tail of his cut
    end = [frames[min(k, N - 1)] for k in range(len(seq) - first_black)]
    encode(dst, seq[:first_black] + end, audio_from=src)
    print(f"placed into {src}: frames {first_black}-{len(seq) - 1} ({first_black / FPS:.3f} s on) -> {dst}")
