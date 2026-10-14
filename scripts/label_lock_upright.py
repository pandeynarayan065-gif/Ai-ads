#!/usr/bin/env python3
"""Lock the real label artwork onto an AI bottle in every frame of a clip.

For a bottle seen front-on with its axis vertical in frame (e.g. lying in snow, shot
from above). The bottle is modelled as a cylinder (centre x, radius); the label art
(label-front-panel.jpg) is wrapped around it at a uniform scale fitted to the AI's own
wordmark. Each frame keeps its own lighting, sparkle and frost: the art is multiplied
by that frame's paper shading and the frame's highlights are added back. Snow lying on
top of the label and the climber's glove passing over it are detected and left alone.

Usage:
  python3 scripts/label_lock_upright.py in.mp4 out.mp4 \
      --xc 598.5 --r 156.5 --wm-top 920 --wm-bottom 1392 --wm-x 596 --from 96
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--art", default="brand/spraymax/assets/label-front-panel.jpg")
ap.add_argument("--xc", type=float, required=True, help="bottle centre x (px)")
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
ap.add_argument("--debug", default=None, help="write the last frame's keep-mask here")
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

x0, x1 = int(a.xc - a.r) + 1, int(a.xc + a.r)
ya, yb = int(y0), min(H, int(y0 + NV * k))
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
alb_dark = alb.mean(axis=2) < 0.35
edge = np.clip((a.r - 8 - np.abs(gx - a.xc)) / 10.0, 0, 1) * np.clip((gy - y0) / 4.0, 0, 1)   # keep the real silhouette
art_print = ((art[..., 0] - art[..., 2]) > 50) & (art.mean(axis=2) < 170)
art_print[640:] = False                                                              # wordmark only, not the wave band
PRINT = cv2.remap(art_print.astype(np.float32), u, v, cv2.INTER_LINEAR) > 0.5      # new wordmark pixels
paper_rows = slice(0, max(10, int(640 * k)))                    # label rows above the old tagline/band

# track the bottle itself: match the tagline + band area of the clean last frame in each
# frame (the mitt works over the top of the bottle while this part stays visible)
ty0, ty1 = int(a.old_band_top - 45), int(a.old_band_top + 160)
tx0, tx1 = int(a.xc - 130), int(a.xc + 130)
tpl = cv2.cvtColor(frames[-1], cv2.COLOR_BGR2GRAY)[ty0:ty1, tx0:tx1]
P = 25
shifts = np.zeros((len(frames), 2), np.float32)
for i in range(a.start, len(frames)):
    g = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)[ty0 - P:ty1 + P, tx0 - P:tx1 + P]
    res = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    shifts[i] = (loc[0] - P, loc[1] - P) if score > 0.6 else (np.nan, np.nan)
for c in range(2):
    col = shifts[a.start:, c]
    ok = ~np.isnan(col)
    col[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), col[ok])
    pad = np.pad(col, 2, mode="edge")
    shifts[a.start:, c] = np.median(np.lib.stride_tricks.sliding_window_view(pad, 5), axis=1)
print("bottle drift px (dx,dy) start/mid/end:", shifts[a.start], shifts[(a.start + len(frames)) // 2], shifts[-1])

out_frames = []
for i, f in enumerate(frames):
    if i < a.start:
        out_frames.append(f)
        continue
    sx, sy = int(round(float(shifts[i, 0]))), int(round(float(shifts[i, 1])))
    by0, by1, bx0, bx1 = ya + sy, yb + sy, x0 + sx, x1 + sx
    box = f[by0:by1, bx0:bx1].astype(np.float32)
    L = box.mean(axis=2)
    sat = box.max(axis=2) - box.min(axis=2)
    Bc, Gc, Rc = box[..., 0], box[..., 1], box[..., 2]
    white = (sat < 45) & (L > 110)
    white &= ~cv2.dilate((~white).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)

    # paper shading: per column (around the bottle) x per row gain (along it)
    pw = white.copy()
    pw[paper_rows.stop:] = False
    col = np.full((box.shape[1], 3), np.nan, np.float32)
    for j in range(box.shape[1]):
        c = box[:, j][pw[:, j]]
        if len(c) > 20:
            col[j] = np.median(c, axis=0)
    for ch in range(3):
        cc = col[:, ch]
        ok = ~np.isnan(cc)
        cc[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), cc[ok])
        col[:, ch] = cv2.GaussianBlur(cc.reshape(1, -1), (0, 0), 3).ravel()
    rowg = np.full(box.shape[0], np.nan, np.float32)
    ref_lum = col.mean(axis=1)
    for r_ in range(paper_rows.stop):
        m = pw[r_]
        if m.sum() > 20:
            rowg[r_] = np.median(L[r_][m] / ref_lum[m])
    ok = ~np.isnan(rowg)
    rowg[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), rowg[ok])
    rowg = cv2.GaussianBlur(rowg.reshape(-1, 1), (0, 0), 25).ravel()
    S = col[None, :, :] * rowg[:, None, None]

    detail = np.where(white[..., None], box - S, 0.0)
    detail = cv2.GaussianBlur(np.clip(detail, -25, 80), (0, 0), 0.6)
    new = np.clip(srgb(alb * lin(S)) + detail, 0, 255)
    # match the ink colour to how the scene lit the AI's own wordmark
    old_ink = ((gx - a.wm_x) ** 2 < 62 ** 2) & (gy > a.wm_top) & (gy < a.wm_bottom) & ((Bc - Rc) > 40) & (L < 150)
    if old_ink.sum() > 500 and PRINT.sum() > 500:
        fac = np.clip(box[old_ink].mean(axis=0) / (new[PRINT].mean(axis=0) + 1e-3), 0.7, 1.8)
        new[PRINT] = np.clip(new[PRINT] * fac, 0, 255)

    # snow piled on the bottle. On bare paper it shows up as texture that departs from the smooth
    # paper shading; over the AI's dark band it shows up as large bright blobs. The AI's own print
    # (old wordmark, tagline, band text, wave crests) is thin, so the openings drop it.
    gx_b, gy_b = gx - x0, gy - ya
    dev = np.abs(L - S.mean(axis=2))
    lmin = cv2.erode(L, np.ones((5, 5), np.uint8))
    old_wm = (np.abs(gx - a.wm_x) < 62) & (gy > a.wm_top - 12) & (gy < a.wm_bottom + 12)
    old_tag = (gy > a.wm_bottom + 10) & (gy < a.old_band_top + 4)
    old_band = (gy >= a.old_band_top) & (gy <= a.old_band_bottom)
    snow_paper = (dev > 16) & (L > 115) & (lmin > 95) & ~old_wm & ~old_tag & ~old_band
    snow_paper = cv2.morphologyEx(snow_paper.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    snow_band = (old_band & (L > 138) & (sat < 55)).astype(np.uint8)
    snow_band = cv2.morphologyEx(snow_band, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    below = (gy > a.old_band_bottom) & (L > 120)                     # under the band: snow / base
    snow = (snow_paper | snow_band).astype(np.uint8) | below.astype(np.uint8)
    snow = cv2.morphologyEx(snow, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)).astype(bool)
    # the mitt: big red or black blobs (opening removes thin letter strokes)
    glove = (((Rc - Gc) > 60) | ((L < 75) & ((Bc - Rc) < 15))).astype(np.uint8)
    glove = cv2.morphologyEx(glove, cv2.MORPH_OPEN, np.ones((17, 17), np.uint8)).astype(bool)
    # anything that is not there in the clean last frame (the mitt, snow still being brushed off)
    refb = frames[-1][ya:yb, x0:x1].astype(np.float32)          # bottle-aligned: box is already shifted
    gain = box.mean() / max(refb.mean(), 1.0)
    moving = (np.abs(box - refb * gain).sum(axis=2) > 70).astype(np.uint8)
    moving = cv2.morphologyEx(moving, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))
    moving = cv2.dilate(moving, np.ones((a.glove_pad, a.glove_pad), np.uint8)).astype(bool)
    if a.static_below is not None:
        moving &= (gy + sy) < a.static_below                     # nothing passes over the lower label
    keep = cv2.dilate((snow | glove | moving).astype(np.uint8), np.ones((5, 5), np.uint8))
    if a.debug and i == len(frames) - 1:
        cv2.imwrite(a.debug, np.dstack([snow * 255, glove * 255, keep * 255]).astype(np.uint8))
    m = edge * (1 - cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 2.5))
    g = f.copy().astype(np.float32)
    g[by0:by1, bx0:bx1] = box * (1 - m[..., None]) + new * m[..., None]
    out_frames.append(np.clip(g, 0, 255).astype(np.uint8))

if a.still:
    cv2.imwrite(a.still, out_frames[-1])
with tempfile.TemporaryDirectory() as td:
    raw = Path(td) / "v.mp4"
    vw = cv2.VideoWriter(str(raw), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    for f in out_frames:
        vw.write(f)
    vw.release()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", a.src, "-map", "0:v", "-map", "1:a?",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart", a.out], check=True)
print(f"k={k:.4f} label rows {ya}-{yb}, fixed frames {a.start}-{len(frames) - 1} -> {a.out}")
