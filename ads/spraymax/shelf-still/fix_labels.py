#!/usr/bin/env python3
"""Fix the small label lines on the three bottles of the shelf still (images/20261103-180852-1.png).

Nano Banana kept the wordmark and the wave band but wrote garbled small text, including made-up "100% ..." and
"98% ..." lines, where the real label says "Instant Hair Volume & Texture" (above the band) and
"FOR ALL HAIR TYPES" / "100ml/3.38fl.oz." (white, on the band). Only those lines change; the AI's wordmark,
band photo, plastic, light and focus stay as they are.

Per bottle (found automatically in its x-range):
1. Measure: the body's centre and radius at the band, and the band's top and bottom edges.
2. Paint out the AI's small lines (its dark strokes above the band, its bright strokes inside the band) with
   OpenCV inpainting.
3. Lay in the real lines from video/assets/label-hires.jpg, placed by the real layout relative to the band, wrapped
   round the cylinder (the band's real width checks out against the AI band within ~4%), softened to the still's
   focus: the dark line multiplies into the paper, the white lines take the AI's own white.

4. The pump: the real nozzle hole faces the back-label side (product lock), so from the label side the head is plain;
   Nano Banana drew the hole facing front on two bottles, so a dark round blob on the pump head is painted out.

  python3 ads/spraymax/shelf-still/fix_labels.py <still.png> <out.png> [--qa <dir>]
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "video/assets/label-hires.jpg"           # 4x label-flat.jpg
AS = 4.0
X0 = 701.0                                             # front-panel centre (label-flat px)
BAND_TOP, BAND_BOT = 697.0, 950.0                      # the wave band (label-flat rows)
SMALL = (660, 688)                                     # rows holding "Instant Hair Volume & Texture"
NOZZLE_HOLES = [(514, 1268, 9), (764, 1268, 12)]          # native px of images/20261103-180852-1.png (centre, radius incl. rim)
BAND_TEXT = [(826, 853, 580, 824), (863, 890, 620, 782)]   # FOR ALL HAIR TYPES, 100ml/3.38fl.oz. (y0, y1, x0, x1)


def measure(img, xr):
    """Centre, radius, band top and bottom of the bottle whose body lies in columns xr (native px)."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(int)
    lum = img.astype(float).mean(2)
    xa, xb = xr
    sub_s = hsv[:, xa:xb, 1]
    # body columns: unsaturated (the backdrop is saturated blue), on rows of the label
    body = (sub_s < 80) & (lum[:, xa:xb] > 60)
    rows = np.nonzero(body.sum(1) > 0.5 * (xb - xa) * 0.6)[0]
    mid = int(np.median(rows))
    cols = np.nonzero(body[mid - 40:mid + 40].mean(0) > 0.8)[0]
    cx, r = xa + (cols[0] + cols[-1]) / 2, (cols[-1] - cols[0] + 1) / 2
    # band: the first long run of saturated rows (the blue waves) in the centre strip, below the wordmark; the bare
    # plastic under it is unsaturated, which separates it from the blue bounce on the base and the shelf below
    strip = lum[:, int(cx - r * 0.4):int(cx + r * 0.4)].mean(1)
    paper = np.percentile(strip[rows], 90)
    sat = hsv[:, int(cx - r * 0.4):int(cx + r * 0.4), 1].mean(1)
    cand = np.nonzero((sat > 55) & (np.arange(len(strip)) > mid))[0]
    runs = np.split(cand, np.nonzero(np.diff(cand) > 3)[0] + 1)
    band = next(run for run in runs if len(run) >= 40)
    return cx, r, band[0], band[-1], paper


def art_to_img_map(shape, cx, r, top, bot):
    """For every pixel: its label-flat coordinates (x, y), and where it lies on the visible cylinder."""
    sv = (bot - top) / (BAND_BOT - BAND_TOP)                   # image px per label-flat px
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    ay = BAND_TOP + (yy - top) / sv
    s = np.clip((xx - cx) / r, -0.999, 0.999)
    ax = X0 + np.arcsin(s) * r / sv
    return ax, ay, sv, np.abs(xx - cx) < r * 0.96


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    qa = Path(a[a.index("--qa") + 1]) if "--qa" in a else None
    img = cv2.imread(src)[:, :, :3].copy()
    H, W = img.shape[:2]
    art = cv2.imread(str(ART)).astype(np.float32) / 255
    art_lum = art.mean(2)
    out = img.copy()
    # the three bottles' columns (native px), from the measured layout at 1080 wide: 318-419, 489-590, 660-761
    k = W / 1080
    for (x0, x1) in ((318, 419), (489, 590), (660, 761)):
        xr = (int(x0 * k) + 6, int(x1 * k) - 6)
        cx, r, top, bot, paper = measure(img, xr)
        # work on a box round the label's lower part
        bx0, bx1 = int(cx - r - 6), int(cx + r + 7)
        by0, by1 = int(top - 0.55 * r), int(bot + 4)
        roi = out[by0:by1, bx0:bx1].copy()
        ax, ay, sv, on = art_to_img_map(roi.shape, cx - bx0, r, top - by0, bot - by0)
        print(f"bottle cx {cx:.1f} r {r:.1f} band {top}-{bot} ({bot - top + 1} px), {sv:.3f} px per label px")
        lum = roi.astype(np.float32).mean(2)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # 1. paint out the AI's small lines: dark strokes between the wordmark and the band, bright strokes on the band
        above = on & (ay > 630) & (ay < BAND_TOP - 1)
        local = cv2.medianBlur(roi, 9).astype(np.float32).mean(2)
        m_dark = above & (lum < local - 14)
        in_band = on & (ay > BAND_TOP + 18) & (ay < BAND_BOT - 18) & (np.abs(ax - X0) < 200)
        m_bright = in_band & (lum > local + 10) & (hsv[..., 1] < 90)
        # the AI's band text: the rows where bright strokes are dense (foam on the waves is sparse), and only the
        # columns its strokes span there
        counts = np.convolve(m_bright.sum(1).astype(float), np.ones(3) / 3, mode="same")
        if counts.max() >= 0.12 * 2 * r:
            pk = int(np.argmax(counts))                            # the densest row is the text line
            yr0 = pk
            while yr0 > 0 and counts[yr0 - 1] > 0.35 * counts[pk]:
                yr0 -= 1
            yr1 = pk
            while yr1 < len(counts) - 1 and counts[yr1 + 1] > 0.35 * counts[pk]:
                yr1 += 1
            yr0, yr1 = yr0 - 2, yr1 + 3
            cols = np.nonzero(m_bright[yr0:yr1].any(0))[0]
            xc0, xc1 = cols.min() - 3, cols.max() + 4
            yy_, xx_ = np.mgrid[0:roi.shape[0], 0:roi.shape[1]]
            # paint out only the AI text line; the foam elsewhere on the band stays untouched
            m_bright = in_band & (yy_ >= yr0) & (yy_ <= yr1) & (xx_ >= xc0) & (xx_ <= xc1) & (lum > local + 6)
            print(f"  AI band text rows {yr0 + by0}-{yr1 + by0}, cols {xc0 + bx0}-{xc1 + bx0}")
        else:
            m_bright = np.zeros_like(m_bright)
        mask = cv2.dilate((m_dark | m_bright).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
        clean = cv2.inpaint(roi, mask, 3, cv2.INPAINT_TELEA)
        # the AI's own white (its brightest band text) and paper (around the small line)
        white = np.percentile(roi[m_bright], 90, axis=0) if m_bright.sum() > 10 else np.array([235, 235, 235.])
        # 2. the real lines, sampled from the hires art at each pixel's label coordinates
        blur = max(0.6, 0.7 / sv / AS * AS)
        art_soft = cv2.GaussianBlur(art, (0, 0), 0.9 / sv * AS * 0.5)
        lay = cv2.remap(art_soft, (ax * AS).astype(np.float32), (ay * AS).astype(np.float32), cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REPLICATE)
        lay_l = lay.mean(2)
        res = clean.astype(np.float32) / 255
        # dark line: multiply the paper by the print (only on the small line's rows, inside the panel)
        sm = on & (ay > SMALL[0]) & (ay < SMALL[1]) & (np.abs(ax - X0) < 233)
        fac = np.where(sm[..., None], np.clip(lay / np.maximum(lay[..., :].max(2, keepdims=True), 1e-3) *
                                              lay_l[..., None] / 0.98, 0, 1), 1.0)
        res = res * fac
        # white lines on the band: text = much brighter than its local surroundings in the art
        loc = cv2.GaussianBlur(art_lum, (0, 0), 6 * AS)
        tmask_art = np.clip((art_lum - loc - 0.18) / 0.15, 0, 1)
        tm = cv2.remap(cv2.GaussianBlur(tmask_art, (0, 0), 0.9 / sv * AS * 0.5), (ax * AS).astype(np.float32),
                       (ay * AS).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        tmb = np.zeros_like(tm)
        for (y0, y1, xa, xb) in BAND_TEXT:                     # each line up to full white at its strokes
            box = (ay > y0) & (ay < y1) & (ax > xa) & (ax < xb) & on
            if box.any():
                tmb[box] = np.clip(tm[box] / max(np.percentile(tm[box], 99), 1e-3), 0, 1)
        tm = tmb[..., None]
        res = res * (1 - tm) + (white / 255) * tm
        out[by0:by1, bx0:bx1] = np.clip(res * 255 + 0.5, 0, 255).astype(np.uint8)
        if qa:
            qa.mkdir(parents=True, exist_ok=True)
            z = np.hstack([img[by0 - int(0.6 * r):by1, bx0:bx1], out[by0 - int(0.6 * r):by1, bx0:bx1]])
            cv2.imwrite(str(qa / f"bottle_{int(cx)}.png"), cv2.resize(z, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC))
    # 4. the pump heads: the nozzle holes Nano Banana drew facing the camera on bottles 1 and 2 (soft grey discs on the
    # actuators under the clear overcaps, located with a blob filter on this still); bottle 3 has none
    m = np.zeros(out.shape[:2], np.uint8)
    for (hx, hy, hr) in NOZZLE_HOLES:
        cv2.circle(m, (int(round(hx * W / 1536)), int(round(hy * H / 2752))), int(round(hr * W / 1536)), 255, -1)
    out = cv2.inpaint(out, m, 5, cv2.INPAINT_TELEA)
    cv2.imwrite(dst, out)
    print("wrote", dst)


if __name__ == "__main__":
    main()
