#!/usr/bin/env python3
"""Clear dark specks/streaks (AI artifacts, birds, debris) from the sky of a locked-off shot.

The camera barely moves, so the per-pixel median of the top band over the clip is a clean
sky plate (sun included). In that band each frame shows the plate, except where the frame
is brighter than it (sun flicker, blowing snow), which is kept; the frame's own fine noise
is laid back on top so the plate does not look frozen. The band must contain only sky.

Usage: python3 scripts/clean_sky.py in.mp4 out.mp4 [--rows 330] [--crf 16]
"""
import argparse
import subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--rows", type=int, default=330, help="sky-only band height (px from the top)")
ap.add_argument("--crf", type=int, default=16)
a = ap.parse_args()

cap = cv2.VideoCapture(a.src)
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
H, W = frames[0].shape[:2]
R = a.rows
band = np.stack([f[:R] for f in frames]).astype(np.float32)
plate = np.median(band, axis=0)
Lp = plate.mean(axis=2)
Lps = cv2.GaussianBlur(Lp, (0, 0), 3)
fade = np.clip((R - 8 - np.arange(R, dtype=np.float32)) / 40.0, 0, 1)[:, None]   # hand back to the frame at the bottom
for i, f in enumerate(frames):
    b = band[i]
    d = cv2.GaussianBlur(b.mean(axis=2), (0, 0), 3) - Lps                     # smooth: no jagged steps in the sun's glow
    keep = np.clip((d - 12) / 18.0, 0, 1)                                        # clearly brighter: real light/snow
    noise = b - cv2.GaussianBlur(b, (0, 0), 1.0)
    noise = np.clip(noise, -6, 6)                                                    # grain only, not streak edges
    m = (1 - keep) * fade
    f[:R] = np.clip(b * (1 - m[..., None]) + (plate + noise) * m[..., None], 0, 255).astype(np.uint8)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", f"{fps}", "-i", "-", "-i", a.src, "-map", "0:v", "-map", "1:a?",
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                        "-c:a", "copy", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
for f in frames:
    enc.stdin.write(f.tobytes())
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")
print(f"sky band 0-{R}px replaced by a clean plate in {len(frames)} frames -> {a.out}")
