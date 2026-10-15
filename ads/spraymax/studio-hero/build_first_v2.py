#!/usr/bin/env python3
"""First frame v2 for the studio hero: the bottle at the REAL bottle's proportions, with the label as a real
sticker and the clear overcap.

The v1 first frame (from the mockup) has a squat bottle: next to the real bottle at the same label size its straight
body is ~14% too short, so the label runs from over the shoulder down to the base. On the real bottle
(brand/spraymax/assets/bottle-real-hand-close.jpg, measured against the wordmark length WL):
  shoulder ends 0.10 WL above the wordmark; the sticker's top edge 0.05 WL above it (just under the shoulder);
  the sticker ends at the bottom of the wave band; bare plastic below it 0.11 WL; body width 0.68 WL.

Here, from images/hero-first.jpg (v1) with its overcap already made clear (clear_cap.py):
- the old bottle is taken off the backdrop (each row filled from the backdrop on both sides);
- the cap, collar and shoulder are kept as they are (rows above the old label);
- the straight body is rebuilt longer (shoulder end -> base 0.93 -> 1.80 WL), lit like the old body (its own
  column x row light, read off the old label's plain paper), with the real label (label-flat.jpg, the full wrap
  art: white side margins and the back-label text/icons at the edges, as on the real bottle) wrapped round it as
  a sticker: a touch whiter and smoother than the greyish plastic, a fine bright line along its top edge and a
  faint shadow under its bottom edge, bare plastic above and below;
- the whole bottle is scaled 0.93 so the taller bottle keeps the same headroom, standing on the same spot;
- the splash droplets along the base are put back in front.

  python3 ads/spraymax/studio-hero/build_first_v2.py cap-cleared-hero-first.png out.png
"""
import sys

import cv2
import numpy as np

src, out_path = sys.argv[1], sys.argv[2]
ART = "brand/spraymax/assets/label-flat.jpg"
ART_U_C, ART_WM_TOP, ART_WM_BOTTOM, ART_H = 702.0, 48.0, 628.0, 955.0

I = cv2.imread(src).astype(np.float32)
H, W = I.shape[:2]
XC = 542.5                                   # bottle axis
R_BODY = 181.5                               # body radius (px)
SPLIT = 660                                  # old rows above this are kept (cap, collar, shoulder)
SHOULDER_END = 700.0                         # body is straight below this
OLD_BASE = 1533.0
WL = 2 * R_BODY / 0.68                       # wordmark length at the real width ratio
K = WL / (ART_WM_BOTTOM - ART_WM_TOP)        # px per art row
GAP_TOP = 0.05 * WL                          # sticker top edge below the shoulder end
GAP_BOTTOM = 0.11 * WL                       # bare plastic under the sticker
STK_TOP = SHOULDER_END + GAP_TOP
STK_BOT = STK_TOP + ART_H * K
NEW_BASE = STK_BOT + GAP_BOTTOM              # base, in the stretched (pre-scale) coordinates
SCALE = 0.93

# old silhouette: (y, left x, right x), measured on hero-first.jpg
SIL = [(126, 470, 616), (129.5, 480, 606), (135, 462, 624), (145, 456, 629), (160, 454.5, 630), (385, 454.5, 630),
       (390, 437, 645), (545, 437, 645), (548, 443, 640), (560, 426, 658), (580, 402, 682), (600, 385, 699),
       (620, 374, 710), (640, 367, 718), (660, 363, 722), (690, 361, 724), (OLD_BASE, 361, 724)]


def sil_poly(rows, base=None):
    pts_l = [(l, y) for y, l, r in rows]
    pts_r = [(r, y) for y, l, r in rows][::-1]
    return np.array(pts_l + pts_r, np.float64)


def poly_mask(poly, shape, soft=0.7):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.round(poly * 8).astype(np.int32)], 255, shift=3, lineType=cv2.LINE_AA)
    m = m.astype(np.float32) / 255
    return cv2.GaussianBlur(m, (0, 0), soft) if soft else m


def lin(x):
    x = np.clip(x / 255.0, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255.0


rng = np.random.default_rng(5)
old_mask = poly_mask(sil_poly(SIL), (H, W), 0.0)
L = I.mean(axis=2)

# ---- 1. backdrop without the old bottle: each row filled from both sides ----
bg = I.copy()
cut = cv2.dilate((old_mask > 0.01).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
for y in range(100, int(OLD_BASE) + 4):
    xs = np.flatnonzero(cut[y])
    if not len(xs):
        continue
    a0, a1 = xs.min(), xs.max()
    lc = np.median(I[y, max(0, a0 - 18):a0 - 3], axis=0)
    rc = np.median(I[y, a1 + 3:min(W, a1 + 18)], axis=0)
    t = np.linspace(0, 1, a1 - a0 + 1)[:, None]
    bg[y, a0:a1 + 1] = lc * (1 - t) + rc * t
smooth = cv2.GaussianBlur(bg, (0, 0), 4)
hp_bd = I[200:1300, 150:330] - cv2.GaussianBlur(I[200:1300, 150:330], (0, 0), 1.5)
sig_bd = float(np.median(np.abs(hp_bd)) * 1.4826)
noise = cv2.GaussianBlur(rng.normal(0, sig_bd, I.shape).astype(np.float32), (0, 0), 0.7)
cutf = cv2.GaussianBlur(cut.astype(np.float32), (0, 0), 1.5)[..., None]
bg = I * (1 - cutf) + (smooth + noise) * cutf

# ---- 2. light on the old body, read off the old label's plain paper (rows 700-1250) ----
sat = I.max(axis=2) - I.min(axis=2)
bh = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, np.ones((15, 15), np.uint8))
paper = (old_mask > 0.99) & (sat < 45) & (L > 120) & (bh < 6)
paper[:700], paper[1250:] = False, False
cols = np.arange(W)
C = np.full((W, 3), np.nan, np.float32)
for x in range(355, 731):
    v = I[:, x][paper[:, x]]
    if len(v) > 40:
        C[x] = np.median(v, axis=0)
ok = ~np.isnan(C[:, 0])
for c in range(3):
    C[~ok, c] = np.interp(cols[~ok], cols[ok], C[ok, c])
    C[:, c] = cv2.GaussianBlur(C[:, c].reshape(1, -1), (0, 0), 1.2).ravel()
Lc = C.mean(axis=1)
Rrow = np.full(H, np.nan, np.float32)
for y in range(640, 1250):
    m = paper[y] & (np.abs(cols - XC) < 0.75 * R_BODY)
    if m.sum() > 20:
        Rrow[y] = np.median(L[y][m] / Lc[m])
yy = np.flatnonzero(~np.isnan(Rrow))
pfit = np.polyfit(yy, Rrow[yy], 1)                        # smooth vertical falloff, extended down the new body
print(f"old body light: column profile {Lc[365]:.0f}..{Lc[int(XC)]:.0f}..{Lc[720]:.0f}, "
      f"row trend {pfit[0] * 100:+.3f}%/100px")

# ---- 3. the new bottle, in stretched coordinates (base at NEW_BASE) ----
HS = int(NEW_BASE) + 40
layer = np.zeros((HS, W, 3), np.float32)
alpha = np.zeros((HS, W), np.float32)
layer[:SPLIT + 8] = I[:SPLIT + 8]
alpha[:SPLIT + 8] = old_mask[:SPLIT + 8]

gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(HS, dtype=np.float32))
body_rows = gy >= SPLIT
# silhouette of the body: shoulder flank 660->700 as in the old bottle, straight below, rounded base corners
half = np.interp(gy, [SPLIT, 690, NEW_BASE], [(722 - 363) / 2, R_BODY, R_BODY]).astype(np.float32)
CORNER = 7.0
dx_edge = half - np.abs(gx - XC)
dy_base = NEW_BASE - gy
inside = np.minimum(dx_edge, dy_base)
cz = (dx_edge < CORNER) & (dy_base < CORNER)
inside = np.where(cz, CORNER - np.hypot(CORNER - dx_edge, CORNER - dy_base), inside)
a_body = np.clip(inside + 0.5, 0, 1) * body_rows
# light: column profile (by angle round the cylinder, so the narrow shoulder rows map onto the body's columns)
u_body = np.clip((gx - XC) / np.maximum(half, 1), -1, 1)
src_x = (XC + u_body * R_BODY).astype(np.float32)
Cmap = np.stack([np.interp(src_x, cols, C[:, c]) for c in range(3)], axis=-1)
Rmap = np.polyval(pfit, np.clip(gy, 640, 1250) + np.clip(gy - 1250, 0, None) * 0.5)   # falloff eases out low down
light = lin(Cmap) * Rmap[..., None] ** 2.2
# base: a little ambient occlusion where the bottle meets the slate
ao = 1 - 0.28 * np.clip(1 - dy_base / 12.0, 0, 1) ** 1.5
light *= ao[..., None]

# the sticker: real wrap-around art on the cylinder
art = cv2.imread(ART).astype(np.float32)
art[:9] = 255.0                                             # (print border line in the art file)
paper_art = np.median(art[60:600, 480:640].reshape(-1, 3), axis=0)
k_u = R_BODY / K                                            # art radius
s = R_BODY * np.arcsin(np.clip((gx - XC) / R_BODY, -1, 1))
u = (ART_U_C + s / K).astype(np.float32)
v = ((gy - STK_TOP) / K).astype(np.float32)
A = cv2.remap(art, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
A = cv2.GaussianBlur(A, (0, 0), 0.7)                        # the frame is a 1.4x upscale: match its softness
alb = lin(A) / lin(paper_art)[None, None, :]
in_stk = np.clip(gy - STK_TOP + 0.5, 0, 1) * np.clip(STK_BOT - gy + 0.5, 0, 1)
STICKER_WHITE = np.array([1.035, 1.035, 1.035], np.float32)  # film label: a touch whiter than the plastic
PLASTIC = np.array([0.965, 0.975, 0.985], np.float32)        # HDPE: a touch greyer and warmer (BGR)
body_lin = light * (alb * STICKER_WHITE * in_stk[..., None] + PLASTIC * (1 - in_stk[..., None]))
# sticker edges: a fine bright line along the top edge, a faint shadow line on the plastic under the bottom edge
edge_top = np.exp(-((gy - STK_TOP - 0.6) / 0.7) ** 2)
edge_bot = np.exp(-((gy - STK_BOT - 1.4) / 1.0) ** 2)
edge_fall = np.clip(np.cos(np.arcsin(np.clip((gx - XC) / R_BODY, -1, 1))), 0, 1) ** 0.5
body_lin *= (1 + 0.10 * edge_top * edge_fall)[..., None]
body_lin *= (1 - 0.16 * edge_bot)[..., None]
body = srgb(body_lin)
# grain like the old body's paper
hp = (I - cv2.GaussianBlur(I, (0, 0), 1.2))[paper]
sig = float(np.median(np.abs(hp)) * 1.4826) + 0.3
body += cv2.GaussianBlur(rng.normal(0, sig, body.shape).astype(np.float32), (0, 0), 0.6)
# match the rebuilt body to the kept shoulder at the seam (per column), fading the correction out downwards,
# then hand over across 8 rows, so there is no visible seam at SPLIT
ref_rows = I[SPLIT:SPLIT + 8].mean(axis=0)
new_rows = body[SPLIT:SPLIT + 8].mean(axis=0)
okc = old_mask[SPLIT + 4] > 0.99
ratio = np.ones((W, 3), np.float32)
ratio[okc] = (ref_rows[okc] + 1) / (new_rows[okc] + 1)
for c in range(3):
    ratio[:, c] = cv2.GaussianBlur(ratio[:, c].reshape(1, -1), (0, 0), 4).ravel()
fade = np.clip(1 - (gy - SPLIT) / 160.0, 0, 1) ** 1.5
body = body * (1 + (ratio[None, :, :] - 1) * fade[..., None])
seam = np.clip((gy - SPLIT) / 8.0, 0, 1)[..., None]
layer = np.where(body_rows[..., None], layer * (1 - seam) + body * seam, layer)
alpha = np.maximum(alpha, a_body)

# ---- 4. stand it on the same spot, scaled so the taller bottle keeps the headroom ----
M = np.float32([[SCALE, 0, XC - SCALE * XC], [0, SCALE, OLD_BASE - SCALE * NEW_BASE]])
lay_f = cv2.warpAffine(layer, M, (W, H), flags=cv2.INTER_AREA, borderValue=0)
a_f = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
out = bg * (1 - a_f[..., None]) + lay_f * a_f[..., None]

# ---- 5. the splash droplets along the base back in front ----
zone = np.zeros((H, W), bool)
zone[int(OLD_BASE) - 3:int(OLD_BASE) + 8, 330:760] = True        # on the slate, along the contact line
loc = cv2.GaussianBlur(I, (0, 0), 6).mean(axis=2)
drop = zone & ((L - loc) > 28) & (sat < 40) & (L > 110)            # clear water, not the old wave print
drop = cv2.dilate(drop.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
drop = cv2.GaussianBlur(drop, (0, 0), 0.8)[..., None] * (old_mask > 0.5)[..., None]
out = out * (1 - drop) + I * drop

cv2.imwrite(out_path, np.clip(out, 0, 255).round().astype(np.uint8))
top_y = OLD_BASE - SCALE * (NEW_BASE - 126)
print(f"WL {WL * SCALE:.0f}px, sticker {OLD_BASE - SCALE * (NEW_BASE - STK_TOP):.0f}-{OLD_BASE - SCALE * (NEW_BASE - STK_BOT):.0f}, "
      f"bare plastic {SCALE * GAP_BOTTOM:.0f}px, cap top {top_y:.0f}, width {2 * R_BODY * SCALE:.0f}px")
