#!/usr/bin/env python3
"""Motion graphics on the fixed shelf still (images/shelf-still-fixed.png), all in post, no AI video.

Narayan: "Recreate this with veo still, and then do motion graphics and give it motion, 100 accurate bottle and
label". The bottles stay exactly as fixed (fix_labels.py); nothing redraws them. On top of the still:

- a slow push-in, 100% -> 107%, eased, centred on the bottles;
- a studio light sweeping across each bottle in turn (left to right, a soft tilted band, stronger at the
  cylinder's centre), screened onto the bottles only;
- a glint running along the glass shelf's front edge after the sweeps;
- dust motes drifting up through the blue light, soft and out of focus;
- fresh grain every frame, so it reads as footage and not a frozen photo;
- version "lockup": the animated logo / BORN IN HIMACHAL / spraymax.in (endcard/make_endcard_overlay.py),
  placed in the space between the upper shelf and the caps.

  python3 ads/spraymax/shelf-still/animate_shelf.py <plate_916.png> <out.mp4> [--lockup] [--dur 3.0] [--size 1080x1920]
     [--preview <t> <out.jpg>]
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "cinematic-12s-ocean" / "endcard"))
FPS = 24
# bottles on the 9:16 plate (crop of the 1536x2752 still, 11 rows off the top), in 1536-wide plate px
BOTTLES = [(523.0, 66.0), (766.5, 66.0), (1009.5, 66.0)]   # centre x, body radius
CAP_TOP, BASE = 1222, 1812                                   # rows of the caps' tops and the bottles' bases
PLATE_W = 1536
FOCUS = (768, 1500)                                          # push-in centre (between the bottles and the shelf)
LOCKUP_DY = 450                                              # move the end-card lockup down into the space above the caps


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * x)


def bottle_masks(plate, sc):
    """Soft alpha of each bottle on the plate (at output scale), from its low saturation against the blue set."""
    hsv = cv2.cvtColor(plate, cv2.COLOR_BGR2HSV)
    lum = plate.astype(np.float32).mean(2)
    masks = []
    for cx, r in BOTTLES:
        x0, x1 = int((cx - r * 1.25) * sc), int((cx + r * 1.25) * sc)
        y0, y1 = int((CAP_TOP - 8) * sc), int((BASE + 2) * sc)
        m = np.zeros(plate.shape[:2], np.uint8)
        sub = ((hsv[y0:y1, x0:x1, 1] < 95) & (lum[y0:y1, x0:x1] > 45)).astype(np.uint8)
        sub = cv2.morphologyEx(sub, cv2.MORPH_CLOSE, np.ones((int(9 * sc) | 1, int(9 * sc) | 1), np.uint8))
        nb, lab, st, _ = cv2.connectedComponentsWithStats(sub)
        if nb > 1:
            sub = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
        m[y0:y1, x0:x1] = sub
        m = cv2.erode(m, np.ones((3, 3), np.uint8))
        masks.append(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2 * sc))
    return masks


def shelf_edge_row(plate, sc):
    """The glass shelf's bright front edge under the bottles: the brightest row just below the bases, off the bottles."""
    lum = plate.astype(np.float32).mean(2)
    ys = np.arange(int((BASE - 4) * sc), int((BASE + 40) * sc))
    cols = np.r_[int(60 * sc):int(420 * sc), int(1120 * sc):int(1480 * sc)]
    prof = lum[ys][:, cols].mean(1)
    return int(ys[np.argmax(prof)])


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    dur = float(a[a.index("--dur") + 1]) if "--dur" in a else (4.0 if "--lockup" in a else 3.0)
    W, H = (int(v) for v in (a[a.index("--size") + 1] if "--size" in a else "1080x1920").split("x"))
    plate = cv2.imread(src)
    plate = cv2.resize(plate, (W, H), interpolation=cv2.INTER_AREA if W < plate.shape[1] else cv2.INTER_LANCZOS4)
    sc = W / PLATE_W
    masks = bottle_masks(plate, sc)
    edge_y = shelf_edge_row(plate, sc)
    base = plate.astype(np.float32) / 255
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(7)
    # dust motes: x, y, radius, alpha, drift speed, sway phase (in 1080-wide units, scaled)
    k = W / 1080
    motes = [(rng.uniform(0, 1080), rng.uniform(150, 1800), rng.uniform(1.5, 5.5), rng.uniform(0.07, 0.28),
              rng.uniform(15, 45), rng.uniform(0, 6.28)) for _ in range(28)]
    lock = None
    if "--lockup" in a:
        import make_endcard_overlay as ov
        lock = ov
    n = int(round(dur * FPS))

    def render(t):
        img = base.copy()
        # light sweeps, one bottle after another
        for i, ((cx, r), m) in enumerate(zip(BOTTLES, masks)):
            t0, t1 = 0.45 + 0.2 * i, 1.35 + 0.2 * i
            if not (t0 <= t <= t1):
                continue
            p = ease_io((t - t0) / (t1 - t0))
            cxs, rs = cx * sc, r * sc
            pos = cxs + (-1.7 + 3.4 * p) * rs                      # band centre along x at the label's mid-height
            ymid = (CAP_TOP + BASE) / 2 * sc
            u = (xx - pos) - (yy - ymid) * np.tan(np.radians(18))  # tilted band (top leans right)
            band = np.exp(-0.5 * (u / (0.2 * rs)) ** 2)
            cyl = 0.55 + 0.45 * np.sqrt(np.clip(1 - ((xx - cxs) / rs) ** 2, 0, 1))
            amt = (0.46 * band * cyl * m * np.sin(np.pi * p) ** 0.6)[..., None]
            img = 1 - (1 - img) * (1 - amt * np.array([1.0, 0.98, 0.94]))
        # glint along the shelf's front edge
        g0, g1 = 1.35, 2.25
        if g0 <= t <= g1:
            p = ease_io((t - g0) / (g1 - g0))
            gx = (-0.1 + 1.2 * p) * W
            glint = np.exp(-0.5 * ((xx - gx) / (70 * k)) ** 2) * np.exp(-0.5 * ((yy - edge_y) / (2.2 * k)) ** 2)
            glint += 0.35 * np.exp(-0.5 * ((xx - gx) / (160 * k)) ** 2) * np.exp(-0.5 * ((yy - edge_y) / (7 * k)) ** 2)
            amt = (0.55 * glint * np.sin(np.pi * p))[..., None]
            img = 1 - (1 - img) * (1 - amt * np.array([0.92, 1.0, 0.86]))   # BGR: the glass edge's cyan-green white
        # push-in
        s = 1.0 + 0.07 * ease_io(t / dur)
        fx, fy = FOCUS[0] * sc, FOCUS[1] * sc
        M = np.float32([[s, 0, fx - s * fx], [0, s, fy - s * fy]])
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # dust motes (screen space, in front)
        layer = np.zeros((H, W), np.float32)
        for (x0, y0, rad, al, spd, ph) in motes:
            x = (x0 + 8 * np.sin(ph + t * 1.3)) * k
            y = (y0 - spd * t) * k
            rr = rad * k
            x_a, x_b, y_a, y_b = int(x - 4 * rr), int(x + 4 * rr) + 1, int(y - 4 * rr), int(y + 4 * rr) + 1
            if x_b < 0 or y_b < 0 or x_a >= W or y_a >= H:
                continue
            xa, xb, ya, yb = max(0, x_a), min(W, x_b), max(0, y_a), min(H, y_b)
            gy, gx_ = np.mgrid[ya:yb, xa:xb].astype(np.float32)
            layer[ya:yb, xa:xb] += al * np.exp(-0.5 * (((gx_ - x) ** 2 + (gy - y) ** 2) / (rr * 0.8) ** 2))
        img = 1 - (1 - img) * (1 - np.clip(layer, 0, 1)[..., None] * np.array([1.0, 0.92, 0.82]))
        # grain
        nz = np.random.default_rng(int(t * 1000) + 3).standard_normal((H, W)).astype(np.float32)
        nz = cv2.GaussianBlur(nz, (0, 0), 0.6 * k) * (2.4 / 255)
        img = img + nz[..., None]
        out = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
        if lock is not None:
            tl = t - 1.4
            if tl > 0:
                fr = lock.frame(tl, W / 1080)                          # RGBA, 1080x1920 layout scaled
                fr = np.asarray(fr).astype(np.float32) / 255
                dy = int(LOCKUP_DY * k)
                fr = np.roll(fr, dy, axis=0)
                fr[:dy] = 0
                al = fr[..., 3:4]
                out = np.clip(out.astype(np.float32) * (1 - al) + fr[..., 2::-1] * 255 * al, 0, 255).astype(np.uint8)
        return out

    if "--preview" in a:
        i = a.index("--preview")
        ts = [float(v) for v in a[i + 1].split(",")]
        frames = [cv2.resize(render(t), (360, 640), interpolation=cv2.INTER_AREA) for t in ts]
        cv2.imwrite(a[i + 2], np.hstack(frames))
        return
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt",
                            "yuv420p", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    for f in range(n):
        enc.stdin.write(render(f / FPS).tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"wrote {dst}: {n} frames, {dur:.2f} s at {W}x{H}; shelf edge at row {edge_y}")


if __name__ == "__main__":
    main()
