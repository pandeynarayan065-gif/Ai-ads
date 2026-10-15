#!/usr/bin/env python3
"""Clean up a CapCut export of the K2 film for Reels: back to its real frame rate, each shot sharpened only as much
as it needs, high-quality encode, audio untouched.

What was wrong with lv_0_20261015213702.mp4 (CapCut, 1080x1920, 60 fps, 14 Mbps):
- exported at 60 fps from 24/30 fps clips: 55% of its frames are exact duplicates (uneven 24->60 cadence = judder,
  and half the bitrate spent on copies). Every other frame is kept -> 30 fps (24 fps clips in the usual 2:3 cadence,
  30 fps clips exact).
- uneven sharpness: the ocean-wave crash (not Veo, a lower-res source) is clearly the softest, the wave curl, the
  hair and the wet close-up a bit soft. Each shot's edge crispness is measured and it is sharpened on luma only (no
  colour fringes), the change clamped so edges don't halo; crisp shots and the end screen are left alone.

  python3 ads/spraymax/k2-15s/enhance_export.py in.mp4 out.mp4
"""
import subprocess
import sys

import cv2
import numpy as np

src, out_path = sys.argv[1], sys.argv[2]
TARGET = 1.45           # edge crispness to aim soft shots towards (fine / blurred gradient on the strongest edges)
MAX_K = 1.3             # strongest sharpening amount
MIN_SHOT = 0.3          # s; shorter "shots" are fast motion inside a shot (whipping hair), not cuts
CLAMP = 14.0            # max change per pixel (8-bit), keeps edges from haloing

cap = cv2.VideoCapture(src)
in_fps = cap.get(cv2.CAP_PROP_FPS)
step = 2 if in_fps > 50 else 1
frames = []
i = 0
while True:
    ok, f = cap.read()
    if not ok:
        break
    if i % step == 0:
        frames.append(f)
    i += 1
FPS = in_fps / step
H, W = frames[0].shape[:2]
N = len(frames)

# ---- shots: hard cuts, where the colour make-up of the frame changes (whipping hair or splashing water moves pixels
# a lot but keeps the colours, so it doesn't count) ----
hists = []
for f in frames:
    hsv = cv2.cvtColor(cv2.resize(f, (135, 240), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1, 2], None, [16, 8, 8], [0, 180, 0, 256, 0, 256])
    hists.append(cv2.normalize(h, h).flatten())
dh = [cv2.compareHist(hists[k - 1], hists[k], cv2.HISTCMP_BHATTACHARYYA) for k in range(1, N)]
cuts = [0]
for k, v in enumerate(dh, start=1):
    if v > 0.35 and (k - cuts[-1]) / FPS >= MIN_SHOT:
        cuts.append(k)
shots = list(zip(cuts, cuts[1:] + [N]))


def detail(f):
    """Edge crispness: fine-scale gradient over slightly blurred gradient, on the strongest 3% of edges.
    Independent of how much texture a shot has (snow and water are smooth, not blurry)."""
    y = cv2.cvtColor(f, cv2.COLOR_BGR2YCrCb)[..., 0].astype(np.float32)
    gm = cv2.magnitude(cv2.Sobel(cv2.GaussianBlur(y, (0, 0), 2.0), cv2.CV_32F, 1, 0),
                       cv2.Sobel(cv2.GaussianBlur(y, (0, 0), 2.0), cv2.CV_32F, 0, 1))
    m = gm > np.percentile(gm, 97)
    yb = cv2.GaussianBlur(y, (0, 0), 1.5)
    g1 = cv2.magnitude(cv2.Sobel(y, cv2.CV_32F, 1, 0, ksize=1), cv2.Sobel(y, cv2.CV_32F, 0, 1, ksize=1))
    g2 = cv2.magnitude(cv2.Sobel(yb, cv2.CV_32F, 1, 0, ksize=1), cv2.Sobel(yb, cv2.CV_32F, 0, 1, ksize=1))
    return float(g1[m].mean() / (g2[m].mean() + 1e-6))


def is_card(f):                                        # the end screen: near-black with a little white text
    return f.mean() < 25 and (f > 200).mean() < 0.05


plan = []
for a, b in shots:
    mid = frames[(a + b) // 2]
    det = float(np.median([detail(frames[k]) for k in range(a, b, max(1, (b - a) // 5))]))
    if is_card(mid) or det >= TARGET:
        k_amt = 0.0
    else:
        k_amt = float(np.clip((TARGET / det - 1.0) * 6.0, 0.0, MAX_K))
    plan.append((a, b, det, k_amt))
    print(f"shot {a / FPS:5.2f}-{b / FPS:5.2f}s  crispness {det:5.3f}  sharpen {k_amt:.2f}")


def sharpen(f, k_amt):
    if k_amt <= 0:
        return f
    ycc = cv2.cvtColor(f, cv2.COLOR_BGR2YCrCb).astype(np.float32)
    y = ycc[..., 0]
    fine = y - cv2.GaussianBlur(y, (0, 0), 0.9)                  # fine texture
    mid = y - cv2.GaussianBlur(y, (0, 0), 2.0)                   # edges and form, for the softest shots
    boost = k_amt * fine + 0.35 * max(0.0, k_amt - 0.6) * mid
    ycc[..., 0] = y + np.clip(boost, -CLAMP, CLAMP)
    return cv2.cvtColor(np.clip(ycc, 0, 255).astype(np.uint8), cv2.COLOR_YCrCb2BGR)


tmp = out_path + ".video.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", f"{FPS:.6f}", "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
                        "-profile:v", "high", "-pix_fmt", "yuv420p", "-x264-params", "aq-mode=3",
                        "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
for a, b, det, k_amt in plan:
    for k in range(a, b):
        enc.stdin.write(sharpen(frames[k], k_amt).tobytes())
enc.stdin.close()
if enc.wait() != 0:
    raise SystemExit("ffmpeg failed")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", src, "-map", "0:v", "-map", "1:a?", "-c", "copy",
                "-movflags", "+faststart", "-shortest", out_path], check=True)
subprocess.run(["rm", "-f", tmp])
print(f"{in_fps:.0f} fps -> {FPS:.0f} fps, {N} frames, {len(shots)} shots -> {out_path}")
