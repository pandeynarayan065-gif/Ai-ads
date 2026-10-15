#!/usr/bin/env python3
"""Slow motion-control push-in for a clip whose camera Veo left still: ease in/out from 1.00 to ZOOM, drifting the
centre to (CX, CY) by the end, with a touch of sharpening to make up for the enlargement. Audio copied from IN.

  python3 ads/spraymax/studio-hero/push_in.py in.mp4 out.mp4 [zoom=1.15] [end_cx=540] [end_cy=840]
"""
import subprocess
import sys

import cv2
import numpy as np

src, out_path = sys.argv[1], sys.argv[2]
ZOOM = float(sys.argv[3]) if len(sys.argv) > 3 else 1.15
CX = float(sys.argv[4]) if len(sys.argv) > 4 else 540.0
CY = float(sys.argv[5]) if len(sys.argv) > 5 else 840.0

cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
tmp = out_path + ".video.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                        "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
i = 0
while True:
    ok, f = cap.read()
    if not ok:
        break
    t = i / max(1, N - 1)
    e = t * t * (3 - 2 * t)
    s = 1.0 + (ZOOM - 1.0) * e
    cx, cy = W / 2 + (CX - W / 2) * e, H / 2 + (CY - H / 2) * e
    A = np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
    out = cv2.warpAffine(f, A, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    if s > 1.001:
        k = 0.35 * (s - 1) / (ZOOM - 1)
        out = cv2.addWeighted(out, 1 + k, cv2.GaussianBlur(out, (0, 0), 1.0), -k, 0)
    enc.stdin.write(out.tobytes())
    i += 1
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", src, "-map", "0:v", "-map", "1:a?", "-c", "copy",
                "-shortest", out_path], check=True)
subprocess.run(["rm", "-f", tmp])
print(f"push-in x{ZOOM} over {i} frames -> {out_path}")
