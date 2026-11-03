#!/usr/bin/env python3
"""The ocean ad's end-card lockup as standalone, animated overlays (Narayan: "Give the overlay with black screen",
"With spraymax.in and video with animation").

Lockup (1080x1920 layout, same place as in spraymax-ocean-12s-endcard.mp4, a little higher to make room): the white
logo 440 px wide, BORN IN HIMACHAL, then spraymax.in, all above the bottle cap in the hero shot and below the
Reels top bar.

Animation, 2.5 s at 24 fps (ease-out, nothing bounces):
  0.15-0.90 s  logo: fades in from a soft blur, drifting up 16 px and settling from 103% to 100%
  0.55-1.30 s  BORN IN HIMACHAL: fades in while its letter spacing tightens (tracking in)
  0.95-1.60 s  spraymax.in: fades in, rising 10 px
  1.60-2.50 s  hold

Writes, in this folder, for 1080x1920 and 4K:
  endcard-overlay-black-<size>.mp4      the animation on black (use Screen blend over footage)
  endcard-overlay-alpha-1080x1920.mov   the animation with transparency (ProRes 4444), for editors that take alpha
  endcard-overlay-black-<size>.png      the final lockup on black
  endcard-overlay-alpha-<size>.png      the final lockup on transparency

  python3 ads/spraymax/cinematic-12s-ocean/endcard/make_endcard_overlay.py [--preview <frame.png> <out.jpg>]
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "cinematic-12s"))
import build_animatic  # noqa: E402

FPS, DUR = 24, 2.5
LOGO_W, LOGO_Y = 440, 130
TAG, TAG_SIZE, TAG_GAP = "BORN IN HIMACHAL", 30, 34          # gap below the logo
URL, URL_SIZE, URL_GAP = "spraymax.in", 36, 22               # gap below the tagline
TAG_FILL, URL_FILL = (236, 240, 248), (250, 250, 252)        # near-white: they must read over a bright sky


def ease(t, t0, t1):
    x = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
    return 1 - (1 - x) ** 3


def spaced(d, xy_center, text, font, gap, fill, alpha):
    """Draw text letter by letter with `gap` px between letters, centred on xy_center[0]."""
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + gap * (len(text) - 1)
    x = xy_center[0] - total / 2
    for ch, w in zip(text, widths):
        d.text((x, xy_center[1]), ch, font=font, fill=fill + (int(alpha),))
        x += w + gap


def frame(t, sc):
    """The lockup at time t, as RGBA, at scale sc (1 = 1080x1920)."""
    W, H = int(1080 * sc), int(1920 * sc)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    logo = build_animatic.white_logo(int(LOGO_W * sc))
    # logo: blur -> sharp, drift up, settle in scale
    e = ease(t, 0.15, 0.90)
    if e > 0:
        s = 1.03 - 0.03 * e
        lg = logo.resize((max(1, int(logo.width * s)), max(1, int(logo.height * s))), Image.LANCZOS)
        pad = int(24 * sc)
        lay = Image.new("RGBA", (lg.width + 2 * pad, lg.height + 2 * pad), (0, 0, 0, 0))
        lay.alpha_composite(lg, (pad, pad))
        blur = 7 * sc * (1 - e)
        if blur > 0.2:
            lay = lay.filter(ImageFilter.GaussianBlur(blur))
        a = np.asarray(lay).copy()
        a[..., 3] = (a[..., 3].astype(np.float32) * e).astype(np.uint8)
        lay = Image.fromarray(a, "RGBA")
        cx = W / 2
        cy = (LOGO_Y + logo.height / sc / 2 + 16 * (1 - e)) * sc
        img.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))
    d = ImageDraw.Draw(img)
    tag_y = LOGO_Y + logo.height / sc + TAG_GAP
    e2 = ease(t, 0.55, 1.30)
    if e2 > 0:
        f = build_animatic.font(int(TAG_SIZE * sc))
        base_gap = d.textlength(" ", font=f)                 # the original lockup's one-space letter spacing
        spaced(d, (W / 2, tag_y * sc), TAG, f, base_gap + 8 * sc * (1 - e2), TAG_FILL, 245 * e2)
    e3 = ease(t, 0.95, 1.60)
    if e3 > 0:
        f = build_animatic.font(int(URL_SIZE * sc))
        url_y = tag_y + TAG_SIZE + URL_GAP + 10 * (1 - e3)
        spaced(d, (W / 2, url_y * sc), URL, f, 0.35 * d.textlength(" ", font=f), URL_FILL, 250 * e3)
    return img


def encode(path, w, h, frames, alpha=False):
    if alpha:
        args = ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
                "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(path)]
    else:
        args = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
                "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(path)]
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y"] + args, stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr)
    p.stdin.close()
    p.wait()


def main():
    if "--preview" in sys.argv:
        i = sys.argv.index("--preview")
        bg = Image.open(sys.argv[i + 1]).convert("RGBA").resize((1080, 1920))
        tiles = []
        for t in (0.45, 0.9, 1.25, 2.4):
            b = bg.copy()
            b.alpha_composite(frame(t, 1))
            tiles.append(b.convert("RGB").resize((360, 640), Image.LANCZOS))
        out = Image.new("RGB", (1440, 640))
        for k, tl in enumerate(tiles):
            out.paste(tl, (360 * k, 0))
        out.save(sys.argv[i + 2], quality=92)
        return
    n = int(round(DUR * FPS))
    for sc, tag in ((1, "1080x1920"), (2, "4k")):
        W, H = int(1080 * sc), int(1920 * sc)
        rgba = [frame(k / FPS, sc) for k in range(n)]
        black = []
        for fr in rgba:
            b = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            b.alpha_composite(fr)
            black.append(b.convert("RGB").tobytes())
        encode(HERE / f"endcard-overlay-black-{tag}.mp4", W, H, black)
        if tag == "1080x1920":
            encode(HERE / f"endcard-overlay-alpha-{tag}.mov", W, H, [fr.tobytes() for fr in rgba], alpha=True)
        rgba[-1].save(HERE / f"endcard-overlay-alpha-{tag}.png")
        Image.open(HERE / f"endcard-overlay-alpha-{tag}.png")
        last = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        last.alpha_composite(rgba[-1])
        last.convert("RGB").save(HERE / f"endcard-overlay-black-{tag}.png")
        print("wrote", tag)


if __name__ == "__main__":
    main()
