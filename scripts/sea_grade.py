#!/usr/bin/env python3
"""Grade an AI sea frame toward real clear-ocean colour and give it a real sky.

- Water: re-coloured toward a real clear-sea palette by distance (bright aqua over the
  sand in front, azure in the middle, deep blue at the horizon), keeping every ripple,
  caustic and sparkle of the original (luminance detail is carried over). Local contrast
  is added to the shallows so the sand reads through clear water.
- Sky: the blank white strip above the horizon becomes a blue gradient with soft,
  out-of-focus clouds; the original lens flare is kept.
- The bottle (cylinder band from the label_wrap geometry) is protected from the grade.

Usage: python3 scripts/sea_grade.py <in.png> <out.png>
"""
import sys

import cv2
import numpy as np

SRC, OUT = sys.argv[1], sys.argv[2]
img = cv2.imread(SRC, cv2.IMREAD_COLOR).astype(np.float32)          # BGR
H, W = img.shape[:2]
gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---- horizon ----
hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
sat_rows = np.median(hsv[:H // 4, W // 16:-W // 16, 1], axis=1)
HZ = int(np.argmax(np.diff(cv2.GaussianBlur(sat_rows.reshape(-1, 1), (1, 0), 2).ravel())))

# ---- bottle protection (same cylinder as scripts/label_wrap.py, flipped frame) ----
SLOPE, Y540, R = 0.1561, 1162.9, 200.0
top_y = Y540 + SLOPE * (gx - 540)
c = np.cos(np.arctan(SLOPE))
waterish = ((img[..., 1] - img[..., 2]) > 22) & ((img[..., 1] - img[..., 0]) > -5)
bottle = (gy > top_y - 4) & (gy < top_y + 2 * R / c) & (gx > 330) & ~waterish
cap_end = np.zeros((H, W), np.uint8)                               # collar + shoulder dome (cap end)
cv2.fillPoly(cap_end, [np.array([[0, 1178], [235, 1178], [262, 1158], [310, 1142], [430, 1136],
                                 [430, 1505], [300, 1478], [235, 1430], [0, 1412]], np.int32)], 1)
bottle = cv2.morphologyEx((bottle | cap_end.astype(bool)).astype(np.uint8), cv2.MORPH_CLOSE,
                          np.ones((9, 9), np.uint8))
protect = cv2.GaussianBlur(bottle.astype(np.float32), (0, 0), 2.5)

# ---- water weight ----
h, s = hsv[..., 0] * 2.0, hsv[..., 1]
w = smooth(8, 30, s) * smooth(140, 155, h) * (1 - smooth(212, 226, h)) * (gy > HZ + 1)
w *= 1 - protect

# ---- palette by distance (RGB keyframes, converted to BGR) ----
depth = np.clip((gy - HZ) / (H - HZ), 0, 1)
keys = np.array([0.00, 0.12, 0.30, 0.55, 0.80, 1.00])
cols = np.array([[30, 88, 140], [38, 108, 160], [52, 140, 182], [78, 172, 196],
                 [105, 192, 202], [118, 200, 204]], np.float32)[:, ::-1]
pal = np.stack([np.interp(depth, keys, cols[:, i]) for i in range(3)], -1)

lum = img.mean(axis=2)
row_mean = np.array([lum[y][w[y] > 0.5].mean() if (w[y] > 0.5).sum() > 50 else np.nan for y in range(H)])
ok = ~np.isnan(row_mean)
row_mean[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), row_mean[ok])
row_mean = cv2.GaussianBlur(row_mean.reshape(-1, 1).astype(np.float32), (1, 0), 25).ravel()
ratio = (lum / row_mean[:, None])[..., None]
pal_ref = pal.mean(axis=2, keepdims=True)
new = pal + (ratio - 1.0) * np.maximum(pal_ref, 60) * 1.15        # carry ripples and caustics
spec = smooth(200, 245, lum) * smooth(60, 25, hsv[..., 1])          # sparkles stay white
new = new * (1 - spec[..., None]) + img * spec[..., None]
# near water: a gentle shift toward aqua-blue instead of the palette (keeps sand and caustics natural)
hh = np.mod(h + 11.0, 360) / 2.0
ss2 = np.clip(s * 1.12, 0, 255)
gentle = cv2.cvtColor(np.stack([hh, ss2, hsv[..., 2]], -1).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
alpha = (0.9 * (1 - smooth(0.22, 0.62, depth)))[..., None]       # palette far away, gentle up close
graded = new * alpha + gentle * (1 - alpha)
out = img * (1 - w[..., None]) + graded * w[..., None]

# turbidity: real sea water scatters light, so the sand and caustics show through a blue veil
# (observed = bottom * T + water body * (1 - T)); surface sparkles sit on top and are kept
TURB = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
sea = ((gy > HZ + 1) & (protect < 0.5)).astype(np.float32)
body = np.stack([np.interp(depth, [0.3, 0.6, 1.0], c) for c in ([170, 175, 180], [125, 135, 142], [45, 50, 56])], -1)
veil = TURB * (0.42 * smooth(0.3, 1.0, depth))                   # stronger in front where we see the sand
veil = (veil * sea * (1 - spec))[..., None]
soft = cv2.GaussianBlur(out, (0, 0), 1.2)                          # scattering also softens the bottom detail
out = np.where(veil > 0, soft * (1 - veil) + body * veil, out)

# ---- sky ----
rng = np.random.default_rng(11)
sky_h = HZ + 6
t = np.linspace(0, 1, sky_h, dtype=np.float32)[:, None]
top_c = np.array([196, 142, 88], np.float32)        # BGR
low_c = np.array([224, 210, 190], np.float32)
grad = (top_c * (1 - t ** 0.6) + low_c * t ** 0.6)[:, None, :] * np.ones((1, W, 1), np.float32)
noise = np.zeros((sky_h, W), np.float32)
for scale, amp in ((70, 1.0), (30, 0.45), (12, 0.2)):
    n = rng.normal(0, 1, (sky_h // 3 + 8, W // 3 + 8)).astype(np.float32)
    n = cv2.resize(n, (W + 24, sky_h + 24), interpolation=cv2.INTER_CUBIC)[12:12 + sky_h, 12:12 + W]
    noise += amp * cv2.GaussianBlur(n, (0, 0), scale, sigmaY=scale * 0.35)
noise = (noise - noise.mean()) / (noise.std() + 1e-6)
band = np.exp(-((t.ravel() - 0.85) / 0.22) ** 2)[:, None]          # low clouds sit near the horizon
cover = smooth(0.3, 1.6, noise * 0.8 + band * 1.0 - 0.1) * 0.75
cover = cv2.GaussianBlur(cover, (0, 0), 22, sigmaY=12)              # far out of focus
cloud = np.array([236, 234, 230], np.float32)
sky = grad * (1 - cover[..., None]) + cloud * cover[..., None]
orig_sky = img[:sky_h]
flare = np.clip(orig_sky - cv2.GaussianBlur(orig_sky, (0, 0), 25), 0, 255)
sky = sky + flare * 1.2 + rng.normal(0, 1.6, sky.shape[:2]).astype(np.float32)[..., None]
# keep the sun's glow where the original frame had it (just outside the frame, top right)
g0 = cv2.GaussianBlur(img[:sky_h].mean(axis=2), (0, 0), 40)
glow = np.clip(g0 - np.percentile(g0, 40), 0, None)
sky = sky + (glow / (glow.max() + 1e-6) * 55.0)[..., None] * np.array([0.95, 1.0, 1.0], np.float32)
fade = smooth(HZ - 4, HZ + 4, np.arange(sky_h, dtype=np.float32))[:, None, None]
out[:sky_h] = sky * (1 - fade) + out[:sky_h] * fade

cv2.imwrite(OUT, np.clip(out, 0, 255).astype(np.uint8))
print(f"horizon y={HZ} -> {OUT}")
