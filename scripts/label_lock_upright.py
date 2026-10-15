#!/usr/bin/env python3
"""Lock the real label artwork onto an AI bottle in every frame of a clip.

For a bottle seen front-on with its axis vertical in frame (e.g. lying in snow, shot
from above). The bottle is modelled as a cylinder (centre x, radius) in the clean LAST
frame; the label art (label-front-panel.jpg) is wrapped around it at a uniform scale
fitted to the AI's own wordmark. Each frame keeps its own lighting, sparkle and frost:
the art is multiplied by that frame's paper shading and the frame's highlights are
added back. Snow lying on top of the label and the climber's glove passing over it are
detected and left alone.

Motion: the camera drifts and slowly pushes in, so every frame gets a sub-pixel
similarity transform (scale + shift) fitted to seven tracked parts of the bottle
(three along the wordmark, the band, the band's base, both edges). The label is built in last-frame
coordinates and warped onto each frame with that transform, so it stays glued to the
bottle with no whole-pixel hops. Paper shading, ink colour and the snow mask are
smoothed over time so nothing flickers from one frame to the next.

Usage (K2 reveal, first clip: bottle face-on, camera pushing in):
  python3 scripts/label_lock_upright.py in.mp4 out.mp4 \
      --xc 598.5 --r 156.5 --wm-top 920 --wm-bottom 1392 --wm-x 596 \
      --old-band-top 1440 --old-band-bottom 1614 --static-below 1400 --glove-pad 25 --from 96

K2 reveal v2 (bottle half-buried and turned ~17 deg, phone held still, spindrift): the full
wrap-around label, camera followed by the rocks, label only inside the traced unburied outline,
blowing snow carried over it and the AI's painted-on frost dropped:
  python3 scripts/label_lock_upright.py reveal-v2-8s.mp4 out.mp4 \
      --art brand/spraymax/assets/label-flat.jpg --art-u-c 702 --art-radius 192.3 \
      --xc 627 --r 151 --edge-margin 3 --rim 22 --wm-top 960 --wm-bottom 1349 --wm-x 672 \
      --old-band-top 1700 --old-band-bottom 1750 \
      --track-rects "900,1500,880,1060;1300,1800,20,250" --visible "<outline, see the commit>" \
      --specks --label-clear --from 64
"""
import argparse
import subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--art", default="brand/spraymax/assets/label-front-panel.jpg")
ap.add_argument("--xc", type=float, required=True, help="bottle centre x (px, last frame)")
ap.add_argument("--r", type=float, required=True, help="bottle radius (px)")
ap.add_argument("--wm-top", type=float, required=True, help="y of the AI wordmark's top")
ap.add_argument("--wm-bottom", type=float, required=True, help="y of the AI wordmark's bottom")
ap.add_argument("--wm-x", type=float, required=True, help="x of the AI wordmark's centre")
ap.add_argument("--old-band-top", type=float, required=True, help="y where the AI's band starts")
ap.add_argument("--old-band-bottom", type=float, required=True, help="y where the AI's band ends")
ap.add_argument("--band-y", type=float, default=None,
                help="y where the AI's wave band starts; with it the label follows perspective along the bottle")
ap.add_argument("--band-end-y", type=float, default=None,
                help="y where the AI's band ends (bottom of the label); fits the label's length to the AI bottle")
ap.add_argument("--r-far", type=float, default=None, help="bottle radius at --band-y (default: --r)")
ap.add_argument("--xc-far", type=float, default=None, help="bottle centre x at --band-y (default: --xc)")
ap.add_argument("--art-radius", type=float, default=None,
                help="bottle radius in art px (default: fitted so the wordmark is not stretched)")
ap.add_argument("--art-u-c", type=float, default=247.0,
                help="art column of the wordmark's centre (247 for label-front-panel, 702 for label-flat)")
ap.add_argument("--track-rects", default=None,
                help="'y0,y1,x0,x1;...' static scenery to follow the camera by (translation only) "
                     "instead of tracking parts of the bottle")
ap.add_argument("--visible", default=None,
                help="'x,y x,y ...' polygon of the label surface that is not buried (last frame); "
                     "outside it the original pixels (snow) are kept")
ap.add_argument("--specks", action="store_true",
                help="carry bright blowing-snow specks over the new label instead of losing them")
ap.add_argument("--edge-margin", type=float, default=8.0, help="px of the real silhouette left untouched")
ap.add_argument("--rim", type=int, default=12, help="px inside the --visible outline where bright snow is kept")
ap.add_argument("--label-clear", action="store_true",
                help="nothing lies on the visible label (only the drift at its outline): skip per-frame "
                     "snow detection there, and drop the AI's painted-on frost flecks (bright dots that "
                     "never move) instead of carrying them over")
ap.add_argument("--art-blur", type=float, default=0.75, help="softness of the printed art (px) to match the footage")
ap.add_argument("--grain", action="store_true",
                help="add grain matched to the footage where the label has none of its own (where the AI's "
                     "letters were), so the new print does not look smoother than the rest of the frame")
ap.add_argument("--keep-frost", action="store_true",
                help="with --label-clear: keep the AI's still frost crystals, drop only those tracing its old text")
ap.add_argument("--debug-frame", type=int, default=None, help="write this frame's masks next to --debug")
ap.add_argument("--chain", action="store_true",
                help="the bottle travels far (e.g. sinking): track backwards from the last frame, each frame "
                     "searched around the next frame's position")
ap.add_argument("--keep-moving", action="store_true",
                help="keep the AI's own pixels wherever the image differs strongly from the settled bottle "
                     "(air cavities, big bubble clusters), so the label is never crisp under turbulent water")
ap.add_argument("--no-base", action="store_true",
                help="don't track the band's base (when it shows moving background, e.g. water around a falling bottle)")
ap.add_argument("--pad-bottom", type=int, default=0,
                help="art rows of plain bottle below the label, to cover AI print that runs past the real label")
ap.add_argument("--sharp", action="store_true", help="cubic resampling onto the frame (for crisp footage)")
ap.add_argument("--relight", action="store_true",
                help="carry the footage's changing light (caustics, bubble shading, passing highlights) onto the "
                     "new label: per-frame light relative to the clip's average, read on the AI's plain paper only")
ap.add_argument("--band-match", action="store_true",
                help="match the wave band's brightness/colour to how the scene lit the AI's band")
ap.add_argument("--no-glove", action="store_true", help="no hand in this shot: skip the dark-mitt detector")
ap.add_argument("--glove-pad", type=int, default=9, help="px of margin kept around the moving glove")
ap.add_argument("--static-below", type=float, default=None, help="ignore motion below this y (nothing crosses it)")
ap.add_argument("--from", dest="start", type=int, default=0, help="first frame to fix")
ap.add_argument("--still", default=None, help="also write the last fixed frame here")
ap.add_argument("--crf", type=int, default=16, help="x264 quality (0 = lossless master)")
ap.add_argument("--debug", default=None, help="write per-frame track + check numbers here (csv)")
a = ap.parse_args()

# art geometry (label-front-panel.jpg, measured): wordmark rows 48..628, wave band from row 703,
# centre column 247
ART_WM_TOP, ART_WM_BOTTOM, ART_BAND = 48.0, 628.0, 703.0
ART_U_C = a.art_u_c
ART_BAND_ROWS = (703, 948)
art = cv2.imread(a.art, cv2.IMREAD_COLOR).astype(np.float32)
art[:9] = 255.0                                   # print border line at the top edge
if a.band_match:                                  # the band wraps to the outline (as on the real bottle)
    b0, b1 = int(ART_BAND_ROWS[0]), int(ART_BAND_ROWS[1])
    blue = (art[b0:b1, :, 0] - art[b0:b1, :, 2]) > 25                  # the wave photo is blue; side text is black
    cols_b = np.flatnonzero(blue.mean(axis=0) > 0.5)
    if len(cols_b):
        c0, c1 = cols_b.min(), cols_b.max()
        band = art[b0:b1, c0:c1 + 1]
        w = c1 - c0 + 1
        left = band[:, ::-1][:, :min(c0, w)][:, ::-1]
        right = band[:, ::-1][:, :min(art.shape[1] - 1 - c1, w)]
        art[b0:b1, c0 - left.shape[1]:c0] = left
        art[b0:b1, c1 + 1:c1 + 1 + right.shape[1]] = right
if a.pad_bottom:
    art = np.vstack([art, np.full((a.pad_bottom, art.shape[1], 3), 247.0, np.float32)])   # bare plastic
NV, NU = art.shape[:2]
k = (a.wm_bottom - a.wm_top) / (ART_WM_BOTTOM - ART_WM_TOP)     # frame px per art px (mean, along)
# along the bottle: frame y = (p0 + p1 v) / (1 + p2 v) for art row v. Uniform (p2 = 0) for a
# bottle seen square-on; with --band-y it is fitted to three marks so it follows perspective.
if a.band_y is None and a.band_end_y is None:
    p0, p1, p2 = a.wm_top - ART_WM_TOP * k, k, 0.0
else:
    third = (ART_BAND, a.band_y) if a.band_y is not None else (948.0, a.band_end_y)
    vs, ys_ = (ART_WM_TOP, ART_WM_BOTTOM, third[0]), (a.wm_top, a.wm_bottom, third[1])
    p0, p1, p2 = np.linalg.solve([[1, v_, -v_ * y_] for v_, y_ in zip(vs, ys_)], ys_)


def y_of_v(v_):
    return (p0 + p1 * v_) / (1 + p2 * v_)


def v_of_y(y_):
    return (y_ - p0) / (p1 - p2 * y_)


y0 = y_of_v(0.0)                                                 # where the label starts
r_far = a.r if a.r_far is None else a.r_far
xc_far = a.xc if a.xc_far is None else a.xc_far
art_radius = a.art_radius or a.r / k

cap = cv2.VideoCapture(a.src)
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
H, W = frames[0].shape[:2]
N = len(frames)
idx = list(range(a.start, N))

# ---- label layer geometry, in last-frame coordinates ------------------------------------
x0, x1 = int(min(a.xc - a.r, xc_far - r_far)) + 1, int(max(a.xc + a.r, xc_far + r_far))
ya, yb = int(y0), min(H, int(y_of_v(NV)))
BH, BW = yb - ya, x1 - x0
gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(ya, yb, dtype=np.float32))
tt = 0.0 if a.band_y is None else (gy - a.wm_top) / (a.band_y - a.wm_top)   # radius/axis along (band_y only)
r_y = a.r + (r_far - a.r) * tt                                   # radius and axis along the bottle
xc_y = a.xc + (xc_far - a.xc) * tt
k_u = r_y / art_radius                                           # frame px per art px, around
s = r_y * np.arcsin(np.clip((gx - xc_y) / r_y, -1, 1))
s_c = r_y * np.arcsin(np.clip((a.wm_x - a.xc) / a.r, -1, 1))
u = (ART_U_C + (s - s_c) / k_u).astype(np.float32)
v = v_of_y(gy).astype(np.float32)
A = cv2.remap(art, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
A = cv2.GaussianBlur(A, (0, 0), a.art_blur)


def lin(x):
    x = np.clip(x / 255.0, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255.0


alb = lin(A)
edge = np.clip((r_y - a.edge_margin - np.abs(gx - xc_y)) / (10.0 if a.edge_margin >= 8 else 4.0), 0, 1) * np.clip((gy - y0) / 4.0, 0, 1)   # keep the real silhouette
art_print = ((art[..., 0] - art[..., 2]) > 50) & (art.mean(axis=2) < 170)
art_print[640:] = False                                                              # wordmark only, not the wave band
PRINT = cv2.remap(art_print.astype(np.float32), u, v, cv2.INTER_LINEAR) > 0.5      # new wordmark pixels
paper_rows = max(10, int(y_of_v(640.0) - ya))          # label rows above the old tagline/band
old_wm = (np.abs(gx - a.wm_x) < 62) & (gy > a.wm_top - 12) & (gy < a.wm_bottom + 12)
old_tag = (gy > a.wm_bottom + 10) & (gy < a.old_band_top + 4)
old_band = (gy >= a.old_band_top) & (gy <= a.old_band_bottom)
below = gy > a.old_band_bottom

# ---- track the bottle: six parts, each matched against the clean last frame -------------
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
xc, r = a.xc, a.r
parts = [(a.wm_top + 5, a.wm_top + 140, xc - 90, xc + 90),                  # wordmark start
         ((a.wm_top + a.wm_bottom) / 2 - 100, (a.wm_top + a.wm_bottom) / 2 + 100, xc - 90, xc + 90),
         (a.wm_bottom - 120, a.wm_bottom + 3, xc - 90, xc + 90),            # wordmark end
         (a.old_band_top - 45, a.old_band_top + 160, xc - 130, xc + 130),   # tagline + band
         (a.old_band_bottom - 14, a.old_band_bottom + 86, xc - 130, xc + 130),   # band base
         (a.wm_top - 20, a.wm_bottom + 10, xc - r - 20, xc - r + 25),       # left edge (x only)
         (a.wm_top - 20, a.wm_bottom + 10, xc + r - 25, xc + r + 20)]       # right edge (x only)
X_ONLY = [False, False, False, False, False, True, True]   # a long vertical edge can't tell up from down
if a.no_base:
    del parts[4], X_ONLY[4]
parts = [(max(30, int(p0)), min(H - 30, int(p1)), max(30, int(q0)), min(W - 30, int(q1))) for p0, p1, q0, q1 in parts]
P = 25


def track(i, p, off=(0, 0)):
    t0, t1, l0, l1 = p
    ox, oy = int(round(off[0])), int(round(off[1]))
    s0, s1 = max(0, t0 + oy - P), min(H, t1 + oy + P)
    q0, q1 = max(0, l0 + ox - P), min(W, l1 + ox + P)
    if s1 - s0 < t1 - t0 + 2 or q1 - q0 < l1 - l0 + 2:
        return 0.0, 0.0, -1.0
    res = cv2.matchTemplate(gray[i][s0:s1, q0:q1], gray[-1][t0:t1, l0:l1], cv2.TM_CCOEFF_NORMED)
    _, sc, _, (x, y) = cv2.minMaxLoc(res)
    dx = dy = 0.0
    if 0 < x < res.shape[1] - 1:
        l_, c_, r_ = res[y, x - 1], res[y, x], res[y, x + 1]
        dx = 0.5 * (l_ - r_) / (l_ - 2 * c_ + r_ - 1e-9)
    if 0 < y < res.shape[0] - 1:
        l_, c_, r_ = res[y - 1, x], res[y, x], res[y + 1, x]
        dy = 0.5 * (l_ - r_) / (l_ - 2 * c_ + r_ - 1e-9)
    return x + q0 - l0 + dx, y + s0 - t0 + dy, sc


if a.track_rects:
    parts = [tuple(int(float(v_)) for v_ in r_.split(",")) for r_ in a.track_rects.split(";")]
    parts = [(max(P + 1, p0), min(H - P - 1, p1), max(P + 1, q0), min(W - P - 1, q1)) for p0, p1, q0, q1 in parts]
    X_ONLY = [False] * len(parts)
centres = np.array([((l0 + l1) / 2.0, (t0 + t1) / 2.0) for t0, t1, l0, l1 in parts], np.float64)
params = np.full((N, 4), np.nan)          # similarity p' = [a -b; b a] p + [tx, ty]
fit_err = np.zeros(N)
prev = None
for i in (idx[::-1] if a.chain else idx):
    if a.chain and prev is not None:          # predict each part from the frame after this one
        pa, pb, ptx, pty = prev
        offs = [(pa * cx - pb * cy + ptx - cx, pb * cx + pa * cy + pty - cy) for cx, cy in centres]
    else:
        offs = [(0, 0)] * len(parts)
    tr = np.array([track(i, p, o) for p, o in zip(parts, offs)])
    good = tr[:, 2] > 0.8
    if (good.sum() < 1) if a.track_rects else (good[:5].sum() < 2 or good.sum() < 3):
        continue
    rows, rhs = [], []
    for (qx, qy), (dx, dy, _), g_, xo in zip(centres, tr, good, X_ONLY):
        if not g_:
            continue
        rows.append([qx, -qy, 1, 0]); rhs.append(qx + dx)
        if not xo:
            rows.append([qy, qx, 0, 1]); rhs.append(qy + dy)
    M, rhs = np.array(rows), np.array(rhs)
    if a.track_rects:                         # scenery: the camera only shifts (scale/rotation stay 1/0)
        sol = np.array([1.0, 0.0, *np.mean((rhs - M[:, :2] @ [1.0, 0.0]).reshape(-1, 2), axis=0)])
    else:
        sol, *_ = np.linalg.lstsq(M, rhs, rcond=None)
    params[i] = sol
    prev = sol
    fit_err[i] = np.abs(M @ sol - rhs).max()
for c in range(4):                        # fill gaps, then smooth: the real camera moves smoothly
    col = params[a.start:, c]
    ok = ~np.isnan(col)
    col[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), col[ok])
    pad = np.pad(col, 6, mode="edge")
    params[a.start:, c] = cv2.GaussianBlur(pad.reshape(-1, 1), (1, 0), 1.5).ravel()[6:-6]
print(f"bottle scale vs last frame: {np.hypot(*params[a.start, :2]):.4f} (frame {a.start}) -> 1.0000; "
      f"max track residual {fit_err[idx].max():.2f}px")


def warp_of(i):
    pa, pb, tx, ty = params[i]
    return np.array([[pa, -pb, tx], [pb, pa, ty]], np.float64)     # last-frame coords -> frame i


def to_ref(i):
    """Frame i resampled into the last frame's label box."""
    Wm = warp_of(i)
    Mb = Wm.copy()
    Mb[:, 2] = Wm[:, :2] @ np.array([x0, ya]) + Wm[:, 2]
    return cv2.warpAffine(frames[i], Mb, (BW, BH), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_REFLECT).astype(np.float32)


# ---- pass 1: measure paper shading, ink colour and what must be kept, per frame ---------
# the part of the label that is not buried (static, from the traced outline)
VIS = np.ones((BH, BW), bool)
if a.visible:
    poly = np.array([[float(c_) for c_ in pt.split(",")] for pt in a.visible.split()], np.float32)
    vm = np.zeros((BH, BW), np.uint8)
    cv2.fillPoly(vm, [np.round(poly - [x0, ya]).astype(np.int32)], 1)
    VIS = vm.astype(bool)
BURIED = ~VIS
VIS_CORE = cv2.erode(VIS.astype(np.uint8), np.ones((2 * a.rim + 1, 2 * a.rim + 1), np.uint8)).astype(bool)
VIS_RIM = VIS & ~VIS_CORE                 # where the drift's own edge may still cover the label

cols, rowgs, facs, snows, gloves, brights, ainks, excess = {}, {}, {}, {}, {}, {}, {}, {}
bfac, lums = {}, {}
_cen = np.abs(gx - a.xc) < 0.6 * a.r
BAND_AI = _cen & (gy > a.old_band_top + 12) & (gy < a.old_band_bottom - 12)
BAND_NEW = _cen & (gy > y_of_v(ART_BAND + 12)) & (gy < y_of_v(940.0))
BAND_AI_R = slice(max(0, int(a.old_band_top + 12 - ya)), max(1, int(a.old_band_bottom - 12 - ya)))
BAND_NEW_R = slice(max(0, int(y_of_v(ART_BAND + 12) - ya)), max(1, int(y_of_v(940.0) - ya)))
BAND_ROWS = (v >= ART_BAND - 2) & (v <= 950)
SEED = cv2.dilate(BURIED.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)


def touching(cand, seed):
    """Components of cand that touch seed (the drift's own snow spilling over the outline)."""
    n_, lab_ = cv2.connectedComponents((cand | seed).astype(np.uint8))
    hit = np.unique(lab_[seed])
    return cand & np.isin(lab_, hit[hit > 0])

ref_box = to_ref(N - 1)
for i in idx:
    box = to_ref(i)
    L = box.mean(axis=2)
    sat = box.max(axis=2) - box.min(axis=2)
    Bc, Gc, Rc = box[..., 0], box[..., 1], box[..., 2]
    white = (sat < 45) & (L > 110)
    white &= ~cv2.dilate((~white).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    pw = white & VIS_CORE
    pw[paper_rows:] = False
    col = np.full((BW, 3), np.nan, np.float32)
    for j in range(BW):
        c = box[:, j][pw[:, j]]
        if len(c) > 20:
            col[j] = np.median(c, axis=0)
    for ch in range(3):
        cc = col[:, ch]
        ok = ~np.isnan(cc)
        cc[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), cc[ok])
        col[:, ch] = cv2.GaussianBlur(cc.reshape(1, -1), (0, 0), 3).ravel()
    rowg = np.full(BH, np.nan, np.float32)
    ref_lum = col.mean(axis=1)
    for r_ in range(paper_rows):
        m = pw[r_]
        if m.sum() > 20:
            rowg[r_] = np.median(L[r_][m] / ref_lum[m])
    ok = ~np.isnan(rowg)
    rowg[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), rowg[ok])
    rowg = cv2.GaussianBlur(rowg.reshape(-1, 1), (0, 0), 25).ravel()
    cols[i], rowgs[i] = col, rowg
    S = col[None, :, :] * rowg[:, None, None]
    # how the scene lit the AI's own wordmark (the new ink is matched to it)
    old_ink = old_wm & ((Bc - Rc) > 40) & (L < 150)
    new0 = srgb(alb * lin(S))
    facs[i] = (box[old_ink].mean(axis=0) / (new0[PRINT].mean(axis=0) + 1e-3)
               if old_ink.sum() > 500 else np.full(3, np.nan))
    if a.band_match:                           # the AI's band vs ours, column by column (keeps its wrap-around shading)
        ai_c = np.array([box[BAND_AI_R][:, j].mean(axis=0) for j in range(BW)])
        nw_c = np.array([new0[BAND_NEW_R][:, j].mean(axis=0) for j in range(BW)])
        fc = cv2.GaussianBlur((ai_c / (nw_c + 1e-3)).astype(np.float32).reshape(1, BW, 3), (0, 0), 6).reshape(BW, 3)
        bfac[i] = fc
    if a.relight:
        lums[i] = L.astype(np.float16)

    # snow piled on the bottle. On bare paper it shows up as texture that departs from the smooth
    # paper shading; over the AI's dark band it shows up as large bright blobs. The AI's own print
    # (old wordmark, tagline, band text, wave crests) is thin, so the openings drop it.
    dev = np.abs(L - S.mean(axis=2))
    lmin = cv2.erode(L, np.ones((5, 5), np.uint8))
    snow_paper = (dev > 16) & (L > 115) & (lmin > 95) & ~old_wm & ~old_tag & ~old_band
    snow_paper = cv2.morphologyEx(snow_paper.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    snow_band = (old_band & (L > 138) & (sat < 55)).astype(np.uint8)
    snow_band = cv2.morphologyEx(snow_band, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    snow = snow_paper | snow_band | (below & (L > 120)).astype(np.uint8)
    rim = VIS_RIM & (L > S.mean(axis=2) + 12) & (sat < 40)
    if a.label_clear:                      # only the drift itself, spilling over the traced edge
        snow = touching(rim, SEED).astype(np.uint8)
    elif a.visible:                        # the drift's rim: bright snow lying over the traced edge
        snow |= rim.astype(np.uint8)
    brights[i] = ((L - S.mean(axis=2)) > 22).astype(np.uint8)
    if a.label_clear:
        excess[i] = (L - S.mean(axis=2)).astype(np.float16)
    if a.keep_frost or a.label_clear:          # the AI's own print in this frame (to tell text-flecks apart)
        aink = (((Bc - Rc) - (S[..., 0] - S[..., 2])) > 15) & (L < S.mean(axis=2) - 25)
        if a.label_clear:                      # black/grey AI print too (taglines, small text)
            aink |= L < S.mean(axis=2) - 40
        ainks[i] = cv2.dilate(aink.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    snows[i] = cv2.morphologyEx(snow, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    # the mitt: big red or black blobs (the opening removes thin letter strokes)
    glove = (((Rc - Gc) > 60) | ((L < 75) & ((Bc - Rc) < 15))).astype(np.uint8)
    glove = cv2.morphologyEx(glove, cv2.MORPH_OPEN, np.ones((17, 17), np.uint8))
    if a.no_glove:
        glove[:] = 0
    if a.keep_moving:                          # turbulent water over the label: keep the AI's refraction
        hp_b = box - cv2.GaussianBlur(box, (0, 0), 4)              # fine detail only: bubbles and the air
        hp_r = ref_box - cv2.GaussianBlur(ref_box, (0, 0), 4)      # tube, not smooth changes of light
        mv = (np.abs(hp_b - hp_r).sum(axis=2) > 60).astype(np.uint8)
        gain = box.mean() / max(ref_box.mean(), 1.0)              # smooth air films too, but only up top,
        upper = gy < (a.wm_top + a.wm_bottom) / 2                  # where air reaches (the band below just
        mv |= ((np.abs(box - ref_box * gain).sum(axis=2) > 60) & upper).astype(np.uint8)   # changes light)
        mv = cv2.morphologyEx(mv, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))
        mv = cv2.morphologyEx(mv, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))   # one solid turbulent zone,
        n_, lab_, st_, _ = cv2.connectedComponentsWithStats((1 - mv).astype(np.uint8))   # holes filled
        for c_ in range(1, n_):
            if st_[c_, cv2.CC_STAT_AREA] < 4000:
                mv[lab_ == c_] = 1
        glove |= cv2.dilate(mv, np.ones((15, 15), np.uint8))
    if glove.any() and not a.keep_moving:
        # snow the mitt is pushing around: changed vs the clean last frame, near the mitt only
        gain = box.mean() / max(ref_box.mean(), 1.0)
        moving = (np.abs(box - ref_box * gain).sum(axis=2) > 70).astype(np.uint8)
        moving = cv2.morphologyEx(moving, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))
        moving &= cv2.dilate(glove, np.ones((61, 61), np.uint8))
        glove = cv2.dilate(glove | moving, np.ones((a.glove_pad, a.glove_pad), np.uint8))
        if a.static_below is not None:
            glove[gy >= a.static_below] = 0           # nothing passes over the lower label
    gloves[i] = glove

# ---- smooth over time (all in the bottle's own coordinates, so frames line up) -----------
def tsmooth(d, sigma):
    arr = np.stack([d[i] for i in idx]).astype(np.float32)
    shp = arr.shape
    flat = arr.reshape(len(idx), -1)
    for c in np.flatnonzero(np.isnan(flat).any(axis=0)):       # frames where it couldn't be measured
        ok = ~np.isnan(flat[:, c])
        flat[~ok, c] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), flat[ok, c]) if ok.any() else 1.0
    pad = np.pad(flat, ((8, 8), (0, 0)), mode="edge")
    sm = cv2.GaussianBlur(pad, (1, 0), sigmaX=0.1, sigmaY=sigma)[8:-8]
    return {i: sm[n].reshape(shp[1:]) for n, i in enumerate(idx)}


cols = tsmooth(cols, 2.0)
rowgs = tsmooth(rowgs, 2.0)
facs = {i: np.clip(f, 0.7, 1.8) for i, f in tsmooth(facs, 3.0).items()}
if a.band_match:
    bfac = {i: np.clip(f, 0.4, 2.0) for i, f in tsmooth(bfac, 3.0).items()}
if a.relight:
    LMED = np.median(np.stack([lums[i] for i in idx[::2]]).astype(np.float32), axis=0)
snow_stack = np.stack([snows[i] for i in idx])
pad = np.pad(snow_stack, ((2, 2), (0, 0), (0, 0)), mode="edge")
vote = sum(pad[d:d + len(idx)].astype(np.uint8) for d in range(5))
snows = {i: vote[n] >= 3 for n, i in enumerate(idx)}     # majority of 5 frames: no one-frame blips
del snow_stack, pad, vote
# AI frost flecks: small bright dots that stay put for 17+ frames (real blowing snow moves on)
flecks = {i: np.zeros((BH, BW), bool) for i in idx}
statics = {i: np.zeros((BH, BW), bool) for i in idx}
transient = {}
if a.label_clear:
    # a passing flake is much brighter than that pixel usually is around this moment
    ex = np.stack([excess[i] for i in idx]).astype(np.float32)
    for n, i in enumerate(idx):
        lo, hi = max(0, n - 12), min(len(idx), n + 13)
        transient[i] = (ex[n] - np.median(ex[lo:hi], axis=0)) > 18
    del ex, excess
    bs = np.stack([brights[i] for i in idx])
    for n, i in enumerate(idx):
        lo, hi = max(0, n - 8), min(len(idx), n + 9)
        still = bs[lo:hi].min(axis=0).astype(np.uint8)
        statics[i] = still.astype(bool)
        nl, lab, st, _ = cv2.connectedComponentsWithStats(still)
        if a.keep_frost:                       # real-looking frost stays; anything still that touches the
            lab_near = np.unique(lab[(lab > 0) & ainks[i]])   # old text goes (dots, halos), whatever its size
            small = np.isin(lab, lab_near[lab_near > 0])
        else:
            small = np.isin(lab, np.flatnonzero(st[:, cv2.CC_STAT_AREA] <= 60)) & (lab > 0)
        flecks[i] = cv2.dilate(small.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    del bs

# ---- pass 2: build the label in bottle coordinates and warp it onto each frame ----------
out_frames = list(frames[:a.start])
log = []
for i in idx:
    box = to_ref(i)
    S = cols[i][None, :, :] * rowgs[i][:, None, None]
    L = box.mean(axis=2)
    sat = box.max(axis=2) - box.min(axis=2)
    white = (sat < 45) & (L > 110)
    white &= ~cv2.dilate((~white).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    carry = white & VIS
    if a.label_clear:                          # nothing still from right around the AI's old letters (their halo)
        near_ai = cv2.dilate(ainks[i].astype(np.uint8), np.ones((17, 17), np.uint8)).astype(bool)
        carry &= ~near_ai
    if a.specks and a.label_clear:             # blowing snow / bubbles crossing the label stay on top of it;
        carry |= transient[i] & (~near_ai | ((L - S.mean(axis=2)) > 20))   # near old print: only truly bright
    elif a.specks:
        carry |= (L - S.mean(axis=2)) > 22
    carry &= ~flecks[i] | (transient[i] if a.label_clear else False)
    if a.label_clear:                          # never carry the AI's ink, however faint
        carry &= ((box[..., 0] - box[..., 2]) - (S[..., 0] - S[..., 2])) < 6
    detail = np.where(carry[..., None], box - S, 0.0)
    if a.label_clear:                          # broad shading continues smoothly where nothing is carried
        paper = (carry & ~(transient[i])).astype(np.float32)
        low = cv2.GaussianBlur(np.where(paper[..., None] > 0, np.clip(box - S, -25, 25), 0.0), (0, 0), 8)
        low /= cv2.GaussianBlur(paper, (0, 0), 8)[..., None] + 1e-3
        wc = cv2.GaussianBlur(carry.astype(np.float32), (0, 0), 5)[..., None]   # soft hand-over, no outlines
        detail = wc * np.where(carry[..., None], detail, low) + (1 - wc) * low
    detail = cv2.GaussianBlur(np.clip(detail, -25, 90 if a.specks else 80), (0, 0), 0.6)
    new = np.clip(srgb(alb * lin(S)) + detail, 0, 255)
    new[PRINT] = np.clip(new[PRINT] * facs[i], 0, 255)
    if a.band_match:
        new = np.where(BAND_ROWS[..., None], np.clip(new * bfac[i][None, :, :], 0, 255), new)
    if a.relight:                              # light that moves over the bottle, read on plain paper only
        ok_px = (white & VIS & ~cv2.dilate(ainks[i].astype(np.uint8), np.ones((17, 17), np.uint8)).astype(bool)
                 & ~(transient[i] if a.label_clear else False)).astype(np.float32)
        rr = np.clip(cv2.GaussianBlur(L, (0, 0), 1.5) / (cv2.GaussianBlur(LMED, (0, 0), 1.5) + 1.0), 0.5, 2.0)
        num = cv2.GaussianBlur(rr * ok_px, (0, 0), 5)
        den = cv2.GaussianBlur(ok_px, (0, 0), 5)
        ratio = np.where(den > 0.05, num / (den + 1e-6), 1.0)
        ratio /= np.median(ratio[den > 0.05]) if (den > 0.05).any() else 1.0   # S already has the overall level
        ratio = np.clip(ratio, 0.8, 1.25)
        new = np.clip(srgb(lin(new) * ratio[..., None] ** 2.2), 0, 255)
    if a.grain:                                # the footage's own noise level, measured on clean paper
        hp = L - cv2.GaussianBlur(L, (0, 0), 1.2)
        ref_px = hp[white & VIS_CORE & ~((L - S.mean(axis=2)) > 22)]
        sigma = 1.4826 * np.median(np.abs(ref_px - np.median(ref_px))) if ref_px.size > 500 else 0.0
        g = cv2.GaussianBlur(np.random.default_rng(1000 + i).normal(0, 1, (BH, BW)).astype(np.float32), (0, 0), 0.6)
        g_hp = g - cv2.GaussianBlur(g, (0, 0), 1.2)
        g *= sigma / (g_hp.std() + 1e-6)
        bare = cv2.GaussianBlur((~carry).astype(np.float32), (0, 0), 1.0)
        new = np.clip(new + (g * bare)[..., None], 0, 255)
    keep = cv2.dilate((snows[i] | gloves[i].astype(bool)).astype(np.uint8), np.ones((5, 5), np.uint8))
    keep |= BURIED.astype(np.uint8)
    m = edge * (1 - cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 6.0 if a.keep_moving else 2.5))
    if a.debug and a.debug_frame == i:
        base = a.debug.rsplit(".", 1)[0]
        cv2.imwrite(base + f"-f{i}-box.png", np.clip(box, 0, 255).astype(np.uint8))
        cv2.imwrite(base + f"-f{i}-new.png", np.clip(new, 0, 255).astype(np.uint8))
        cv2.imwrite(base + f"-f{i}-masks.png", np.dstack([carry * 255, flecks[i] * 255, keep * 255]).astype(np.uint8))
        cv2.imwrite(base + f"-f{i}-detail.png", np.clip(128 + detail * 3, 0, 255).astype(np.uint8))

    # warp the label + its mask from bottle coordinates onto frame i (sub-pixel)
    Wm = warp_of(i)
    Winv = cv2.invertAffineTransform(Wm)
    corners = np.array([[x0, ya, 1], [x1, ya, 1], [x0, yb, 1], [x1, yb, 1]], np.float64) @ Wm.T
    fx0, fx1 = max(0, int(corners[:, 0].min()) - 40), min(W, int(corners[:, 0].max()) + 40)   # where the label
    fy0, fy1 = max(0, int(corners[:, 1].min()) - 40), min(H, int(corners[:, 1].max()) + 40)   # is in THIS frame
    Mi = Winv.copy()
    Mi[:, 2] = Winv[:, :2] @ np.array([fx0, fy0]) + Winv[:, 2] - np.array([x0, ya])
    sz = (fx1 - fx0, fy1 - fy0)
    new_f = cv2.warpAffine(new.astype(np.float32), Mi, sz,
                           flags=(cv2.INTER_CUBIC if a.sharp else cv2.INTER_LINEAR) | cv2.WARP_INVERSE_MAP,
                           borderMode=cv2.BORDER_REPLICATE)
    m_f = cv2.warpAffine(m.astype(np.float32), Mi, sz, flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    g = frames[i].astype(np.float32)
    reg = g[fy0:fy1, fx0:fx1]
    g[fy0:fy1, fx0:fx1] = reg * (1 - m_f[..., None]) + new_f * m_f[..., None]
    out = np.clip(g, 0, 255).astype(np.uint8)
    out_frames.append(out)
    log.append((i, *params[i], fit_err[i], float(snows[i].mean()), float(gloves[i].mean())))

if a.debug:
    with open(a.debug, "w") as fh:
        fh.write("frame,a,b,tx,ty,track_residual_px,snow_frac,glove_frac\n")
        for row in log:
            fh.write(",".join(f"{x:.5f}" if isinstance(x, float) else str(x) for x in row) + "\n")
if a.still:
    cv2.imwrite(a.still, out_frames[-1])
# frames go straight into x264 (a lossy intermediate would pulse in quality every GOP)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", f"{fps}", "-i", "-", "-i", a.src, "-map", "0:v", "-map", "1:a?",
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                        "-c:a", "copy", "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
for f in out_frames:
    enc.stdin.write(f.tobytes())
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")
print(f"k={k:.4f} label rows {ya}-{yb}, fixed frames {a.start}-{N - 1} -> {a.out}")
