#!/usr/bin/env python3
"""Replace an AI-drawn bottle label with the real label artwork.

The bottle is modelled as a cylinder lying across the frame. Each image pixel on the
bottle is mapped to a point on the flat label artwork (around-the-bottle angle from
its distance to the axis; along-the-bottle position from its axial coordinate, with a
perspective term so constant-label-lines curve like the bottle's real label edge).
The original photo's lighting, colour cast, droplets and sheen are kept: the new art
is multiplied by the paper shading measured from the original label and the original
highlights are added back on top.

Geometry for ads/spraymax/sea-15s/images/still-2-float.png (flipped so the cap is on
the left), measured from the photo:
  top silhouette    y = 1162.9 + 0.1561 (x - 540)
  radius            200 px (the waterline hides the lower part of the bottle)
  perspective       label lines satisfy  t + A cos(psi + 14.6 deg) = const, with
                    A = 55.3 at the sticker edge (const 605.7) and 15.9 at the band end (1536.9)

Usage:
  python3 scripts/label_wrap.py <ai-still.png> <label-flat.jpg> <out.png>
"""
import sys

import cv2
import numpy as np

SRC, ART, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

SLOPE, Y540 = 0.1561, 1162.9          # top silhouette
R = 200.0                             # bottle radius in px
A_EDGE, A_END, PSI_M = 55.3, 15.9, np.radians(-14.6)
T_LABEL, T_BAND_END = 605.7, 1536.9
PSI_C = np.radians(39.0)              # where the label's front centre faces (above the view axis)
U_C = 696.0                           # front-panel centre in the trimmed artwork
V_LO, V_HI = 3.0, 950.0               # replace from just inside the sticker edge to past the band

img = cv2.imread(SRC, cv2.IMREAD_COLOR)[:, ::-1].astype(np.float32)          # flip: cap on the left
art = cv2.imread(ART, cv2.IMREAD_COLOR).astype(np.float32)[6:949, 6:1397]    # trim crop-mark borders
NV = art.shape[0]

th = np.arctan(SLOPE)
c, s = np.cos(th), np.sin(th)
p_ax = -540 * s + (Y540 + R / c) * c
k = (T_BAND_END - T_LABEL) / float(NV - 1)
dA = (A_END - A_EDGE) / float(NV - 1)          # curvature changes along the bottle (perspective)


def lin(x):
    x = np.clip(x / 255.0, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255.0


# ---- unwrapped (v, s) grid -> image coordinates -------------------------------------
S_HALF = int(R * np.pi / 2) - 2
s_vals = np.arange(-S_HALF, S_HALF + 1, dtype=np.float32)    # arc px, + = up toward the silhouette
v_vals = np.arange(0, NV + 10, dtype=np.float32)
vv, ss = np.meshgrid(v_vals, s_vals)
psi = ss / R
t = T_LABEL + vv * k - (A_EDGE + dA * vv) * np.cos(psi - PSI_M)
p = p_ax - R * np.sin(psi)
U = cv2.remap(img, (t * c - p * s).astype(np.float32), (t * s + p * c).astype(np.float32),
              cv2.INTER_LINEAR)

# ---- paper shading per arc position, from clean white label areas -----------------------
Lum = U.mean(axis=2)
sat = U.max(axis=2) - U.min(axis=2)
white = (sat < 60) & (Lum > 70)
white[:, 600:] = False                 # the AI's tagline and fake band
white[:, :30] = False                  # near the sticker edge
white &= ~cv2.dilate((~white).astype(np.uint8), np.ones((19, 19), np.uint8)).astype(bool)
shade = np.full((len(s_vals), 3), np.nan, np.float32)
for i in range(len(s_vals)):
    row = U[i][white[i]]
    if len(row) > 30:
        shade[i] = np.median(row, axis=0)
for ch in range(3):
    col = shade[:, ch]
    ok = ~np.isnan(col)
    col[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), col[ok])
    shade[:, ch] = cv2.GaussianBlur(col.reshape(-1, 1), (1, 0), 6).ravel()
SH = np.repeat(shade[:, None, :], len(v_vals), axis=1)

detail = np.where(white[..., None], U - SH, 0.0)             # droplets, sheen, paper grain
detail = cv2.GaussianBlur(np.clip(detail, -18, 120), (0, 0), 0.6)

# ---- new label: real artwork lit by the original shading ---------------------------------
u = (U_C + (ss - PSI_C * R) / k).astype(np.float32)
art_img = cv2.remap(art, u, vv.astype(np.float32), cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
art_img = cv2.GaussianBlur(art_img, (0, 0), 0.7)
alb = lin(art_img)
alb[:, vv[0] > NV - 1] *= 0.975                               # bare plastic past the label
NEW = np.clip(srgb(alb * lin(SH)) + detail, 0, 255)

# ---- back into the photo ----------------------------------------------------------------
x0, x1, y0, y1 = 300, 1520, 1080, 1760
gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
tt = gx * c + gy * s
dd = (-gx * s + gy * c) - p_ax
psi_i = np.arcsin(np.clip(-dd / R, -1, 1))
C = np.cos(psi_i - PSI_M)
v_i = (tt - T_LABEL + A_EDGE * C) / (k - dA * C)
patch = cv2.remap(NEW, v_i.astype(np.float32), (psi_i * R + S_HALF).astype(np.float32),
                  cv2.INTER_LINEAR)

og = img[y0:y1, x0:x1]
water = ((og[..., 1] - og[..., 2]) > 22) & ((og[..., 1] - og[..., 0]) > -5)   # BGR: G-R, G-B
water = cv2.morphologyEx(water.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
top_y = Y540 + SLOPE * (gx - 540)
mask = (gy > top_y + 1.5) & (np.abs(dd) < R - 1.5) & (v_i >= V_LO) & (v_i <= V_HI) & ~water
m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.6)
m *= np.clip((gy - top_y) / 4.0, 0, 1)                        # soft at the silhouette
m *= np.clip((v_i - V_LO) / 8.0, 0, 1) * np.clip((V_HI - v_i) / 3.0, 0, 1)

rng = np.random.default_rng(7)
patch = np.clip(patch + rng.normal(0, 2.2, patch.shape[:2]).astype(np.float32)[..., None], 0, 255)
out = img.copy()
out[y0:y1, x0:x1] = og * (1 - m[..., None]) + patch * m[..., None]
cv2.imwrite(OUT, np.clip(out, 0, 255).astype(np.uint8))
print(f"r={R} k={k:.4f} done -> {OUT}")
