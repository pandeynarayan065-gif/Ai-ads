#!/usr/bin/env python3
"""4x rebuild of the real Spraymax label for macro 3D shots.

label-flat.jpg is 1403 px for the full wrap (~11 px/mm): fine for packshots, soft when the camera is a
few centimetres from the wordmark. This upscales the artwork 4x (Lanczos + a light unsharp mask) and
redraws the wordmark from the vector-clean logo-wide.png (3840 px wide), rotated to read top to bottom
and fitted to the label's own wordmark box, in the label's own indigo.

  python3 video/blender/label_hires.py [out=video/assets/label-hires.jpg]
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "brand/spraymax/assets"
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "video/assets/label-hires.jpg"
K = 4

lab = cv2.imread(str(A / "label-flat.jpg"))
H, W = lab.shape[:2]

# the wordmark: strongly blue pixels in the centre column of the artwork
reg = lab[30:660, 600:800].astype(int)
ink = (reg[..., 0] - reg[..., 2]) > 60
ys, xs = np.nonzero(ink)
x0, x1, y0, y1 = xs.min() + 600, xs.max() + 600, ys.min() + 30, ys.max() + 30
px = reg[ink]
ink_bgr = np.median(px[px.sum(1) < np.percentile(px.sum(1), 30)], 0)   # the label's printed indigo (solid core)

big = cv2.resize(lab, (W * K, H * K), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
big = big + 0.6 * (big - cv2.GaussianBlur(big, (0, 0), 2.0))   # restore edge contrast lost to the upscale

# erase the old wordmark (it sits on plain white), then draw the clean one
bx0, bx1, by0, by1 = (x0 - 3) * K, (x1 + 4) * K, (y0 - 3) * K, (y1 + 4) * K
big[by0:by1, bx0:bx1] = 255.0
logo = cv2.imread(str(A / "logo-wide.png"), cv2.IMREAD_UNCHANGED)
a = logo[..., 3]
ly, lx = np.nonzero(a > 10)
alpha = a[ly.min():ly.max() + 1, lx.min():lx.max() + 1]
alpha = cv2.rotate(alpha, cv2.ROTATE_90_CLOCKWISE)            # reads top to bottom, like the bottle
tw, th = (x1 - x0 + 1) * K, (y1 - y0 + 1) * K
alpha = cv2.resize(alpha, (tw, th), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255.0
sub = big[y0 * K:y0 * K + th, x0 * K:x0 * K + tw]
sub[:] = sub * (1 - alpha) + ink_bgr[None, None, :] * alpha

out.parent.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(out), np.clip(big, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
print(f"wordmark box {x0}-{x1} x {y0}-{y1}, ink BGR {ink_bgr.round()}, {W * K}x{H * K} -> {out}")
