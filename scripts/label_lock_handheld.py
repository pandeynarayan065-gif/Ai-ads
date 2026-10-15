#!/usr/bin/env python3
"""Lock the real Spraymax label onto a small hand-held AI bottle, lit by the AI bottle's own light, and take
the AI's colour cast off the whole bottle.

Why not label_lock_upright.py: on a bottle ~90 px wide with bold AI lettering there is too little clean paper
for its column x row light model. The new label came out flatter and darker than the plastic around it (it
read as a printed sticker), the band stopped short of the outline, and the AI's cream/yellow plastic stayed.

Here, per frame, in the bottle's own coordinates (tracked by optical flow back from the last frame):
- the light is the AI bottle's own luminance, pixel for pixel, wherever its paper or plastic shows; under its
  lettering and band it is filled in from the paper around it, so highlights, finger shadows and water
  droplets on the bottle carry straight onto the new print;
- the real label (label-flat.jpg wrapped round a cylinder, wave band continued round to the outline) is that
  light times the real print;
- colour: the bottle's chroma is re-centred on the scene's own white (the bright neutral clouds/foam in the
  same frame), keeping part of its local variation (warm bounce off the fingers, cool sky reflections);
- the label follows the bottle's perspective taper (--xc-bottom/--r-bottom), and in every frame it is only
  painted where the AI bottle actually is (grown from its middle over its own cream and print), so fingers,
  locks of hair and the sky showing between them keep the AI's pixels.

Spray, ocean (spray-ocean-v2-8s.mp4):
  python3 scripts/label_lock_handheld.py spray-ocean-v2-8s.mp4 out.mp4 \\
      --xc 594.5 --r 46.5 --xc-bottom 597 --r-bottom 43 --wm-top 702 --wm-bottom 827 --wm-x 603 --band-top 840 --band-end-y 893 \\
      --pump-bottom 655 --bottle "592,573 630,573 631,607 633,625 633,653 640,690 641,760 640,895 636,903 557,903 554,895 \\
                548,730 548,700 560,668 582,653 582,625 591,607"
"""
import argparse
import subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--art", default="brand/spraymax/assets/label-flat.jpg")
ap.add_argument("--art-u-c", type=float, default=702.0, help="art column of the wordmark's centre")
ap.add_argument("--art-radius", type=float, default=192.3, help="bottle radius in art px")
ap.add_argument("--xc", type=float, required=True, help="bottle centre x (last frame)")
ap.add_argument("--r", type=float, required=True, help="bottle radius (last frame)")
ap.add_argument("--xc-bottom", type=float, default=None, help="bottle centre x at --band-end-y (default --xc)")
ap.add_argument("--r-bottom", type=float, default=None, help="bottle radius at --band-end-y (perspective taper)")
ap.add_argument("--wm-top", type=float, required=True, help="y of the wordmark's top (last frame)")
ap.add_argument("--wm-bottom", type=float, required=True, help="y of the wordmark's bottom")
ap.add_argument("--wm-x", type=float, required=True, help="x of the wordmark's centre")
ap.add_argument("--band-top", type=float, required=True, help="y where the AI's wave band starts")
ap.add_argument("--band-end-y", type=float, required=True, help="y where the label ends (bottom of the band)")
ap.add_argument("--pump-bottom", type=float, required=True,
                help="y where the collar meets the shoulder (above it the pump is taken from the outline alone)")
ap.add_argument("--bottle", required=True, help="'x,y x,y ...' outline of the whole bottle incl. pump (last frame)")
ap.add_argument("--edge", type=float, default=1.0, help="px of the outline left to the footage")
ap.add_argument("--chroma-keep", type=float, default=0.5, help="share of the bottle's local colour variation kept")
ap.add_argument("--art-blur", type=float, default=0.5)
ap.add_argument("--crf", type=int, default=16)
ap.add_argument("--still", default=None, help="also write this frame (index:path)")
ap.add_argument("--debug", default=None, help="prefix for debug images of --debug-frame")
ap.add_argument("--debug-frame", type=int, default=None)
a = ap.parse_args()

ART_WM_TOP, ART_WM_BOTTOM, ART_BAND0, ART_BAND1 = 48.0, 628.0, 703, 948


def lin(x):
    x = np.clip(x / 255.0, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255.0


def to_lab(bgr):
    return cv2.cvtColor(np.clip(bgr, 0, 255).round().astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)


def from_lab(lab):
    return cv2.cvtColor(np.clip(lab, 0, 255).round().astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)


def fill(val, w, sigmas=(1.5, 4.0, 10.0, 25.0)):
    """val where w, filled in from around it (normalized convolution, finest scale that has support)."""
    out = np.where(w, val, 0.0).astype(np.float32)
    have = w.astype(bool).copy()
    wf = w.astype(np.float32)
    for s in sigmas:
        num = cv2.GaussianBlur(np.where(wf > 0, val, 0.0).astype(np.float32), (0, 0), s)
        den = cv2.GaussianBlur(wf, (0, 0), s)
        ok = (den > 0.15) & ~have
        out[ok] = num[ok] / den[ok]
        have |= ok
    if (~have).any() and have.any():
        out[~have] = out[have].mean()
    return out


# ---- frames ----------------------------------------------------------------------------
cap = cv2.VideoCapture(a.src)
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
N = len(frames)
H, W = frames[0].shape[:2]
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]

# ---- track: frame-to-frame similarities on the bottle's own print, chained back from the last frame ----
xc, r = a.xc, a.r
params = np.zeros((N, 4))
params[N - 1] = [1.0, 0.0, 0.0, 0.0]
region = np.array([[xc - r + 4, a.wm_top - 12], [xc + r - 4, a.wm_top - 12],
                   [xc + r - 4, a.band_end_y - 4], [xc - r + 4, a.band_end_y - 4]], np.float64)
lk = dict(winSize=(15, 15), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
fit_err = np.zeros(N)
for i in range(N - 2, -1, -1):
    Wn = np.vstack([[[params[i + 1][0], -params[i + 1][1], params[i + 1][2]],
                     [params[i + 1][1], params[i + 1][0], params[i + 1][3]]], [0, 0, 1]])
    msk = np.zeros((H, W), np.uint8)
    cv2.fillPoly(msk, [np.round(np.c_[region, np.ones(4)] @ Wn[:2].T).astype(np.int32)], 255)
    q1 = cv2.goodFeaturesToTrack(gray[i + 1], 300, 0.005, 3, mask=msk)
    M_ = None
    if q1 is not None and len(q1) >= 8:
        q0, s0, _ = cv2.calcOpticalFlowPyrLK(gray[i + 1], gray[i], q1, None, **lk)
        qb, s1, _ = cv2.calcOpticalFlowPyrLK(gray[i], gray[i + 1], q0, None, **lk)
        good = (s0.ravel() == 1) & (s1.ravel() == 1) & (np.linalg.norm((q1 - qb).reshape(-1, 2), axis=1) < 0.5)
        if good.sum() >= 8:
            M_, inl = cv2.estimateAffinePartial2D(q1.reshape(-1, 2)[good], q0.reshape(-1, 2)[good],
                                                  method=cv2.RANSAC, ransacReprojThreshold=1.0)
    if M_ is None:
        params[i] = params[i + 1]
        continue
    Wi = np.vstack([M_, [0, 0, 1]]) @ Wn
    params[i] = [Wi[0, 0], Wi[1, 0], Wi[0, 2], Wi[1, 2]]
    p_in = q1.reshape(-1, 2)[good][inl.ravel() == 1]
    p_out = q0.reshape(-1, 2)[good][inl.ravel() == 1]
    fit_err[i] = float(np.abs(p_in @ M_[:, :2].T + M_[:, 2] - p_out).max()) if len(p_in) else 0.0
for c in range(4):                              # the hand moves smoothly
    pad = np.pad(params[:, c], 6, mode="edge")
    params[:, c] = cv2.GaussianBlur(pad.reshape(-1, 1), (1, 0), 1.5).ravel()[6:-6]
print(f"bottle scale vs last frame: {np.hypot(*params[0, :2]):.4f} (frame 0); max flow residual {fit_err.max():.2f}px")

# ---- geometry in last-frame coordinates -------------------------------------------------
poly = np.array([[float(c_) for c_ in pt.split(",")] for pt in a.bottle.split()], np.float64)
x0, y0 = int(np.floor(poly[:, 0].min())) - 4, int(np.floor(poly[:, 1].min())) - 4
x1, y1 = int(np.ceil(poly[:, 0].max())) + 5, int(np.ceil(poly[:, 1].max())) + 5
BW, BH = x1 - x0, y1 - y0
gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
pm = np.zeros((BH, BW), np.uint8)
cv2.fillPoly(pm, [np.round((poly - [x0, y0]) * 8).astype(np.int32)], 1, shift=3)
dist_in = cv2.distanceTransform(pm, cv2.DIST_L2, 5)
dist_out = cv2.distanceTransform(1 - pm, cv2.DIST_L2, 5)
W_POLY = np.clip(dist_in - a.edge + 0.5, 0, 1)                   # inside the outline, minus the AI's own edge
RING = (dist_out > 0) & (dist_out <= 3)                           # just outside: the AI's yellow fringe

vs, ys_ = (ART_WM_TOP, ART_WM_BOTTOM, float(ART_BAND1)), (a.wm_top, a.wm_bottom, a.band_end_y)
p0, p1, p2 = np.linalg.solve([[1, v_, -v_ * y_] for v_, y_ in zip(vs, ys_)], ys_)
v = ((gy - p0) / (p1 - p2 * gy)).astype(np.float32)               # art row of each pixel
tt = np.clip((gy - a.wm_top) / (a.band_end_y - a.wm_top), -0.5, 1.2)   # taper along the bottle
xc_y = xc + ((a.xc_bottom if a.xc_bottom is not None else xc) - xc) * tt
r_y = r + ((a.r_bottom if a.r_bottom is not None else r) - r) * tt
k_u = r_y / a.art_radius
s = r_y * np.arcsin(np.clip((gx - xc_y) / r_y, -1, 1))
s_c = r_y * np.arcsin(np.clip((a.wm_x + (xc_y - xc) - xc_y) / r_y, -1, 1))
u = (a.art_u_c + (s - s_c) / k_u).astype(np.float32)
cyl = np.clip(r_y - np.abs(gx - xc_y) + 0.5, 0, 1)                 # anti-aliased cylinder side
W_LABEL = np.clip(v + 0.5, 0, 1) * np.clip(ART_BAND1 - v + 0.5, 0, 1) * cyl
label_top_y, label_bot_y = p0, (p0 + p1 * ART_BAND1) / (1 + p2 * ART_BAND1)

art = cv2.imread(a.art, cv2.IMREAD_COLOR).astype(np.float32)
art[:9] = 255.0
blue = (art[ART_BAND0:ART_BAND1, :, 0] - art[ART_BAND0:ART_BAND1, :, 2]) > 25
cols_b = np.flatnonzero(blue.mean(axis=0) > 0.5)
c0, c1 = cols_b.min(), cols_b.max()                               # the band wraps all the way round
band = art[ART_BAND0:ART_BAND1, c0:c1 + 1]
bw_ = c1 - c0 + 1
left = band[:, ::-1][:, :min(c0, bw_)][:, ::-1]
right = band[:, ::-1][:, :min(art.shape[1] - 1 - c1, bw_)]
art[ART_BAND0:ART_BAND1, c0 - left.shape[1]:c0] = left
art[ART_BAND0:ART_BAND1, c1 + 1:c1 + 1 + right.shape[1]] = right
paper_art = np.median(art[60:600, 480:640].reshape(-1, 3), axis=0)
A = cv2.remap(art, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
A = cv2.GaussianBlur(A, (0, 0), a.art_blur)
ALB = lin(A) / lin(paper_art)[None, None, :]                       # real print, paper = 1
BAND_ROWS = (gy >= a.band_top - 2) & (gy <= a.band_end_y + 1)
ABOVE_BAND = (gy >= label_top_y) & (gy < a.band_top - 2)


def to_ref(i):
    pa, pb, tx, ty = params[i]
    Mb = np.array([[pa, -pb, pa * x0 - pb * y0 + tx], [pb, pa, pb * x0 + pa * y0 + ty]])
    return cv2.warpAffine(frames[i], Mb, (BW, BH), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_REFLECT).astype(np.float32)


# ---- the scene's white, per frame (bright, colourless clouds and foam), smoothed over time ----
whites = []
for f in frames:
    lab = to_lab(cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32))
    sat = np.abs(lab[..., 1] - 128) + np.abs(lab[..., 2] - 128)
    m = (lab[..., 0] > 175) & (sat < 10)
    whites.append([np.median(lab[..., 1][m]), np.median(lab[..., 2][m])] if m.sum() > 200 else [np.nan, np.nan])
whites = np.array(whites, np.float64)
for c in range(2):
    ok = ~np.isnan(whites[:, c])
    whites[~ok, c] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), whites[ok, c]) if ok.any() else 128.0
    whites[:, c] = cv2.GaussianBlur(np.pad(whites[:, c], 8, mode="edge").reshape(-1, 1), (1, 0), 4).ravel()[8:-8]
print(f"scene white a*/b*: {whites[:, 0].mean():.1f}/{whites[:, 1].mean():.1f} (128 = neutral)")

# ---- per frame ----------------------------------------------------------------------------
rng = np.random.default_rng(7)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", str(a.crf), "-preset", "slow",
                        "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
still_i, still_p = (int(a.still.split(":")[0]), a.still.split(":", 1)[1]) if a.still else (None, None)
for i in range(N):
    box = to_ref(i)
    lab = to_lab(box)
    L8, aa, bb = lab[..., 0], lab[..., 1], lab[..., 2]
    Bc, Rc = box[..., 0], box[..., 2]
    sat = box.max(axis=2) - box.min(axis=2)
    Y = (lin(box) @ np.array([0.0722, 0.7152, 0.2126], np.float32)).astype(np.float32)
    inside = W_POLY > 0.5

    # the AI's own lettering (dark, thin) and band; fingers and hair over the bottle
    bh = cv2.morphologyEx(L8, cv2.MORPH_BLACKHAT, np.ones((13, 13), np.uint8))
    ink = (inside & ABOVE_BAND & (bh > 18)                           # thin dark strokes, not broad shadow,
           & ((np.abs(gx - a.wm_x) < 0.45 * r) | (gy > a.wm_bottom + 1)))   # only where the AI prints (not hair)
    ink = cv2.dilate(ink.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    plain = inside & ~ink & ~BAND_ROWS & (sat < 70)
    a0, b0 = (np.median(aa[plain]), np.median(bb[plain])) if plain.sum() > 50 else (128.0, 128.0)
    Lp = np.median(L8[plain]) if plain.sum() > 50 else 160.0
    skin = (aa > a0 + 10) & (bb > b0 - 2) & ((L8 < Lp - 12) | (sat > 70))
    skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    bh7 = cv2.morphologyEx(L8, cv2.MORPH_BLACKHAT, np.ones((7, 7), np.uint8))
    hair = ((bh7 > 25) & ((Rc - Bc) > 8) & ~ink).astype(np.uint8)
    keep = cv2.morphologyEx(skin | hair, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    keep = cv2.dilate(keep, np.ones((3, 3), np.uint8)).astype(np.float32)
    # where the AI bottle actually is in this frame: grown from its middle over its own cream and print (not
    # brighter than its paper: sunlit sky between hair and fingers is). The dark outline the AI draws round it
    # stops the growth too, so sky and hair just outside it are never painted
    allowed = inside & (ink | (BAND_ROWS & (cyl > 0.5))
                        | ((L8 > 0.45 * Lp) & (L8 < 1.12 * Lp) & (np.abs(aa - a0) < 7) & (bb > b0 - 4)))
    er = cv2.erode(allowed.astype(np.uint8), np.ones((3, 3), np.uint8))
    n_, lab_ = cv2.connectedComponents(er)
    seed = (er > 0) & (np.abs(gx - xc_y) < 0.5 * r_y) & (gy > label_top_y + 4) & (gy < a.band_end_y - 4)
    ids = np.unique(lab_[seed])
    region = np.isin(lab_, ids[ids > 0]).astype(np.uint8)
    region = cv2.dilate(region, np.ones((3, 3), np.uint8)) & allowed.astype(np.uint8)
    outside = (1 - region).astype(np.uint8)                          # holes (highlights, droplets) belong to it
    cv2.floodFill(outside, np.zeros((BH + 2, BW + 2), np.uint8), (0, 0), 2)
    region = (region > 0) | (outside == 1) | (inside & (gy < a.pump_bottom))
    W_REG = cv2.GaussianBlur(region.astype(np.float32), (0, 0), 0.7) * W_POLY
    ring_i = (cv2.dilate(region.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) & ~region
    W_KEEP = cv2.GaussianBlur(keep, (0, 0), 0.8)

    # light: the AI bottle's own luminance where its paper/plastic shows, filled in under its print
    paper = plain & (keep < 0.5)
    light = fill(Y, paper)
    # across its band: per column, from the paper just above to the plastic just below
    rows = np.arange(BH, dtype=np.float32) + y0
    above = (rows >= a.band_top - 9) & (rows < a.band_top - 3)
    below = (rows > a.band_end_y + 2) & (rows <= a.band_end_y + 6)
    l_above = light[above].mean(axis=0)
    pb_ = paper[below]
    l_below = np.where(pb_.sum(axis=0) >= 2,
                       (light[below] * pb_).sum(axis=0) / np.maximum(pb_.sum(axis=0), 1), l_above)
    t = np.clip((rows - (a.band_top - 3)) / max(1.0, (a.band_end_y + 3) - (a.band_top - 3)), 0, 1)[:, None]
    band_light = l_above[None, :] * (1 - t) + l_below[None, :] * t
    light = np.where(BAND_ROWS, band_light, light)

    # colour: the scene's white, plus part of the bottle's local variation (bounce light)
    wa, wb = whites[i]
    da = fill(aa - a0, paper, (4.0, 10.0, 25.0))
    db = fill(bb - b0, paper, (4.0, 10.0, 25.0))
    k = a.chroma_keep

    # the real label in that light
    new = srgb(ALB * light[..., None])
    nlab = to_lab(new)
    hp = L8 - cv2.GaussianBlur(L8, (0, 0), 1.2)                   # footage grain where the light was filled
    sig = 1.4826 * np.median(np.abs(hp[paper] - np.median(hp[paper]))) if paper.sum() > 200 else 1.5
    g = cv2.GaussianBlur(rng.normal(0, 1, (BH, BW)).astype(np.float32), (0, 0), 0.6)
    g *= sig / (g - cv2.GaussianBlur(g, (0, 0), 1.2)).std()
    pw = cv2.GaussianBlur(paper.astype(np.float32), (0, 0), 0.8)
    nlab[..., 0] += g * (1 - pw)
    nlab[..., 1] += (wa - 128) + k * da
    nlab[..., 2] += (wb - 128) + k * db
    new = from_lab(nlab)

    # the rest of the bottle (pump, collar, shoulder, base) and its yellow fringe: same light, scene's white
    plab = lab.copy()
    plab[..., 1] = wa + k * (aa - a0)
    plab[..., 2] = wb + k * (bb - b0)
    plastic = from_lab(plab)
    warm = np.clip((bb - wb - 3) / 6, 0, 1) * (1 - np.clip((aa - a0 - 6) / 4, 0, 1))   # yellow, not skin
    w_ring = ring_i * (L8 > 0.5 * Lp) * (np.abs(aa - a0) < 9) * warm * (1 - W_KEEP)   # its cream outline only

    wl = W_REG * W_LABEL * (1 - W_KEEP)
    wp = W_REG * (1 - W_LABEL) * (1 - W_KEEP)
    outb = box * (1 - wl - wp - w_ring)[..., None] + new * wl[..., None] + plastic * (wp + w_ring)[..., None]
    m = np.clip(wl + wp + w_ring, 0, 1)

    if a.debug and a.debug_frame == i:
        cv2.imwrite(f"{a.debug}-f{i}-box.png", np.clip(box, 0, 255).astype(np.uint8))
        cv2.imwrite(f"{a.debug}-f{i}-out.png", np.clip(outb, 0, 255).astype(np.uint8))
        cv2.imwrite(f"{a.debug}-f{i}-masks.png",
                    np.dstack([paper * 255, region * 255, keep * 255]).astype(np.uint8))
        cv2.imwrite(f"{a.debug}-f{i}-light.png", np.clip(srgb(light), 0, 255).astype(np.uint8))

    # back onto the frame (sub-pixel), only where something changed
    pa, pb, tx, ty = params[i]
    Wm = np.array([[pa, -pb, tx], [pb, pa, ty]])
    cr = np.array([[x0, y0, 1], [x1, y0, 1], [x0, y1, 1], [x1, y1, 1]], np.float64) @ Wm.T
    fx0, fx1 = max(0, int(cr[:, 0].min()) - 4), min(W, int(cr[:, 0].max()) + 5)
    fy0, fy1 = max(0, int(cr[:, 1].min()) - 4), min(H, int(cr[:, 1].max()) + 5)
    Wi = cv2.invertAffineTransform(Wm)
    Mi = Wi.copy()
    Mi[:, 2] = Wi[:, :2] @ np.array([fx0, fy0]) + Wi[:, 2] - np.array([x0, y0])
    sz = (fx1 - fx0, fy1 - fy0)
    o_f = cv2.warpAffine(outb.astype(np.float32), Mi, sz, flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_REPLICATE)
    m_f = cv2.warpAffine(m.astype(np.float32), Mi, sz, flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    fr = frames[i].astype(np.float32)
    reg = fr[fy0:fy1, fx0:fx1]
    fr[fy0:fy1, fx0:fx1] = reg * (1 - m_f[..., None]) + o_f * m_f[..., None]
    out = np.clip(fr, 0, 255).round().astype(np.uint8)
    if i == still_i:
        cv2.imwrite(still_p, out)
    enc.stdin.write(out.tobytes())
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")
print(f"label rows {label_top_y:.0f}-{label_bot_y:.0f}, {N} frames -> {a.out}")
