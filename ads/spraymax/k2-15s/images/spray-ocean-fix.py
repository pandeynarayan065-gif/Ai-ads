"""One-off, coordinates are for spray-ocean-raw.png only.
Usage: python3 spray-ocean-fix.py spray-ocean-raw.png fixed.png

Fix the Nano Banana ocean still before the label lock: remove the nasal-spray tube and the
pre-press mist (the real pump head has a flush side orifice), add the real closure's fine ribs,
and take out the green flare streak in the bottom-right corner."""
import sys
import cv2
import numpy as np

src, out = sys.argv[1], sys.argv[2]
im = cv2.imread(src).astype(np.float32)
H, W = im.shape[:2]
rng = np.random.default_rng(7)

def sky_fit(img, box, keep):
    """2nd-order polynomial sky per channel fitted on `keep` pixels inside box (y0,y1,x0,x1)."""
    y0, y1, x0, x1 = box
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    u, v = (xx - x0) / (x1 - x0), (yy - y0) / (y1 - y0)
    A = np.stack([np.ones_like(u), u, v, u * u, u * v, v * v], -1)
    sm = cv2.GaussianBlur(img[y0:y1, x0:x1], (0, 0), 2.0)
    fit = np.zeros_like(sm)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A[keep], sm[..., c][keep], rcond=None)
        fit[..., c] = A @ coef
    return fit

def grain_patch(img, box, shape):
    y0, y1, x0, x1 = box
    p = img[y0:y1, x0:x1]
    hp = p - cv2.GaussianBlur(p, (0, 0), 2.0)
    reps = (shape[0] // hp.shape[0] + 1, shape[1] // hp.shape[1] + 1, 1)
    return np.tile(hp, reps)[:shape[0], :shape[1]]

# ---- 1. mist + tube over the sky, left of the pump head ----
box = (600, 720, 560, 800)                               # y0, y1, x0, x1
y0, y1, x0, x1 = box
reg = im[y0:y1, x0:x1]
lum = reg.mean(-1)
hair = cv2.dilate((lum < 150).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
yy, xx = np.mgrid[y0:y1, x0:x1]
# mist cone from the tube tip (731, 662) spreading left; the tube itself
cone = (xx < 742) & (xx > 590) & (np.abs(yy - 663) < 9 + (742 - xx) * 0.42)
core = cone & (xx > 640)                                  # dense part: rebuilt as sky
tube = (((xx >= 724) & (xx <= 754) & (yy >= 645) & (yy <= 682)) |
        ((xx >= 754) & (xx <= 796) & (yy >= 650) & (yy <= 679)))
act = (xx >= 788)                                        # the pump head itself
keep = ~hair & ~cone & ~tube & ~act
fit = sky_fit(im, box, keep)
resid = reg - fit
g = grain_patch(im, (606, 640, 620, 720), reg.shape)
# faint outer mist: subtract its smoothed excess (hair keeps its detail)
haze = cv2.GaussianBlur(np.where((hair | ~cone)[..., None], 0, resid), (0, 0), 5)
mc = cv2.GaussianBlur(cone.astype(np.float32), (0, 0), 5)[..., None]
reg2 = reg - np.clip(haze, 0, None) * mc
# dense mist and the tube, where no hair crosses: fitted sky + matched grain
rep = (core | tube) & ~(hair & ~tube)
mr = cv2.GaussianBlur(rep.astype(np.float32), (0, 0), 2.0)[..., None]
mr = np.maximum(mr, tube[..., None].astype(np.float32))
mr[:, 228 - 0:] = np.where(act[:, 228:, None], 0, mr[:, 228:])   # never touch the head (x >= 788)
reg2 = reg2 * (1 - mr) + (fit + g) * mr
im[y0:y1, x0:x1] = reg2
# rebuild the head's left edge across the junction rows: the edge profile just below the tube,
# with the head's own vertical shading and fresh grain on every row
prof = im[681:689, 782:806].mean(0)
hp = im[655:700, 806:836] - cv2.GaussianBlur(im[655:700, 806:836], (0, 0), 1.5)
for y in range(649, 681):
    ratio = im[y, 806:814].mean() / max(im[681:689, 806:814].mean(), 1)
    row = prof * np.clip(ratio, 0.9, 1.1) + hp[(y - 649) % hp.shape[0], :24]
    im[y, 782:806] = row

# ---- 2. fine vertical ribs on the closure (cylinder, compressed toward the edges) ----
cy0, cy1, cxl, cxr = 732, 788, 771, 857
cxc, cr = (cxl + cxr) / 2, (cxr - cxl) / 2
reg = im[cy0:cy1, cxl:cxr]
hsv = cv2.cvtColor(np.clip(reg, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
plastic = (hsv[..., 1] < 40) & (hsv[..., 2] > 120)                 # white plastic, not skin
plastic = cv2.erode(plastic.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
xs = np.arange(cxl, cxr) + 0.5
th = np.arcsin(np.clip((xs - cxc) / cr, -0.999, 0.999))
rib = np.cos(th * 70 / 2)                                          # 70 ribs around the closure
rib = np.sign(rib) * np.abs(rib) ** 0.6
amp = 0.045 * np.cos(th) ** 0.5                                     # fades toward the silhouette
mod = 1 + amp * rib
vfade = np.ones(cy1 - cy0); vfade[:3] = [0.3, 0.6, 0.85]; vfade[-3:] = [0.85, 0.6, 0.3]
m = cv2.GaussianBlur(plastic, (0, 0), 0.8) * vfade[:, None]
reg[:] = reg * (1 + (mod[None, :] - 1) * m)[..., None]

# ---- 3. green flare streak over the rocks, bottom-right ----
fy0, fx0 = 2250, 1250
reg = im[fy0:, fx0:]
b, g_, r = reg[..., 0], reg[..., 1], reg[..., 2]
cast = cv2.GaussianBlur(np.clip((g_ - r) + 0.5 * (b - r), 0, None), (0, 0), 3)
mask = np.clip((cast - 4) / 10, 0, 1)
mask = cv2.GaussianBlur(mask, (0, 0), 4)
reg[..., 1] = g_ - (g_ - r) * mask
reg[..., 0] = b - (b - r) * mask
im[fy0:, fx0:] = reg

cv2.imwrite(out, np.clip(im, 0, 255).round().astype(np.uint8))
print("ok", W, H)
