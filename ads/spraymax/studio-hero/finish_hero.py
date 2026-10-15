#!/usr/bin/env python3
"""Finish the studio hero clip (hero-8s.mp4): the real volume line on the label, and a motion-control push-in.

Veo kept the real label from the first frame almost perfectly (wordmark, small line, wave band, FOR ALL HAIR
TYPES), but garbled the tiny volume line "100ml/3.38fl.oz.". So only that line is replaced, in every frame:
- the label's band is followed by template matching against frame 0 (Veo's camera drifts and pushes in ~2-3%);
- Veo's garbled line is taken off the band (thin bright strokes, filled from the band around them) and the real
  line from the first frame (images/hero-first.jpg, real label locked on) is printed in its place, in the colour
  Veo gives its own white print (FOR ALL HAIR TYPES, just above) in that frame, at Veo's sharpness;
- while the splash runs over the band the line is left to the footage (crisp print under moving water is wrong).

Then the camera: Veo barely moved it, so a slow motion-control push-in is added (ease in/out, 1.00 -> 1.15,
ending higher, on the wordmark).

  python3 ads/spraymax/studio-hero/finish_hero.py ads/spraymax/studio-hero/clips/hero-8s.mp4 \
      ads/spraymax/studio-hero/images/hero-first.jpg out.mp4
"""
import subprocess
import sys

import cv2
import numpy as np

src, ref_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
ZOOM_END, END_CY = (float(sys.argv[4]) if len(sys.argv) > 4 else 1.15), 840.0                      # push-in: final scale, final centre row (wordmark)
TEXT = (1455, 1497, 450, 640)                       # y0, y1, x0, x1 of the volume line (frame 0 / reference)
FOR_LINE = (1422, 1440, 440, 715)                   # the FOR ALL HAIR TYPES line just above

cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while True:
    ok, f = cap.read()
    if not ok:
        break
    frames.append(f)
N = len(frames)
H, W = frames[0].shape[:2]
ref = cv2.imread(ref_path)
gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]

# ---- follow the label's band: translation vs frame 0, right where the line is (Veo also pushes in ~2-3%, so the
# cap and the band move differently; the band text area itself is matched), smoothed; the match score drops
# when the splash runs over the band ----
T0, T1, L0, L1 = 1415, 1500, 440, 720                             # FOR ALL HAIR TYPES + volume line + band
P = 40
tpl = gray[0][T0:T1, L0:L1]
shift = np.full((N, 2), np.nan)
score = np.zeros(N)
for i in range(N):
    res = cv2.matchTemplate(gray[i][T0 - P:T1 + P, L0 - P:L1 + P], tpl, cv2.TM_CCOEFF_NORMED)
    _, sc, _, (x, y) = cv2.minMaxLoc(res)
    dx = dy = 0.0
    if 0 < x < res.shape[1] - 1:
        a_, b_, c_ = res[y, x - 1], res[y, x], res[y, x + 1]
        dx = 0.5 * (a_ - c_) / (a_ - 2 * b_ + c_ - 1e-9)
    if 0 < y < res.shape[0] - 1:
        a_, b_, c_ = res[y - 1, x], res[y, x], res[y + 1, x]
        dy = 0.5 * (a_ - c_) / (a_ - 2 * b_ + c_ - 1e-9)
    score[i] = sc
    if sc > 0.7:
        shift[i] = (x - P + dx, y - P + dy)
for c in range(2):
    ok = ~np.isnan(shift[:, c])
    shift[~ok, c] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), shift[ok, c])
    shift[:, c] = cv2.GaussianBlur(np.pad(shift[:, c], 10, mode="edge").reshape(-1, 1), (1, 0), 2).ravel()[10:-10]
CLEAR = np.clip((cv2.GaussianBlur(np.pad(score, 6, mode="edge").reshape(-1, 1), (1, 0), 1.5).ravel()[6:-6]
                 - 0.66) / 0.1, 0, 1)                               # 1 = band clear of the splash
print(f"band drift: x {shift[:, 0].min():+.1f}..{shift[:, 0].max():+.1f}, y {shift[:, 1].min():+.1f}..{shift[:, 1].max():+.1f} px")

# ---- the real volume line (from the reference), as a coverage mask ----
y0, y1, x0, x1 = TEXT
M = 6
rr = cv2.cvtColor(ref[y0 - M:y1 + M, x0 - M:x1 + M], cv2.COLOR_BGR2GRAY).astype(np.float32)
bg_r = cv2.morphologyEx(rr, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
ex = rr - bg_r
ALPHA = np.clip(ex / max(np.percentile(ex[M:-M, M:-M], 99.5), 1.0), 0, 1)
ALPHA = np.clip((ALPHA - 0.12) / 0.7, 0, 1)                       # crisp it up to Veo's sharpness
ALPHA = cv2.GaussianBlur(ALPHA, (0, 0), 0.45)
ALPHA[:M], ALPHA[-M:], ALPHA[:, :M], ALPHA[:, -M:] = 0, 0, 0, 0



def patch(frame, i):
    dx, dy = shift[i]
    M_ = np.float32([[1, 0, -dx], [0, 1, -dy]])                     # this frame -> frame-0 coordinates
    box = cv2.warpAffine(frame, M_, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    box = box.astype(np.float32)
    w = float(CLEAR[i])                                              # 0 while the splash covers the band
    if w <= 0:
        return frame, w
    s = box[y0 - M:y1 + M, x0 - M:x1 + M]
    L = s.mean(axis=2)
    # Veo's garbled line off the band
    opened = cv2.morphologyEx(L, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    vt = ((L - opened) > 22).astype(np.uint8)
    vt = cv2.dilate(vt, np.ones((3, 3), np.uint8))
    vt[:M - 2], vt[-(M - 2):], vt[:, :M - 2], vt[:, -(M - 2):] = 0, 0, 0, 0
    clean = cv2.inpaint(np.clip(s, 0, 255).astype(np.uint8), vt, 3, cv2.INPAINT_TELEA).astype(np.float32)
    # Veo's own white print colour in this frame (FOR ALL HAIR TYPES)
    fl = box[FOR_LINE[0]:FOR_LINE[1], FOR_LINE[2]:FOR_LINE[3]].reshape(-1, 3)
    lum = fl.mean(axis=1)
    ink = fl[lum >= np.percentile(lum, 97)].mean(axis=0) * 0.92      # the smaller line prints a touch dimmer
    new = clean * (1 - ALPHA[..., None]) + ink[None, None, :] * ALPHA[..., None]
    # back into this frame, only around the line
    feather = np.zeros(s.shape[:2], np.float32)
    feather[2:-2, 2:-2] = 1
    feather = cv2.GaussianBlur(feather, (0, 0), 1.2) * w
    out_box = box.copy()
    out_box[y0 - M:y1 + M, x0 - M:x1 + M] = s * (1 - feather[..., None]) + new * feather[..., None]
    Mi = np.float32([[1, 0, dx], [0, 1, dy]])
    back = cv2.warpAffine(out_box, Mi, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    msk = np.zeros((H, W), np.float32)
    msk[y0 - M:y1 + M, x0 - M:x1 + M] = feather
    msk = cv2.warpAffine(msk, Mi, (W, H), flags=cv2.INTER_LINEAR)
    res = frame.astype(np.float32) * (1 - msk[..., None]) + back * msk[..., None]
    return np.clip(res, 0, 255).round().astype(np.uint8), w


def push_in(frame, i):
    t = i / (N - 1)
    e = t * t * (3 - 2 * t)                                          # ease in / out
    s = 1.0 + (ZOOM_END - 1.0) * e
    cy = H / 2 + (END_CY - H / 2) * e
    cx = W / 2
    A = np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
    out = cv2.warpAffine(frame, A, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    if s > 1.001:                                                    # make up the softness of the enlargement
        bl = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = cv2.addWeighted(out, 1 + 0.35 * (s - 1) / (ZOOM_END - 1), bl, -0.35 * (s - 1) / (ZOOM_END - 1), 0)
    return out


enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                        "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
ws = []
for i, f in enumerate(frames):
    p, w = patch(f, i)
    ws.append(w)
    enc.stdin.write((push_in(p, i) if ZOOM_END != 1.0 else p).tobytes())   # 1.0: the line only (for checking)
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")
ws = np.array(ws)
print(f"volume line replaced in {int((ws > 0.99).sum())}/{N} frames, faded in {int(((ws > 0) & (ws <= 0.99)).sum())}, "
      f"left to the splash in {int((ws <= 0).sum())}")
