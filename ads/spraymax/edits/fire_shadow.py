#!/usr/bin/env python3
"""Relight the fire-behind shot: the fire is behind him, so his face should fall into shadow and the smoky
background should go darker, while the flames and the warm rim on his hair stay bright.

  python3 fire_shadow.py <in.mp4> <out.mp4> --start 958 --end 1000 [--face 0.78 --bg 0.5]
Frames outside start..end are copied untouched; audio is copied.
"""
import argparse
import subprocess

import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def face_centre(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sk = (r > .25) & (r < .85) & (g > .12) & (g < r * .8) & (b < g) & (r - b > .12)
    reg = np.zeros(sk.shape, bool)
    reg[550:950, 330:780] = True
    ys, xs = np.nonzero(sk & reg)
    return xs.mean(), ys.mean()


def relight(a, cx, cy, face, bg):
    L = a.mean(2)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 1) darks and mid-tones go down, flames (bright) stay: background smoke, coat and wall get moodier
    keep = smoothstep(0.30, 0.78, L)
    darken = bg + (1 - bg) * keep
    # 2) face shadow: a soft oval over the face, heavier on the left side (light is behind and to his left-rear,
    #    so a sliver of fire light stays on his right cheek edge)
    oval = np.exp(-(((xx - cx) / 175) ** 2 + ((yy - cy) / 215) ** 2) ** 1.6)
    side = 0.55 + 0.45 * smoothstep(cx + 90, cx - 90, xx + (yy - cy) * 0.35)  # diagonal edge
    shade = 1 - face * oval * side
    # keep the hot rim on the hair/edges: saturated bright red-orange pixels are protected
    rim = smoothstep(0.55, 0.8, a[..., 0]) * smoothstep(0.25, 0.5, a[..., 0] - a[..., 2])
    m = darken * shade
    m = m + (1 - m) * rim * 0.7
    m = np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    out = a * m[..., None]
    # cooler, deeper shadows so the orange fire separates
    sh = (1 - smoothstep(0.0, 0.25, out.mean(2)))[..., None] * 0.06
    out = out * (1 - sh) + sh * np.array([0.02, 0.03, 0.06])
    return np.clip(out, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--start", type=int, default=958)
    ap.add_argument("--end", type=int, default=1000)
    ap.add_argument("--face", type=float, default=0.78, help="how dark the face shadow gets (0..1)")
    ap.add_argument("--bg", type=float, default=0.5, help="multiplier on darks (lower = darker)")
    a = ap.parse_args()
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                          "-of", "csv=p=0", a.src], capture_output=True, text=True).stdout.strip()
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", fps, "-i", "-", "-i", a.src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-crf", "10", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", a.out],
                           stdin=subprocess.PIPE)
    n, fs, c = 0, W * H * 3, None
    while True:
        b = dec.stdout.read(fs)
        if len(b) < fs:
            break
        if a.start <= n <= a.end:
            f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32) / 255
            p = np.array(face_centre(f))
            c = p if c is None else c * 0.7 + p * 0.3  # smoothed so the shadow doesn't jitter
            b = (relight(f, c[0], c[1], a.face, a.bg) * 255 + 0.5).astype(np.uint8).tobytes()
        enc.stdin.write(b)
        n += 1
    enc.stdin.close()
    enc.wait()
    print(f"Saved {a.out}: {n} frames, relit {a.start}-{a.end}")


if __name__ == "__main__":
    main()
