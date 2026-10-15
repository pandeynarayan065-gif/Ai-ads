#!/usr/bin/env python3
"""Make the spray bottle's overcap clear, like the real one, in the studio hero clip.

Veo drew the overcap as frosted, milky plastic: the gaps between the overcap wall and the white actuator inside
read light grey. The real overcap is clear: the dark backdrop shows through those gaps, the white actuator and
its nozzle disc sit crisply inside, and the clear wall shows only thin bright edges and a soft reflection.

Per frame:
- the cap is followed by template matching (scale + shift) against the reference frame (Veo pushes in ~2-3%);
- the backdrop behind the cap is rebuilt from the backdrop just left and right of it, row by row, with grain;
- inside the overcap but outside the actuator/ring (geometry measured on the reference frame), the milky haze
  becomes the backdrop seen through clear plastic plus a soft vertical reflection from the key light and thin
  bright wall edges and top rim;
- wherever the splash passes in front of the cap, Veo's own pixels are kept.

  python3 ads/spraymax/studio-hero/clear_cap.py in.mp4 out.mp4 [clarity 0..1, default 0.7]

The real overcap is clear but slightly frosted polypropylene (in the brand's own photos the white actuator shows
through it crisply, while the empty parts still glow a little), so by default the result is 70% of the way from
Veo's milky cap to glass-clear.
"""
import subprocess
import sys

import cv2
import numpy as np

src, out_path = sys.argv[1], sys.argv[2]
CLARITY = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7     # 1 = glass-clear, 0 = Veo's frosted cap
REF = 0
ONLY = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else None   # frames to write as stills

# geometry on the reference frame (1080x1920), measured on a contrast-enhanced crop
# The tops are arched (the camera looks slightly down onto the cap): top(x) = top + ARCH * (x - XC)^2.
XC, ARCH = 545.0, 0.0026
CAP = dict(x0=454.5, x1=630.0, top=129.5, bot=376.0, corner=6.0)       # overcap outline
ACT = dict(x0=474.0, x1=608.0, top=163.5, bot=296.0, corner=5.0)       # actuator inside
RING = dict(x0=462.0, x1=622.0, top=294.0, bot=376.0, arch=0.0)       # ring under the actuator (its top
                                                                       # meets the actuator: no gap between)
WIN = (100, 560, 400, 690)                                             # y0, y1, x0, x1 region handled

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
y0w, y1w, x0w, x1w = WIN
gy, gx = np.mgrid[y0w:y1w, x0w:x1w].astype(np.float32)


def rounded_rect(d, soft=0.8):
    """Anti-aliased mask of a box with an arched top and rounded top corners (signed distance, approx.)."""
    arch = d.get("arch", ARCH)
    top = d["top"] + arch * (gx - XC) ** 2
    inside = np.minimum.reduce([gx - d["x0"], d["x1"] - gx, (gy - top) / np.sqrt(1 + (2 * arch * (gx - XC)) ** 2),
                                d["bot"] - gy])
    c = d.get("corner", 0.0)
    if c:
        for cx, sgn in ((d["x0"] + c, -1), (d["x1"] - c, 1)):
            cy = d["top"] + arch * (cx - XC) ** 2 + c
            sel = (gy < cy) & ((gx - cx) * sgn > 0)
            dist = c - np.hypot(gx - cx, gy - cy)
            inside = np.where(sel, np.minimum(inside, dist), inside)
    return np.clip(inside / soft + 0.5, 0, 1)


M_CAP = rounded_rect(CAP)
M_ACT = rounded_rect(ACT)
M_RING = rounded_rect(RING)
CLEAR = np.clip(M_CAP - np.maximum(M_ACT, M_RING), 0, 1)             # where the backdrop shows through
d_in = cv2.distanceTransform((M_CAP > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
WALL = np.exp(-((d_in - 1.2) / 1.1) ** 2) * (M_CAP > 0.02)           # thin bright edge of the clear wall
TOP_RIM = np.exp(-((gy - (CAP["top"] + ARCH * (gx - XC) ** 2 + 2.0)) / 1.6) ** 2) * (M_CAP > 0.02)
xn = (gx - CAP["x0"]) / (CAP["x1"] - CAP["x0"])                        # 0..1 across the cap
REFL = (0.75 * np.exp(-((xn - 0.12) / 0.06) ** 2) + 0.25 * np.exp(-((xn - 0.88) / 0.05) ** 2))
REFL *= np.clip((gy - CAP["top"]) / 25, 0, 1)                          # key light front-left, rim right

ref_g = cv2.cvtColor(frames[REF], cv2.COLOR_BGR2GRAY)
ref_box = frames[REF][y0w:y1w, x0w:x1w].astype(np.float32)
TPL = ref_g[120:540, 430:660]


def find(i):
    """Similarity (scale s, shift tx, ty) mapping reference coords -> frame i, from the cap + collar template."""
    g = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
    best = (-1.0, 1.0, 0.0, 0.0)
    for s in np.arange(0.97, 1.061, 0.0075):
        t = cv2.resize(TPL, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        oy = max(0, int(120 * s + 330 * (1 - s)) - 60)                 # search around where it would be
        ox = max(0, int(430 * s + 545 * (1 - s)) - 60)                 # if scaled about the cap centre
        win = g[oy:min(H, oy + t.shape[0] + 120), ox:min(W, ox + t.shape[1] + 120)]
        if win.shape[0] < t.shape[0] or win.shape[1] < t.shape[1]:
            continue
        r = cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED)
        _, sc, _, (x, y) = cv2.minMaxLoc(r)
        if sc > best[0]:                                               # ref (430,120) -> (ox+x, oy+y)
            best = (sc, s, ox + x - 430 * s, oy + y - 120 * s)
    return best


track = np.array([find(i) for i in range(N)])
for c in (1, 2, 3):                                                    # smooth: the camera moves smoothly
    track[:, c] = cv2.GaussianBlur(np.pad(track[:, c], 8, mode="edge").reshape(-1, 1), (1, 0), 2.0).ravel()[8:-8]
print(f"cap track: scale {track[:, 1].min():.3f}..{track[:, 1].max():.3f}, "
      f"min match {track[:, 0].min():.2f} (frame {int(track[:, 0].argmin())})")

rng = np.random.default_rng(11)
enc = None if ONLY is not None else subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(fps), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                        "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
water_frac = []
for i in range(N):
    _, s, tx, ty = track[i]
    A = np.float32([[s, 0, tx], [0, s, ty]])                            # ref -> frame i
    Mb = cv2.invertAffineTransform(A)                                   # frame i -> ref
    full_ref = cv2.warpAffine(frames[i], Mb, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    box = full_ref[y0w:y1w, x0w:x1w].astype(np.float32)

    # backdrop behind the cap, row by row from both sides
    left = np.median(box[:, 456 - 45 - x0w:456 - 12 - x0w], axis=1)
    right = np.median(box[:, 630 + 12 - x0w:630 + 45 - x0w], axis=1)
    left = cv2.GaussianBlur(left.reshape(-1, 1, 3), (1, 0), 6).reshape(-1, 3)
    right = cv2.GaussianBlur(right.reshape(-1, 1, 3), (1, 0), 6).reshape(-1, 3)
    t = np.clip((gx[0] - 456) / (630 - 456), 0, 1)[None, :, None]
    bg = left[:, None, :] * (1 - t) + right[:, None, :] * t
    hp = box[:, 410 - x0w:446 - x0w] - cv2.GaussianBlur(box[:, 410 - x0w:446 - x0w], (0, 0), 1.5)
    sig = float(np.median(np.abs(hp)) * 1.4826) + 0.5
    bg = bg + cv2.GaussianBlur(rng.normal(0, sig, bg.shape).astype(np.float32), (0, 0), 0.6)

    # Veo's own light on the cap this frame (how bright the key light is right now)
    key = float(np.percentile(box[(M_CAP > 0.9) & (CLEAR > 0.9)].mean(axis=1), 90)) if (CLEAR > 0.9).any() else 200.0
    clear = bg * 0.9 + (REFL * (key - 40) * 0.35)[..., None] \
        + (WALL * (key - 30) * 0.55)[..., None] + (TOP_RIM * (key - 30) * 0.5)[..., None]

    # splash in front of the cap: keep Veo's pixels where this frame departs from the reference cap
    dev = np.abs(box - ref_box * (box[CLEAR > 0.9].mean() / max(ref_box[CLEAR > 0.9].mean(), 1))).mean(axis=2)
    water = cv2.GaussianBlur((dev > 45).astype(np.float32), (0, 0), 3)
    water = np.clip(water * 2.5, 0, 1)
    # the actuator is a white cylinder: let it fall off a little toward its sides so it isn't a flat cut-out
    xa = (gx - ACT["x0"]) / (ACT["x1"] - ACT["x0"])
    shade = 1 - 0.12 * np.clip(1 - np.minimum(xa, 1 - xa) / 0.12, 0, 1) * (M_ACT > 0.5)
    w = CLEAR * (1 - water) * CLARITY
    box = box * np.where((M_ACT > 0.5)[..., None], (1 - (1 - shade) * CLARITY)[..., None], 1.0)
    water_frac.append(float((water[CLEAR > 0.5] > 0.5).mean()))
    newbox = box * (1 - w[..., None]) + clear * w[..., None]
    w = np.maximum(w, (M_ACT > 0.5) * (1 - water) * CLARITY * (shade < 0.999))      # carry the actuator shading

    # back into frame i
    fr = frames[i].astype(np.float32)
    full_new = full_ref.astype(np.float32)
    full_new[y0w:y1w, x0w:x1w] = newbox
    wm = np.zeros((H, W), np.float32)
    wm[y0w:y1w, x0w:x1w] = w
    back = cv2.warpAffine(full_new, A, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    wmb = cv2.warpAffine(wm, A, (W, H), flags=cv2.INTER_LINEAR)
    out = fr * (1 - wmb[..., None]) + back * wmb[..., None]
    out = np.clip(out, 0, 255).round().astype(np.uint8)
    if ONLY is not None:
        if i in ONLY:
            cv2.imwrite(f"{out_path}-f{i}.png", out)
        continue
    enc.stdin.write(out.tobytes())
if enc is not None:
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit("ffmpeg failed")
wf = np.array(water_frac)
print(f"water in front of the cap in {int((wf > 0.05).sum())}/{N} frames (kept as Veo drew it there)")
