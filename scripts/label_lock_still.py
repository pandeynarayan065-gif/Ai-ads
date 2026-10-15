"""Put the real Spraymax label on the AI bottle in one still (upright bottle, label facing camera).

The bottle's own light is read off the AI's plain paper (column x row shading, plus a low-frequency
residual for local shadows), the real label art is wrapped round a cylinder and multiplied by that
light in linear RGB, the AI's ink colour in this light sets the new ink colour, and the AI's fine
detail (grain, water droplets) is carried back. Hair strands and fingers over the bottle are kept.

Use it on a first frame before animating it, so the video starts from the exact label. The label's
length can be fitted to an AI bottle that is longer than the real one (--ky, frame px per art row)
and bare plastic fills the rest down to --pad-to, covering the AI's own band.

Spray, ocean (Nano Banana still, bottle upright, label to camera, hand at top right):
  python3 scripts/label_lock_still.py fixed.png ads/spraymax/k2-15s/images/spray-ocean-first.png \
      --xc 796.5 --r 74.5 --xc-bottom 791.5 --r-bottom 76.5 --y-top 852 --ky 0.42 --pad-to 1292 \
      --wm-x 789 --margin 2
"""
import argparse
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--art", default="brand/spraymax/assets/label-flat.jpg")
ap.add_argument("--art-u-c", type=float, default=702.0)
ap.add_argument("--art-radius", type=float, default=192.3)
ap.add_argument("--xc", type=float, required=True); ap.add_argument("--r", type=float, required=True)
ap.add_argument("--xc-bottom", type=float, required=True); ap.add_argument("--r-bottom", type=float, required=True)
ap.add_argument("--y-top", type=float, required=True, help="label top row")
ap.add_argument("--ky", type=float, required=True, help="frame px per art row")
ap.add_argument("--pad-to", type=float, required=True, help="bare plastic below the label down to this row")
ap.add_argument("--wm-x", type=float, required=True, help="frame x of the wordmark centre")
ap.add_argument("--ai-band", default="1164,1287", help="AI band rows (no paper there)")
ap.add_argument("--paper-rows", default="840,1160")
ap.add_argument("--margin", type=float, default=4.0)
ap.add_argument("--debug", default=None)
a = ap.parse_args()

I = cv2.imread(a.src).astype(np.float32)
H, W = I.shape[:2]


def lin(x):
    x = np.clip(x / 255.0, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255.0


# ---- art: band wraps to the outline (mirrored sideways), as on the real bottle ----
art = cv2.imread(a.art).astype(np.float32)
art[:9] = 255.0
b0, b1 = 703, 948
blue = (art[b0:b1, :, 0] - art[b0:b1, :, 2]) > 25
cb = np.flatnonzero(blue.mean(axis=0) > 0.5)
c0, c1 = cb.min(), cb.max()
band = art[b0:b1, c0:c1 + 1]
w_ = c1 - c0 + 1
left = band[:, ::-1][:, :min(c0, w_)][:, ::-1]
right = band[:, ::-1][:, :min(art.shape[1] - 1 - c1, w_)]
art[b0:b1, c0 - left.shape[1]:c0] = left
art[b0:b1, c1 + 1:c1 + 1 + right.shape[1]] = right
paper_art = np.median(art[60:600, 480:640].reshape(-1, 3), axis=0)
print("art paper", paper_art)
print_mask = ((art[..., 0] - art[..., 2]) > 50) & (art.mean(axis=2) < 170)
print_mask[640:] = False

# ---- geometry ----
y_top, ky = a.y_top, a.ky
y_bot = a.pad_to
ya, yb = int(y_top) - 2, int(np.ceil(y_bot)) + 3
xa, xb = int(min(a.xc - a.r, a.xc_bottom - a.r_bottom)) - 3, int(max(a.xc + a.r, a.xc_bottom + a.r_bottom)) + 4
gx, gy = np.meshgrid(np.arange(xa, xb, dtype=np.float32), np.arange(ya, yb, dtype=np.float32))
t = (gy - y_top) / (y_bot - y_top)
xc_y = a.xc + (a.xc_bottom - a.xc) * t
r_y = a.r + (a.r_bottom - a.r) * t
k_u = r_y / a.art_radius
s = r_y * np.arcsin(np.clip((gx - xc_y) / r_y, -1, 1))
s_c = r_y * np.arcsin(np.clip((a.wm_x - xc_y) / r_y, -1, 1))
u = (a.art_u_c + (s - s_c) / k_u).astype(np.float32)
v = ((gy - y_top) / ky).astype(np.float32)
NV = art.shape[0]
art_p = np.vstack([art, np.tile(paper_art * 0.985, (400, art.shape[1], 1))])   # bare plastic below
A = cv2.remap(art_p, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
A = cv2.GaussianBlur(A, (0, 0), 0.4)
PRINT = cv2.remap(print_mask.astype(np.float32), u, v, cv2.INTER_LINEAR) > 0.5
alb = lin(A) / lin(paper_art)[None, None, :]

box = I[ya:yb, xa:xb]
L = box.mean(axis=2)
Bc, Gc, Rc = box[..., 0], box[..., 1], box[..., 2]
sat = box.max(axis=2) - box.min(axis=2)
inside = np.abs(gx - xc_y) < r_y - a.margin

# ---- what is on top of the bottle: hair strands and fingers (warm), droplets (bright specks) ----
lab = cv2.cvtColor(np.clip(box, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
aa, bb = lab[..., 1], lab[..., 2]
Lmed0 = cv2.medianBlur(np.clip(L, 0, 255).astype(np.uint8), 41).astype(np.float32)
ref = inside & (sat < 60) & (L > 60) & (np.abs(L - Lmed0) < 10)
a0, b0 = np.median(aa[ref]), np.median(bb[ref])
print("paper a*b*", a0, b0)
skin = (aa > a0 + 9) & (bb > b0 - 2) & inside                                       # lit fingers
dark_warm = (L < Lmed0 - 20) & ((aa > a0 + 3) | (bb > b0 + 4)) & (bb > b0 - 4) & ((Bc - Rc) < 0) & inside   # hair strands, shaded hand
keep = skin | dark_warm
keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
keep = cv2.dilate(keep, np.ones((3, 3), np.uint8)).astype(np.float32)
keep = cv2.GaussianBlur(keep, (0, 0), 2.0) > 0.35                 # smooth outline, no stair-steps

# ---- the AI's old print ----
ai_blue = ((Bc - Rc) > 18) & inside
ai_band = (gy >= int(a.ai_band.split(",")[0]) - 3) & (gy <= int(a.ai_band.split(",")[1]) + 3)

# ---- paper shading: column x row from plain paper, plus a smooth residual ----
pr0, pr1 = (int(x) for x in a.paper_rows.split(","))
hp = L - cv2.GaussianBlur(L, (0, 0), 2)
speck = (hp > 7) & inside
speck = cv2.dilate(speck.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
Lmed = cv2.medianBlur(np.clip(L, 0, 255).astype(np.uint8), 41).astype(np.float32)   # paper level, ink ignored
ai_dark = inside & (L < Lmed - 22)                                  # the AI's black print
ink_near = cv2.dilate((ai_blue | ai_dark).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
paper = inside & (sat < 60) & (L > 60) & ~ink_near & ~keep & ~speck & ~ai_band
paper &= ((gy >= pr0) & (gy <= pr1)) | (gy > int(a.ai_band.split(",")[1]) + 4)
BH, BW = box.shape[:2]
col = np.full((BW, 3), np.nan, np.float32)
for j in range(BW):
    c = box[:, j][paper[:, j] & (gy[:, j] <= pr1)]
    if len(c) > 15:
        col[j] = np.median(c, axis=0)
for ch in range(3):
    cc = col[:, ch]; ok = ~np.isnan(cc)
    cc[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), cc[ok])
    col[:, ch] = cv2.GaussianBlur(cc.reshape(1, -1), (0, 0), 2).ravel()
colL = col.mean(axis=1)
rowg = np.full(BH, np.nan, np.float32)
for i in range(BH):
    m = paper[i]
    if m.sum() > 12:
        rowg[i] = np.median(L[i][m] / colL[m])
ok = ~np.isnan(rowg)
rowg[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), rowg[ok])
rowg = cv2.GaussianBlur(rowg.reshape(-1, 1), (0, 0), 10).ravel()
S = col[None, :, :] * rowg[:, None, None]
S_lin = lin(S)
res = np.where(paper[..., None], lin(box) - S_lin, 0)
pw = paper.astype(np.float32)
low = cv2.GaussianBlur(res, (0, 0), 7) / (cv2.GaussianBlur(pw, (0, 0), 7)[..., None] + 1e-3)
conf = np.clip(cv2.GaussianBlur(pw, (0, 0), 7) / 0.25, 0, 1)[..., None]
low = np.clip(low, -0.06, 0.06) * conf
light = np.clip(S_lin + low, 0, None)

new_lin = alb * light
new = srgb(new_lin)

# ink: match the AI's own indigo as lit in this frame
old_ink = ai_blue & ~ai_band & (L < Lmed - 25)
if old_ink.sum() > 300 and PRINT.sum() > 300:
    fac = box[old_ink].mean(axis=0) / (new[PRINT].mean(axis=0) + 1e-3)
    fac = 1 + (np.clip(fac, 0.6, 1.6) - 1) * 0.7
    print("ink factor", fac)
    pm = cv2.GaussianBlur(PRINT.astype(np.float32), (0, 0), 0.7)[..., None]
    new = new * (1 - pm) + new * fac[None, None, :] * pm

# fine detail: the AI's own grain and droplets on plain paper; matched grain elsewhere
hp3 = box - cv2.GaussianBlur(box, (0, 0), 1.6)
sig = np.std(hp3[paper & ~speck], axis=0)
print("grain sigma", sig)
rng = np.random.default_rng(3)
noise = rng.normal(0, 1, box.shape).astype(np.float32)
noise = cv2.GaussianBlur(noise, (0, 0), 0.6)
noise *= (sig / (noise.reshape(-1, 3).std(axis=0) + 1e-6))[None, None, :]
carry_ok = paper | (speck & ~ink_near & ~ai_band)
cw = cv2.GaussianBlur(carry_ok.astype(np.float32), (0, 0), 1.0)[..., None]
new = new + hp3 * cw + noise * (1 - cw)

# blend: inside the silhouette, not over hair/fingers, feathered at the label's top and the pad's end
wx = np.clip((r_y - a.margin - np.abs(gx - xc_y)) / 2.5, 0, 1)
wy = np.clip((gy - y_top) / 2.0, 0, 1) * np.clip((y_bot - gy) / 3.0, 0, 1)
wk = 1 - cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.1)
w = (wx * wy * wk)[..., None]
out = I.copy()
out[ya:yb, xa:xb] = box * (1 - w) + new * w
cv2.imwrite(a.out, np.clip(out, 0, 255).round().astype(np.uint8))
if a.debug:
    dbg = np.hstack([np.dstack([paper * 255] * 3), np.dstack([keep * 255] * 3), np.dstack([speck * 255] * 3)]).astype(np.uint8)
    cv2.imwrite(a.debug, dbg)
print("done", xa, xb, ya, yb)
