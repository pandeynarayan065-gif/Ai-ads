#!/usr/bin/env python3
"""Spraymax Combo Drop: AI clips as full-screen B-roll between the motion graphics (9:16, 15 s).

B-roll beats (1-1.5 s each) are cut between the Combo Drop graphics on a 120 BPM grid.
Each source window was checked frame by frame for bottle/label morphing:
  g2 2.0-3.5  g5 3.0-4.5  g7 2.3-3.8  g6 1.8-3.3
The 1280x720 clips are cropped to a 9:16 slice (with a slow pan where the subject is wide),
graded to one look, lightly sharpened and grained to sit with the graphics.
Source clips are not in the repo (Drive folder); pass their directory:
  python3 video/render_mix.py <clips_dir> [--preview]
"""
import glob
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_combo as rc  # noqa: E402
from render_brand import ease_out_quint, reveal  # noqa: E402
from render_typo import ease_in_out, prog  # noqa: E402

W, H, FPS = rc.W, rc.H, rc.FPS
OUT = rc.OUT
WHITE = (255, 255, 255)
SRC_W, SRC_H = 1280, 720
CROP_W = int(round(SRC_H * W / H))      # 405 px 9:16 slice

# key: (clip, source start s, crop centre x at start, at end)
SHOTS = {
    "sea":    ("g2", 2.0, 880, 860),     # bottle floating, upright-ish
    "spray":  ("g7", 2.5, 790, 600),     # bottle + mist, drifting toward the hair
    "splash": ("g6", 2.0, 620, 620),     # crown splash on the salt rock
    "shore":  ("g5", 3.0, 470, 820),     # pan along the bottle, cap -> label
}
FRAMES = {}


def load(clips_dir):
    for key, (g, t0, _, _) in SHOTS.items():
        f = glob.glob(str(Path(clips_dir) / f"{g}_*.mp4"))[0]
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-i", f, "-t", "1.6",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        FRAMES[key] = np.frombuffer(raw, np.uint8).reshape(-1, SRC_H, SRC_W, 3)


def grade(a):
    """One look for all clips: gentle contrast, slightly muted, shadows pulled toward brand indigo."""
    x = a.astype(np.float32) / 255
    x = np.clip((x - 0.5) * 1.08 + 0.5, 0, 1)
    lum = x.mean(2, keepdims=True)
    x = lum + (x - lum) * 0.92
    w = (1 - lum) ** 2
    x += w * np.array([-0.03, -0.025, 0.06])
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


LEAK = None


def make_leak():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = ((xx - W * 1.05) / (W * 0.7)) ** 2 + ((yy - H * 0.15) / (H * 0.45)) ** 2
    a = np.exp(-d * 1.6)
    rgb = np.zeros((H, W, 3), np.float32) + np.array([255, 150, 90], np.float32)
    return np.dstack([rgb, a * 255]).astype(np.uint8)


def frame_marks(c, alpha):
    d = ImageDraw.Draw(c)
    col = WHITE + (int(200 * alpha),)
    m, L = 54, 70
    for (x, y, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line((x, y, x + sx * L, y), fill=col, width=4)
        d.line((x, y, x, y + sy * L), fill=col, width=4)


def sticker(c, lt, t0, kind):
    """Offer overlays that pop over the footage."""
    q = prog(lt, t0, 0.35)
    if q <= 0:
        return
    sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
    a = min(1, q * 3)
    if kind == "new":
        im = rc.pill(rc.txt("NEW  ·  THE COMBO COLLECTION", "InterTight-800", 36, rc.INDIGO, tracking=3), WHITE, pad=(30, 15))
        rc.put(c, im, W / 2, 1640, alpha=a, scale=sc)
    elif kind in (2, 3):
        old, new, save = rc.PRICES[kind]
        tag = rc.pill(rc.txt(f"PACK OF {kind}  ·  {new}", "InterTight-800", 50, WHITE), rc.INDIGO, pad=(30, 16), radius=20)
        rc.put(c, tag, W / 2, 1560, alpha=a, scale=sc)
        q2 = ease_out_quint(prog(lt, t0 + 0.18, 0.35))
        chip = rc.pill(rc.txt(f"SAVE {save}", "InterTight-800", 38, WHITE, tracking=2), None, pad=(24, 10), outline=WHITE)
        rc.put(c, chip, W / 2, 1680 + 14 * (1 - q2), alpha=q2)
    elif kind == "ship":
        im = rc.pill(rc.txt("Free shipping across India", "InterTight-800", 40, rc.INDIGO), WHITE, pad=(30, 15))
        rc.put(c, im, W / 2, 1600, alpha=a, scale=sc)


def broll(key, lines, sub=None, over=None):
    def scene(lt, dur):
        fr = FRAMES[key]
        img = Image.fromarray(grade(fr[min(len(fr) - 1, int(lt * 24))]))
        _, _, cx0, cx1 = SHOTS[key]
        p = ease_in_out(lt / dur)
        z = 1.0 + 0.05 * (lt / dur)                                   # slow push-in
        cw, ch = CROP_W / z, SRC_H / z
        cx = cx0 + (cx1 - cx0) * p
        cx = min(max(cx, cw / 2), SRC_W - cw / 2)
        box = (cx - cw / 2, (SRC_H - ch) / 2, cx + cw / 2, (SRC_H + ch) / 2)
        c = img.crop(tuple(int(round(v)) for v in box)).resize((W, H), Image.LANCZOS)
        c = c.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2)).convert("RGBA")
        # legibility: soft dark gradient behind the type
        g = np.zeros((H, W), np.float32)
        y = np.arange(H)[:, None]
        g += np.clip(1 - np.abs(y - 640) / 520, 0, 1) ** 1.5 * 0.55
        shade = Image.new("RGBA", (W, H), (6, 4, 40, 0))
        shade.putalpha(Image.fromarray((g * 255).astype(np.uint8)))
        c.alpha_composite(shade)
        # warm light leak drifting in, viewfinder marks, small logo
        lk = LEAK.copy()
        k = 0.35 + 0.35 * np.sin(lt * 3.1 + len(key))
        lk[..., 3] = (lk[..., 3].astype(np.float32) * k).astype(np.uint8)
        c.alpha_composite(Image.fromarray(lk, "RGBA"))
        frame_marks(c, ease_out_quint(prog(lt, 0.0, 0.3)))
        lg = rc.LOGO_WHITE
        c.alpha_composite(lg, (int(W / 2 - lg.width / 2), 120))
        if over:
            sticker(c, lt, over[1], over[0])
        for i, (txt, y0, size) in enumerate(lines):
            reveal(c, rc.txt(txt, "InterTight-800", size, WHITE), W / 2, y0, lt, 0.06 + 0.12 * i, 0.4)
        if sub:
            q = ease_out_quint(prog(lt, 0.3, 0.4))
            rc.put(c, rc.txt(sub, "InterTight-600", 40, (215, 215, 255)), W / 2, 870 + 12 * (1 - q), alpha=q)
        return c, "indigo"
    return scene


TL = [
    (broll("sea", [("ONE’S", 520, 190), ("GOOD.", 720, 190)], over=("new", 0.5)), 1.5, False),
    (rc.s_two, 1.5, False),
    (rc.s_pack(2), 2.0, False),
    (broll("spray", [("INSTANT", 560, 150), ("VOLUME.", 720, 150)], over=(2, 0.12)), 1.0, False),
    (rc.s_three, 1.5, False),
    (rc.s_pack(3), 2.0, False),
    (broll("splash", [("REAL", 560, 150), ("TEXTURE.", 720, 150)], over=(3, 0.12)), 1.0, False),
    (rc.s_compare, 2.0, False),
    (broll("shore", [("HIMALAYAN", 560, 132), ("SEA SALT.", 710, 132)], over=("ship", 0.15)), 1.0, False),
    (rc.s_end(0), 1.5, False),
]


def main():
    clips_dir = sys.argv[1]
    global LEAK
    rc.setup()
    LEAK = make_leak()
    logo = rc.LOGO
    white = Image.new("RGBA", logo.size, WHITE + (255,))
    white.putalpha(logo.getchannel("A"))
    rc.LOGO_WHITE = white.resize((260, int(260 * logo.height / logo.width)), Image.LANCZOS)
    load(clips_dir)
    rc.TIMELINES["mix"] = TL
    rc.FILES["mix"] = "combo-ai-broll-15s.mp4"
    if "--preview" in sys.argv:
        (OUT / "preview").mkdir(parents=True, exist_ok=True)
        for t in (0.9, 2.6, 4.6, 5.5, 8.9, 10.0, 11.8, 13.0, 14.6):
            rc.frame_at(TL, t, int(t * FPS)).save(OUT / "preview" / f"mix_{t:05.2f}.jpg", quality=90)
        print("previews written")
        return
    rc.render("mix")


if __name__ == "__main__":
    main()
