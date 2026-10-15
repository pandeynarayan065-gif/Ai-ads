#!/usr/bin/env python3
"""Spraymax K2, 15 s (9:16, 24 fps): cut to the K2 East Face reel's music that Narayan picked.

The track (taken from that reel, 14.24 s) is a percussive build: a big hit every ~1.27 s (0.19, 1.46, 2.73, 4.00,
5.27, 6.53), double time from 7.65 (8.28, 8.92, 9.55, 10.18), then at 11.21 the drums drop out to low sustained
notes. Every cut lands on a hit; the end card takes the drop.

  python3 ads/spraymax/k2-15s/edit_k2_15s.py <music.wav> out.mp4
"""
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

music, out_path = sys.argv[1], sys.argv[2]
FPS, W, H = 24, 1080, 1920
K = "ads/spraymax/k2-15s/clips/"
HERO = "ads/spraymax/studio-hero/clips/hero-v2-final.mp4"
FONTS = "video/fonts/"

# (cut in, cut out on the music) <- (clip, source start s)
OCEAN = K + "spray-ocean-v2-locked.mp4"
SHOTS = [
    (0.00, 1.46, K + "ridge-8s-clean.mp4", 2.25),        # spindrift tearing off the ridge, climber
    (1.46, 2.73, K + "hair-helmet-8s.mp4", 0.00),        # helmet comes off, the wind takes his hair
    (2.73, 4.00, K + "salt-cut-3s.mp4", 0.40),           # pink salt, snow melting off it
    (4.00, 5.27, OCEAN, 0.75),                           # the sea: he sprays his hair as a wave explodes
    (5.27, 6.53, K + "drop-8s-locked.mp4", 1.50),        # the bottle plunges into water
    (6.53, 7.65, HERO, 0.55),                            # studio: the water crown
    (7.65, 8.28, K + "hair-helmet-8s.mp4", 6.25),        # double time: mountain wind in his hair
    (8.28, 8.92, OCEAN, 4.17),                           # sea wind in his hair
    (8.92, 9.55, K + "drop-8s-locked.mp4", 3.25),        # bubbles round the bottle
    (9.55, 10.18, HERO, 4.00),                           # water pours over the shoulder
    (10.18, 11.21, HERO, 6.20),                          # wet close-up, wordmark
]
END_IN = 11.21
TOTAL = 14.24


def read_frames(path, start, n):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(start * FPS)))
    out = []
    for _ in range(n):
        ok, f = cap.read()
        if not ok:
            out.append(out[-1])
            continue
        if f.shape[:2] != (H, W):
            f = cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA)
        out.append(f)
    return out


def text_img(txt, font, size, tracking=0.0, fill=(255, 255, 255)):
    f = ImageFont.truetype(FONTS + font, size)
    widths = [f.getbbox(c)[2] - f.getbbox(c)[0] if c != " " else size * 0.28 for c in txt]
    tw = int(sum(widths) + tracking * size * (len(txt) - 1)) + 20
    asc, desc = f.getmetrics()
    img = Image.new("RGBA", (tw, asc + desc + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 10
    for c, w in zip(txt, widths):
        d.text((x - f.getbbox(c)[0] if c != " " else x, 10), c, font=f, fill=fill + (255,))
        x += w + tracking * size
    return img


def paste(canvas, img, cx, cy, alpha):
    if alpha <= 0:
        return
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    sub = canvas[y0:y0 + h, x0:x0 + w]
    al = a[..., 3:4] / 255.0 * alpha
    sub[:] = sub * (1 - al) + a[..., [2, 1, 0]] * al


# ---- end card assets ----
L1 = text_img("8,000 METRES UP,", "Outfit-300.ttf", 46, tracking=0.22)
L2 = text_img("THERE WAS ONCE A SEA.", "Outfit-300.ttf", 46, tracking=0.22)
TAG = text_img("BORN IN HIMACHAL", "Outfit-500.ttf", 30, tracking=0.45, fill=(200, 205, 220))
logo = cv2.imread("brand/spraymax/assets/logo-wide.png", cv2.IMREAD_UNCHANGED)
ys, xs = np.nonzero(logo[..., 3] > 10)
logo = logo[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
lw = 560
logo = cv2.resize(logo, (lw, int(lw * logo.shape[0] / logo.shape[1])), interpolation=cv2.INTER_AREA)
LOGO = Image.fromarray(np.dstack([np.full(logo.shape[:2] + (3,), 255, np.uint8), logo[..., 3]]), "RGBA")
BG = np.zeros((H, W, 3), np.float32)
BG[:] = (14, 10, 8)                                           # near black, a touch of the studio's blue
vig = np.hypot((np.arange(W) - W / 2) / W, (np.arange(H)[:, None] - H * 0.45) / H)
BG *= (1.15 - 0.6 * vig)[..., None]


def ramp(t, t0, d):
    return float(np.clip((t - t0) / d, 0, 1)) ** 1.6


def end_card(t):
    c = BG.copy()
    paste(c, L1, W / 2, 760, ramp(t, END_IN + 0.10, 0.45))
    paste(c, L2, W / 2, 830, ramp(t, END_IN + 0.75, 0.45))
    a2 = ramp(t, END_IN + 1.75, 0.40)
    paste(c, LOGO, W / 2, 1060, a2)
    paste(c, TAG, W / 2, 1185, ramp(t, END_IN + 2.05, 0.40))
    return np.clip(c, 0, 255).astype(np.uint8)


# ---- render ----
tmp = out_path + ".video.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "15", "-preset", "slow",
                        "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
n_total = int(round(TOTAL * FPS))
frame_no = 0
for t0, t1, path, s0 in SHOTS:
    n = int(round(t1 * FPS)) - int(round(t0 * FPS))
    fr = read_frames(path, s0, n)
    for k, f in enumerate(fr):
        if frame_no < 5:                                     # the track opens on near-silence: rise from black
            f = (f.astype(np.float32) * (frame_no / 5) ** 1.5).astype(np.uint8)
        enc.stdin.write(f.tobytes())
        frame_no += 1
while frame_no < n_total:
    enc.stdin.write(end_card(frame_no / FPS).tobytes())
    frame_no += 1
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")

# ---- sound: the track, plus the studio splash and the sea spray's own hiss and waves under their shots ----
subprocess.run([
    "ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", music, "-i", HERO, "-i", OCEAN,
    "-filter_complex",
    f"[1:a]atrim=0:{TOTAL},asetpts=N/SR/TB,afade=t=out:st={TOTAL - 0.45}:d=0.45[m];"
    f"[2:a]atrim=0.55:1.67,asetpts=N/SR/TB,volume=0.35,adelay=6530|6530,apad,atrim=0:{TOTAL}[s];"
    f"[3:a]atrim=0.75:2.02,asetpts=N/SR/TB,volume=0.4,afade=t=in:d=0.05,afade=t=out:st=1.17:d=0.1,"
    f"adelay=4000|4000,apad,atrim=0:{TOTAL}[o];"
    f"[m][s][o]amix=inputs=3:normalize=0,loudnorm=I=-9:TP=-1.0:LRA=7[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
    "-shortest", out_path], check=True)
subprocess.run(["rm", "-f", tmp])
print(f"{frame_no} frames ({frame_no / FPS:.2f} s) -> {out_path}")
