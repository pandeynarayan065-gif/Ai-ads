#!/usr/bin/env python3
"""Spraymax Combo Drop: AI footage + motion graphics (9:16, 15 s).

0-6 s: four Gemini clips in a 2.39:1 cinematic band on the grainy indigo set,
graded to one look, slow push-ins, headline above the band. 6-15 s: the
Combo Drop graphics from render_combo.py. Cuts land on a 120 BPM grid.

Every source window was checked frame by frame for bottle/label morphing:
  g2 2.0-3.5  g5 3.0-4.5  g7 2.3-3.8  g6 1.8-3.3
Source clips are not in the repo (Drive folder); pass their directory:
  python3 video/render_mix.py <clips_dir> [--preview]
"""
import glob
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_combo as rc  # noqa: E402
from render_brand import ease_out_quint, reveal  # noqa: E402
from render_typo import prog  # noqa: E402

W, H, FPS = rc.W, rc.H, rc.FPS
OUT = rc.OUT
BAND_W, BAND_H = 1080, 452            # 2.39:1
BAND_CY = 1090
WHITE = (255, 255, 255)

# clip, source start (s), crop box in the 1280x720 source (x0, y0, x1) at 2.39:1
SHOTS = {
    "sea":    ("g2", 2.0, (0, 40, 1280)),
    "shore":  ("g5", 3.0, (0, 92, 1280)),
    "spray":  ("g7", 2.3, (52, 40, 1228)),
    "splash": ("g6", 1.8, (0, 30, 1280)),
}
FRAMES = {}


def load(clips_dir):
    for key, (g, t0, _) in SHOTS.items():
        f = glob.glob(str(Path(clips_dir) / f"{g}_*.mp4"))[0]
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-i", f, "-t", "1.6",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        FRAMES[key] = np.frombuffer(raw, np.uint8).reshape(-1, 720, 1280, 3)


def grade(a):
    """One look for clips from different generations: gentle contrast, shadows pulled toward brand indigo."""
    x = a.astype(np.float32) / 255
    x = np.clip((x - 0.5) * 1.07 + 0.5, 0, 1)
    lum = x.mean(2, keepdims=True)
    x = lum + (x - lum) * 0.92
    w = (1 - lum) ** 2
    x += w * np.array([-0.025, -0.02, 0.055])
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def band_frame(key, lt, dur):
    fr = FRAMES[key]
    i = min(len(fr) - 1, int(lt * 24))
    x0, y0, x1 = SHOTS[key][2]
    cw = x1 - x0
    ch = int(round(cw / (BAND_W / BAND_H)))
    z = 1.0 + 0.06 * (lt / dur)                       # slow push-in
    zw, zh = cw / z, ch / z
    cx, cy = x0 + cw / 2, y0 + ch / 2
    crop = Image.fromarray(grade(fr[i])).crop((int(cx - zw / 2), int(cy - zh / 2), int(cx + zw / 2), int(cy + zh / 2)))
    return crop.resize((BAND_W, BAND_H), Image.LANCZOS)


def footage(key, head=None, sub=None, out_flash=False):
    def scene(lt, dur):
        c = rc.INDIGO_SET.copy()
        band = band_frame(key, lt, dur).convert("RGBA")
        top = BAND_CY - BAND_H // 2
        sh = Image.new("RGBA", (W, BAND_H + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle((0, 40, W, BAND_H + 40), fill=(0, 0, 20, 120))
        c.alpha_composite(sh.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(24)), (0, top - 30))
        c.alpha_composite(band, (0, top))
        lg = rc.LOGO_WHITE
        c.alpha_composite(lg, (int(W / 2 - lg.width / 2), 250))
        if head:
            for k, (txt, y, t0) in enumerate(head):
                reveal(c, rc.txt(txt, "InterTight-800", 150, WHITE), W / 2, y, lt, t0, 0.45)
        if sub:
            q = ease_out_quint(prog(lt, 0.2, 0.45))
            rc.put(c, rc.txt(sub, "InterTight-600", 40, (200, 200, 255)), W / 2, BAND_CY + BAND_H / 2 + 90 + 14 * (1 - q), alpha=q)
        q = ease_out_quint(prog(lt + (1.5 if key != "sea" else 0), 0.4, 0.5))
        teaser = rc.pill(rc.txt("NEW  ·  THE COMBO COLLECTION", "InterTight-800", 34, rc.INDIGO, tracking=3), WHITE, pad=(30, 14))
        rc.put(c, teaser, W / 2, 1720 + 16 * (1 - q), alpha=q)
        if out_flash:
            f = prog(lt, dur - 0.16, 0.16)
            if f > 0:
                c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * f))))
        return c, "indigo"
    return scene


# headline builds across shots: ONE'S (sea) -> ONE'S GOOD. (shore, spray) -> WHY STOP AT ONE? (splash)
TL = [
    (footage("sea", head=[("ONE’S", 580, 0.15)]), 1.5, False),
    (footage("shore", head=[("ONE’S", 580, -1), ("GOOD.", 735, 0.05)], sub="Himalayan sea salt spray"), 1.5, True),
    (footage("spray", head=[("ONE’S", 580, -1), ("GOOD.", 735, -1)], sub="Instant volume. Real texture."), 1.5, True),
    (footage("splash", head=[("WHY STOP", 580, 0.05), ("AT ONE?", 735, 0.15)], out_flash=True), 1.5, True),
    (rc.s_two, 1.5, True),
    (rc.s_pack(2), 2.2, False),
    (rc.s_three, 1.3, True),
    (rc.s_pack(3), 2.2, True),
    (rc.s_end(0), 1.8, True),
]


def main():
    clips_dir = sys.argv[1]
    rc.setup()
    logo = rc.LOGO
    white = Image.new("RGBA", logo.size, WHITE + (255,))
    white.putalpha(logo.getchannel("A"))
    rc.LOGO_WHITE = white.resize((300, int(300 * logo.height / logo.width)), Image.LANCZOS)
    load(clips_dir)
    rc.TIMELINES["mix"] = TL
    rc.FILES["mix"] = "combo-ai-mix-15s.mp4"
    if "--preview" in sys.argv:
        (OUT / "preview").mkdir(parents=True, exist_ok=True)
        for t in (0.9, 2.2, 3.7, 5.2, 5.95, 6.9, 14.6):
            rc.frame_at(TL, t, int(t * FPS)).save(OUT / "preview" / f"mix_{t:05.2f}.jpg", quality=90)
        print("previews written")
        return
    rc.render("mix")


if __name__ == "__main__":
    main()
