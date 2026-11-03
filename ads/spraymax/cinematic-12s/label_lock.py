#!/usr/bin/env python3
"""Lock one garbled line of small label text in a Seedance take to the real label artwork.

Take 1's label macro (frames 129-141, 5.38-5.92 s) renders "100ml/3.38fl.oz." as "100ml/3.3afl.oz.". For each
frame: find the line (template match across scales, seeded from a hand-measured box), paint the garbled strokes
out (OpenCV inpaint), then lay the real line from video/assets/label-hires.jpg on top in the frame's own text
colour and softness.

  python3 ads/spraymax/cinematic-12s/label_lock.py <take.mp4> <out.mp4>
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FRAMES = range(129, 142)                       # the label macro in take 1
SEED_FRAME = 135                               # ~5.65 s, where the box below was measured
SEED_BOX = (210, 955, 518, 992)                # x0, y0, x1, y1 of "100ml/3.3afl.oz." in that frame (720x1280)
LABEL_BOX = (2498, 3468, 3106, 3548)           # the real "100ml/3.38fl.oz." in label-hires.jpg (5612x3820)
W, H = 720, 1280


def read_frames(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (W * H * 3)
    return np.frombuffer(raw[:n * W * H * 3], np.uint8).reshape(n, H, W, 3).copy()


def track(frames):
    """Position and scale of the line in each frame, relative to the seed box."""
    x0, y0, x1, y1 = SEED_BOX
    g = cv2.cvtColor(frames[SEED_FRAME], cv2.COLOR_RGB2GRAY)
    tmpl = g[y0:y1, x0:x1]
    out = {}
    for i in FRAMES:
        gi = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)
        best = (-1, None, None)
        for s in np.linspace(0.85, 1.15, 31):
            t = cv2.resize(tmpl, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            sx0, sy0 = max(0, int(x0 - 80)), max(0, int(y0 - 80))
            win = gi[sy0:min(H, int(y1 + 80 * s + 80)), sx0:min(W, int(x1 + 80 * s + 80))]
            if win.shape[0] < t.shape[0] or win.shape[1] < t.shape[1]:
                continue
            r = cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(r)
            if mv > best[0]:
                best = (mv, s, (sx0 + ml[0], sy0 + ml[1]))
        out[i] = best
    return out


def real_line():
    lab = np.asarray(Image.open(ROOT / "video/assets/label-hires.jpg").convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = LABEL_BOX
    crop = lab[y0:y1, x0:x1]
    lum = crop.mean(2)
    bg = cv2.medianBlur(lum.astype(np.uint8), 31).astype(np.float32)
    alpha = np.clip((lum - bg - 25) / 70, 0, 1)            # white print over the wave photo
    return alpha


def lock(frames):
    alpha_full = real_line()
    tr = track(frames)
    x0, y0, x1, y1 = SEED_BOX
    bw, bh = x1 - x0, y1 - y0
    for i, (score, s, (px, py)) in tr.items():
        f = frames[i].astype(np.float32)
        w, h = int(round(bw * s)), int(round(bh * s))
        pad = 6                                                  # the garbled strokes overhang the real line a little
        bx0, by0 = max(px - pad, 0), max(py - pad, 0)
        box = f[by0:py + h + pad, bx0:px + w + pad]
        lum = box.mean(2)
        bg = cv2.medianBlur(lum.astype(np.uint8), 15).astype(np.float32)
        strokes = ((lum - bg) > 16).astype(np.uint8)
        strokes = cv2.dilate(strokes, np.ones((3, 3), np.uint8), iterations=2)
        bright = box[(lum - bg) > 30]
        col = np.percentile(bright, 85, axis=0) if len(bright) else np.array([190, 198, 212], np.float32)
        mask = np.zeros((H, W), np.uint8)
        mask[by0:by0 + box.shape[0], bx0:bx0 + box.shape[1]] = strokes * 255
        clean = cv2.inpaint(frames[i], mask, 5, cv2.INPAINT_TELEA).astype(np.float32)
        a = cv2.resize(alpha_full, (w, h), interpolation=cv2.INTER_AREA)
        a = cv2.GaussianBlur(a, (0, 0), 0.7)                     # match the take's softness
        reg = clean[py:py + h, px:px + w]
        clean[py:py + h, px:px + w] = reg * (1 - a[..., None]) + col * a[..., None]
        frames[i] = np.clip(clean, 0, 255).astype(np.uint8)
        print(f"frame {i}: match {score:.2f} scale {s:.3f} at {px},{py}")
    return frames


def main():
    take, out = Path(sys.argv[1]), Path(sys.argv[2])
    frames = lock(read_frames(take))
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", "24", "-i", "-", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-pix_fmt",
                            "yuv420p", str(out)], stdin=subprocess.PIPE)
    enc.stdin.write(frames.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
