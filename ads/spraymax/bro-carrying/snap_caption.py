#!/usr/bin/env python3
"""Snapchat-style caption overlay: a full-width translucent black bar with white text, emoji in colour.

Writes two transparent PNGs: the full 1080x1920 frame with the bar at --y (centre, px; 850 = the reference
reel's position, ~44% down), and the bar alone (1080 wide) to place by hand in CapCut.

  python3 ads/spraymax/bro-carrying/snap_caption.py "tf is blud even spraying😭" --out DIR/name [--y 850]

Text: Liberation Sans (a free metric clone of Helvetica, the face Snapchat captions use). Emoji: Noto Color Emoji.
"""
import argparse
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
TEXT_FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
SIZE = 42                     # text px at 1080 wide
BAR_H = 76
BAR_ALPHA = 140               # ~55% black, like the app's caption bar

ap = argparse.ArgumentParser()
ap.add_argument("text")
ap.add_argument("--out", required=True, help="output path stem (writes STEM-1080x1920.png and STEM-bar.png)")
ap.add_argument("--y", type=int, default=850)
args = ap.parse_args()

tf = ImageFont.truetype(TEXT_FONT, SIZE)
ef = ImageFont.truetype(EMOJI_FONT, 109)       # the colour emoji font only has a 109 px strike


def is_emoji(ch):
    return ord(ch) > 0x2600 and unicodedata.category(ch) in ("So", "Sk") or 0x1F000 <= ord(ch) <= 0x1FAFF


# split into runs of text and emoji
runs = []
for ch in args.text:
    kind = "e" if is_emoji(ch) else "t"
    if runs and runs[-1][0] == kind and kind == "t":
        runs[-1][1] += ch
    else:
        runs.append([kind, ch])

asc, desc = tf.getmetrics()
emoji_h = int(SIZE * 1.12)
pieces = []                                    # (image RGBA, width)
for kind, s in runs:
    if kind == "t":
        x0, _, x1, _ = tf.getbbox(s)
        im = Image.new("RGBA", (x1 + 4, asc + desc), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), s, font=tf, fill=(255, 255, 255, 255))
        pieces.append((im, tf.getlength(s)))
    else:
        big = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
        ImageDraw.Draw(big).text((0, 0), s, font=ef, embedded_color=True)
        big = big.crop(big.getbbox())
        sc = emoji_h / big.height
        im = big.resize((max(1, round(big.width * sc)), emoji_h), Image.LANCZOS)
        pieces.append((im, im.width + SIZE * 0.08))

total = int(sum(w for _, w in pieces))
bar = Image.new("RGBA", (W, BAR_H), (0, 0, 0, BAR_ALPHA))
x = (W - total) / 2
for im, w in pieces:
    if im.height == emoji_h:                   # emoji: centred on the bar, a hair above the text baseline
        bar.alpha_composite(im, (round(x + SIZE * 0.08), (BAR_H - emoji_h) // 2 - 1))
    else:                                      # text: centred on the bar by its cap height
        cap = tf.getbbox("H")
        y = (BAR_H - (cap[3] - cap[1])) // 2 - cap[1]
        bar.alpha_composite(im, (round(x), y))
    x += w

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
bar.save(f"{out}-bar.png")
frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
frame.alpha_composite(bar, (0, args.y - BAR_H // 2))
frame.save(f"{out}-1080x1920.png")
print(f"{out}-bar.png ({W}x{BAR_H}), {out}-1080x1920.png (bar centred at y={args.y})")
