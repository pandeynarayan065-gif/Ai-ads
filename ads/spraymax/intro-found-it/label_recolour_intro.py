#!/usr/bin/env python3
"""Fix the intro take's label by recolouring Seedance's own print, instead of replacing the label.

Narayan on the replaced label (label_lock_intro.py): "It lowk morphs and the lighting is distinguishable". So no
pixel geometry is redrawn here. Seedance spelled the wordmark right; what was wrong is colour: a lavender wordmark
(the brand is deep indigo; "Purple kyu he colour scheme") and a pale lavender band (the real band is a dark
teal-navy wave photo). Per frame:

1. Where: the label's two zones (wordmark, band), from the same ECC track as label_lock_intro.py, warped into the
   frame and feathered. They only need to be roughly right: the pixels themselves decide what is ink.
2. How much ink: each pixel's ink coverage comes from how far it falls below the local paper colour (the paper
   is estimated by a max filter, so it carries Seedance's own shading). The wordmark is measured on the green
   channel (purple ink drops green most), the band on the red channel.
3. Recolour: the ink part of each pixel is scaled per channel from Seedance's ink-to-paper ratio to the real
   label's (measured on label-flat.jpg). Paper, highlights, grain, shape and light are Seedance's own, untouched.

The small garbled lines are left as Seedance drew them (a few px tall on a phone).

  python3 ads/spraymax/intro-found-it/label_recolour_intro.py <clip.mp4> <out.mp4> [--scale 3 --track <take.mp4>] [--qa <dir>]
"""
import contextlib
import io
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import label_lock_intro as L  # noqa: E402

# Seedance's print over its paper (BGR), and the real print over white paper (label-flat.jpg), measured on frame 72
AI_WM, AI_BAND, AI_PAPER = np.array([190, 134, 150.]), np.array([186, 129, 118.]), np.array([232, 207, 210.])
# label-flat.jpg's wordmark is BGR (122, 38, 43); printed and lit it reads as the brand's royal indigo (#0A0096-ish,
# brand file), so the target is nudged that way; the band (157, 128, 85) nudged toward ocean blue, not teal
REAL_WM, REAL_BAND = np.array([150, 34, 46.]) / 255, np.array([170, 124, 80.]) / 255
WM_RATIO = REAL_WM / (AI_WM / AI_PAPER)            # what Seedance's ink must be multiplied by, per channel
BAND_RATIO = REAL_BAND / (AI_BAND / AI_PAPER)
V_OFF = -1.0
RAMP = 6                                            # frames over which the fix fades in where the track starts


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    s = int(a[a.index("--scale") + 1]) if "--scale" in a else 1
    take = a[a.index("--track") + 1] if "--track" in a else src
    qa = Path(a[a.index("--qa") + 1]) if "--qa" in a else None
    small = L.read(take, L.W, L.H)
    rate = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    k = L.fit_k(small[L.REF])[0]
    with contextlib.redirect_stdout(io.StringIO()):
        Hs, _ = L.track(small, k)
    locked = [i for i, h in enumerate(Hs) if h is not None]
    print(f"zones tracked on frames {locked[0]}-{locked[-1]}; ratios wordmark {WM_RATIO.round(2)}, band {BAND_RATIO.round(2)}")

    # zone masks in REF coordinates at output scale (a crop round the label)
    corners = L.label_pts((0.0, 1.0), k)
    pad = L.REF_R + 14
    bx0, by0 = int(corners[:, 0].min() - pad), int(corners[:, 1].min() - pad)
    bx1, by1 = int(corners[:, 0].max() + pad), int(corners[:, 1].max() + pad)
    cw, ch = (bx1 - bx0) * s, (by1 - by0) * s
    T = np.array([[1, 0, bx0 * s], [0, 1, by0 * s], [0, 0, 1]], np.float64)
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    px, py = (xx + bx0 * s + 0.5) / s - 0.5 - L.REF_BOTTOM[0], (yy + by0 * s + 0.5) / s - 0.5 - L.REF_BOTTOM[1]
    nrm = np.array([-L.REF_A[1], L.REF_A[0]])
    u, v = px * L.REF_A[0] + py * L.REF_A[1], px * nrm[0] + py * nrm[1]
    feather = lambda m: cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5 * s)  # noqa: E731
    z_band = feather((u > -3) & (u < 46) & (np.abs(v - V_OFF) < L.REF_R + 1.5))
    z_wm = feather((u > 51) & (u < 143) & (np.abs(v - V_OFF) < 13))

    # fade in with the bottle's size: while it is small Seedance's lettering is a garbled smudge, and darkening it
    # would only make the smudge stand out
    size = np.array([np.sqrt(abs(np.linalg.det(h[:2, :2].astype(np.float64)))) if h is not None else 0 for h in Hs])
    strength = np.clip((size - 0.55) / 0.25, 0, 1).astype(np.float32)
    strength[[i for i, h in enumerate(Hs) if h is None]] = 0
    print("bottle size vs REF, every 6th frame:", {i: round(float(size[i]), 2) for i in range(locked[0], len(Hs), 6)})

    S = np.diag([s, s, 1]).astype(np.float64)
    Si = np.diag([1 / s, 1 / s, 1]).astype(np.float64)
    hs, ws = L.H * s, L.W * s
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ws}x{hs}",
                            "-r", rate, "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p",
                            dst], stdin=subprocess.PIPE)
    fsize = ws * hs * 3
    i = 0
    while True:
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        f = np.frombuffer(buf, np.uint8).reshape(hs, ws, 3)
        if i >= len(Hs) or strength[i] == 0:
            enc.stdin.write(f.tobytes())
            i += 1
            continue
        Hn = S @ Hs[i].astype(np.float64) @ Si @ T
        zb = cv2.warpPerspective(z_band, Hn, (ws, hs), flags=cv2.INTER_LINEAR)
        zw = cv2.warpPerspective(z_wm, Hn, (ws, hs), flags=cv2.INTER_LINEAR)
        ys, xs = np.nonzero((zb > 0.01) | (zw > 0.01))
        o = f.copy()
        if len(ys):
            m = 40 * s
            y0, y1 = max(0, ys.min() - m), min(hs, ys.max() + m + 1)
            x0, x1 = max(0, xs.min() - m), min(ws, xs.max() + m + 1)
            img = f[y0:y1, x0:x1].astype(np.float32) / 255
            zb_, zw_ = zb[y0:y1, x0:x1], zw[y0:y1, x0:x1]
            # Seedance's local paper (its own shading): a max filter wider than the print, softened
            scale_here = np.sqrt(abs(np.linalg.det(Hs[i][:2, :2].astype(np.float64))))   # bottle size vs REF
            r_wm = int(max(5, 9 * s * scale_here)) | 1
            r_band = int(max(9, 60 * s * scale_here)) | 1
            paper_wm = cv2.GaussianBlur(cv2.dilate(img, np.ones((r_wm, r_wm), np.uint8)), (0, 0), r_wm / 4)
            paper_band = cv2.GaussianBlur(cv2.dilate(img, np.ones((r_band, r_band), np.uint8)), (0, 0), r_band / 6)
            # ink coverage, 0..1
            c_wm = np.clip((1 - img[..., 1] / np.maximum(paper_wm[..., 1], 1e-3)) / (1 - AI_WM[1] / AI_PAPER[1]), 0, 1)
            c_band = np.clip((1 - img[..., 2] / np.maximum(paper_band[..., 2], 1e-3)) / (1 - AI_BAND[2] / AI_PAPER[2]), 0, 1)
            # not the glove or rock: dark and unsaturated
            hsv = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
            dark = ((img.mean(2) < 0.3) & (hsv[..., 1] < 90)).astype(np.float32)
            keep = 1 - cv2.GaussianBlur(cv2.dilate(dark, np.ones((3 * s, 3 * s), np.uint8)), (0, 0), s)
            # the ink part of the pixel, recoloured: px + c * (paper * ai_ink_ratio) * (ratio - 1)
            out = img.copy()
            for c_, z_, ratio, paper, ai in ((c_wm, zw_, WM_RATIO, paper_wm, AI_WM),
                                              (c_band, zb_, BAND_RATIO, paper_band, AI_BAND)):
                w = (c_ * z_ * keep * strength[i])[..., None]
                ink = paper * (ai / AI_PAPER)
                out = out + w * ink * (ratio - 1)
            o[y0:y1, x0:x1] = np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8)
        enc.stdin.write(o.tobytes())
        if qa and i % 6 == 0:
            qa.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(qa / f"f{i:03d}.jpg"), np.hstack([f, o]))
        i += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"wrote {dst}: {i} frames, recoloured on {len(locked)} (from frame {locked[0]})")


if __name__ == "__main__":
    main()
