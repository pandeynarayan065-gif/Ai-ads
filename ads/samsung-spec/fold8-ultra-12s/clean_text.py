#!/usr/bin/env python3
"""Paint out the fake text Seedance printed on the chip lid in the Samsung take (takes/20261104-194336-1.mp4).

Chip shot: 6.62-7.38 s (frames 159-176). The lid is a bright, unsaturated metal plate; its fake lettering is dark strokes
on it. Per frame: the lid = the largest bright, unsaturated blob, eroded well off its edge; it is refilled with a smooth
version of its own bare metal (letters left out), so its shading stays and every letter goes. The real chip name goes on later as a spec super, from Samsung's page.

  python3 ads/samsung-spec/fold8-ultra-12s/clean_text.py <take.mp4> <out.mp4> [--qa <dir>]
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

W, H, FPS = 720, 1280, 24
CHIP = (159, 177)


def lid_plate(f):
    """The chip lid: the largest bright, unsaturated blob (closed so its lettering counts as lid), eroded well off its edge
    so the gold traces and the lid's rim are never touched."""
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    v, s = hsv[..., 2], hsv[..., 1]
    plate = ((v > 140) & (s < 50)).astype(np.uint8)
    plate = cv2.morphologyEx(plate, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(plate)
    if n <= 1:
        return None
    big = 1 + np.argmax(st[1:, 4])
    if st[big, 4] < 20000:
        return None
    return cv2.erode((lab == big).astype(np.uint8), np.ones((15, 15), np.uint8))


def clean_lid(f):
    """Refill the lid with a smooth version of its own brushed metal: its shading is kept, every letter goes."""
    plate = lid_plate(f)
    if plate is None:
        return f
    img = f.astype(np.float32)
    g = img.mean(2)
    loc = cv2.GaussianBlur(g, (0, 0), 9)
    good = ((plate > 0) & (g >= loc - 6)).astype(np.float32)          # the lid's bare metal, letters left out
    w = cv2.GaussianBlur(good, (0, 0), 14)
    smooth = cv2.GaussianBlur(img * good[..., None], (0, 0), 14) / np.maximum(w, 1e-4)[..., None]
    grain = cv2.GaussianBlur(np.random.default_rng(0).normal(0, 3, g.shape).astype(np.float32), (0, 0), 0.8)
    smooth = smooth + grain[..., None]
    alpha = cv2.GaussianBlur(plate.astype(np.float32), (0, 0), 3)[..., None]
    return np.clip(img * (1 - alpha) + smooth * alpha, 0, 255).astype(np.uint8)


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    qa = Path(a[a.index("--qa") + 1]) if "--qa" in a else None
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).copy()
    for i in range(*CHIP):
        before = frames[i].copy()
        frames[i] = clean_lid(frames[i])
        if True:
            if qa and i in (CHIP[0] + 1, CHIP[0] + 9, CHIP[1] - 2):
                qa.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(qa / f"f{i:03d}.jpg"), np.hstack([before, frames[i]]))
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-pix_fmt",
                            "yuv420p", dst], stdin=subprocess.PIPE)
    enc.stdin.write(frames.tobytes())
    enc.stdin.close()
    enc.wait()
    print("wrote", dst)


if __name__ == "__main__":
    main()
