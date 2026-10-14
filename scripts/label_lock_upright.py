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

Usage:
  python3 scripts/label_lock_upright.py in.mp4 out.mp4 \
      --xc 598.5 --r 156.5 --wm-top 920 --wm-bottom 1392 --wm-x 596 \
      --old-band-top 1440 --old-band-bottom 1614 --from 96
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
ap.add_argument("--glove-pad", type=int, default=9, help="px of margin kept around the moving glove")
ap.add_argument("--static-below", type=float, default=None, help="ignore motion below this y (nothing crosses it)")
ap.add_argument("--from", dest="start", type=int, default=0, help="first frame to fix")
ap.add_argument("--still", default=None, help="also write the last fixed frame here")
ap.add_argument("--crf", type=int, default=16, help="x264 quality (0 = lossless master)")
ap.add_argument("--debug", default=None, help="write per-frame track + check numbers here (csv)")
a = ap.parse_args()

# art geometry (label-front-panel.jpg, measured): wordmark rows 48..628, centre column 247
ART_WM_TOP, ART_WM_BOTTOM, ART_U_C = 48.0, 628.0, 247.0
art = cv2.imread(a.art, cv2.IMREAD_COLOR).astype(np.float32)
art[:9] = 255.0                                   # print border line at the top edge
NV, NU = art.shape[:2]
k = (a.wm_bottom - a.wm_top) / (ART_WM_BOTTOM - ART_WM_TOP)     # frame px per art px
y0 = a.wm_top - ART_WM_TOP * k                                   # where the label starts
s_c = a.r * np.arcsin(np.clip((a.wm_x - a.xc) / a.r, -1, 1))

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
x0, x1 = int(a.xc - a.r) + 1, int(a.xc + a.r)
ya, yb = int(y0), min(H, int(y0 + NV * k))
BH, BW = yb - ya, x1 - x0
gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(ya, yb, dtype=np.float32))
s = a.r * np.arcsin(np.clip((gx - a.xc) / a.r, -1, 1))
u = (ART_U_C + (s - s_c) / k).astype(np.float32)
v = ((gy - y0) / k).astype(np.float32)
A = cv2.remap(art, u, v, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
A = cv2.GaussianBlur(A, (0, 0), 0.75)


def lin(x):
    x = np.clip(x / 255.0, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255.0


alb = lin(A)
edge = np.clip((a.r - 8 - np.abs(gx - a.xc)) / 10.0, 0, 1) * np.clip((gy - y0) / 4.0, 0, 1)   # keep the real silhouette
art_print = ((art[..., 0] - art[..., 2]) > 50) & (art.mean(axis=2) < 170)
art_print[640:] = False                                                              # wordmark only, not the wave band
PRINT = cv2.remap(art_print.astype(np.float32), u, v, cv2.INTER_LINEAR) > 0.5      # new wordmark pixels
paper_rows = max(10, int(640 * k))                    # label rows above the old tagline/band
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
parts = [(max(30, int(p0)), min(H - 30, int(p1)), max(30, int(q0)), min(W - 30, int(q1))) for p0, p1, q0, q1 in parts]
P = 25


def track(i, p):
    t0, t1, l0, l1 = p
    res = cv2.matchTemplate(gray[i][t0 - P:t1 + P, l0 - P:l1 + P], gray[-1][t0:t1, l0:l1], cv2.TM_CCOEFF_NORMED)
    _, sc, _, (x, y) = cv2.minMaxLoc(res)
    dx = dy = 0.0
    if 0 < x < res.shape[1] - 1:
        l_, c_, r_ = res[y, x - 1], res[y, x], res[y, x + 1]
        dx = 0.5 * (l_ - r_) / (l_ - 2 * c_ + r_ - 1e-9)
    if 0 < y < res.shape[0] - 1:
        l_, c_, r_ = res[y - 1, x], res[y, x], res[y + 1, x]
        dy = 0.5 * (l_ - r_) / (l_ - 2 * c_ + r_ - 1e-9)
    return x - P + dx, y - P + dy, sc


centres = np.array([((l0 + l1) / 2.0, (t0 + t1) / 2.0) for t0, t1, l0, l1 in parts], np.float64)
params = np.full((N, 4), np.nan)          # similarity p' = [a -b; b a] p + [tx, ty]
fit_err = np.zeros(N)
for i in idx:
    tr = np.array([track(i, p) for p in parts])
    good = tr[:, 2] > 0.8
    if good[:5].sum() < 2 or good.sum() < 3:
        continue
    rows, rhs = [], []
    for (qx, qy), (dx, dy, _), g_, xo in zip(centres, tr, good, X_ONLY):
        if not g_:
            continue
        rows.append([qx, -qy, 1, 0]); rhs.append(qx + dx)
        if not xo:
            rows.append([qy, qx, 0, 1]); rhs.append(qy + dy)
    M, rhs = np.array(rows), np.array(rhs)
    sol, *_ = np.linalg.lstsq(M, rhs, rcond=None)
    params[i] = sol
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
cols, rowgs, facs, snows, gloves = {}, {}, {}, {}, {}
ref_box = to_ref(N - 1)
for i in idx:
    box = to_ref(i)
    L = box.mean(axis=2)
    sat = box.max(axis=2) - box.min(axis=2)
    Bc, Gc, Rc = box[..., 0], box[..., 1], box[..., 2]
    white = (sat < 45) & (L > 110)
    white &= ~cv2.dilate((~white).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    pw = white.copy()
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
    snows[i] = cv2.morphologyEx(snow, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    # the mitt: big red or black blobs (the opening removes thin letter strokes)
    glove = (((Rc - Gc) > 60) | ((L < 75) & ((Bc - Rc) < 15))).astype(np.uint8)
    glove = cv2.morphologyEx(glove, cv2.MORPH_OPEN, np.ones((17, 17), np.uint8))
    if glove.any():
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
snow_stack = np.stack([snows[i] for i in idx])
pad = np.pad(snow_stack, ((2, 2), (0, 0), (0, 0)), mode="edge")
vote = sum(pad[d:d + len(idx)].astype(np.uint8) for d in range(5))
snows = {i: vote[n] >= 3 for n, i in enumerate(idx)}     # majority of 5 frames: no one-frame blips
del snow_stack, pad, vote

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
    detail = np.where(white[..., None], box - S, 0.0)
    detail = cv2.GaussianBlur(np.clip(detail, -25, 80), (0, 0), 0.6)
    new = np.clip(srgb(alb * lin(S)) + detail, 0, 255)
    new[PRINT] = np.clip(new[PRINT] * facs[i], 0, 255)
    keep = cv2.dilate((snows[i] | gloves[i].astype(bool)).astype(np.uint8), np.ones((5, 5), np.uint8))
    m = edge * (1 - cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 2.5))

    # warp the label + its mask from bottle coordinates onto frame i (sub-pixel)
    Wm = warp_of(i)
    Winv = cv2.invertAffineTransform(Wm)
    fx0, fx1 = max(0, x0 - 40), min(W, x1 + 40)
    fy0, fy1 = max(0, ya - 40), min(H, yb + 40)
    Mi = Winv.copy()
    Mi[:, 2] = Winv[:, :2] @ np.array([fx0, fy0]) + Winv[:, 2] - np.array([x0, ya])
    sz = (fx1 - fx0, fy1 - fy0)
    new_f = cv2.warpAffine(new.astype(np.float32), Mi, sz, flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
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
