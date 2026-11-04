#!/usr/bin/env python3
"""Paint out the stray marks Seedance put on the Red Bull take (takes/20261104-192915-1.mp4), frame by frame:

- wingsuit shot (6.50-7.08 s): small red pseudo-letters ("R9BB") on the navy suit, next to the big red panel. Mask: red
  pixels on the suit, minus the largest red blob (the panel); inpaint from the navy around them.
- ice-bucket shot (9.50-10.71 s): a white star logo and outline on each black racing glove, like a real glove brand's
  mark. Mask: light pixels inside the glove's silhouette (the dark glove shape, closed to fill the marks); inpaint.

  python3 ads/redbull-spec/cinematic-12s/clean_logos.py <take.mp4> <out.mp4> [--qa <dir>]
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

W, H, FPS = 720, 1280, 24
WING = (156, 170)        # frames of the wingsuit shot (6.50-7.08 s)
GLOVE = (228, 257)       # frames of the ice-bucket shot (9.50-10.71 s)


def wing_mask(f):
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    red = (((h < 8) | (h > 170)) & (s > 110) & (v > 90)).astype(np.uint8)
    red[:760] = 0                                         # the suit fills the lower part of the frame
    n, lab, st, _ = cv2.connectedComponentsWithStats(red)
    if n <= 1:
        return np.zeros((H, W), np.uint8)
    panel = 1 + np.argmax(st[1:, 4])
    keep = [i for i in range(1, n) if i != panel and st[i, 4] < 0.25 * st[panel, 4]]
    m = np.isin(lab, keep).astype(np.uint8) * 255
    return cv2.dilate(m, np.ones((5, 5), np.uint8))


def glove_mask(f):
    """Light marks inside the black glove's silhouette, never on the can. The glove is dark AND unsaturated (the can's
    dark blue is saturated, so it never counts as glove); the can (its blue and red print, grown and closed) is fenced
    off; then the glove shape is closed to fill the marks and only light, unsaturated pixels inside it are taken."""
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    print_ = ((((h >= 100) & (h <= 130)) | (h < 8) | (h > 170)) & (s > 90)).astype(np.uint8)
    can = cv2.morphologyEx(print_, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
    can = cv2.dilate(can, np.ones((5, 5), np.uint8))                 # a tight fence: the glove marks run right up to the can
    dark = ((v < 70) & (s < 70)).astype(np.uint8)
    dark[700:] = 0                                        # the gloves are in the top half; the ice is below
    closed = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (45, 45)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(closed)
    gloves = np.isin(lab, [i for i in range(1, n) if st[i, 4] > 8000]).astype(np.uint8)   # the two big glove shapes
    gloves = cv2.erode(gloves, np.ones((5, 5), np.uint8))                                 # stay off the glove's edge
    m = ((gloves > 0) & (can == 0) & (v > 70) & (s < 70)).astype(np.uint8) * 255
    return cv2.dilate(m, np.ones((9, 9), np.uint8)) & ((can == 0).astype(np.uint8) * 255)


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    qa = Path(a[a.index("--qa") + 1]) if "--qa" in a else None
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).copy()
    for i in range(len(frames)):
        m = None
        if WING[0] <= i < WING[1]:
            m = wing_mask(frames[i])
        elif GLOVE[0] <= i < GLOVE[1]:
            m = glove_mask(frames[i])
        if m is not None and m.any():
            before = frames[i].copy()
            frames[i] = cv2.inpaint(frames[i], m, 6, cv2.INPAINT_TELEA)
            if qa and i in (WING[0] + 6, GLOVE[0] + 2, GLOVE[0] + 15, GLOVE[1] - 2):
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
