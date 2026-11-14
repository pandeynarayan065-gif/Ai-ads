#!/usr/bin/env python3
"""Burn-in captions for the Avrana hoodie reel (Narayan, 14 Nov 2026: "Add captions like this and the website is
avrana.co"), in the style of his reference reel (the Children of Khan "move to China" clip):

- phrase by phrase, one spoken phrase per caption, cut exactly on the spoken words (faster-whisper word timings);
- white Helvetica-style sans (Liberation Sans), lower case except "I", no punctuation, centred, one or two lines;
- a thin dark outline and a soft shadow, no box;
- the last caption is the website, shown while the voice says "get yours at avrana.co".
Captions sit at ~74% height, clear of Instagram's bottom UI. The audio is kept as it is.

  python3 ads/avrana/hoodie-reel/add_captions.py <source.mp4> <out.mp4> [--size 1080x1920] [--srt out.srt]
"""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
# (start s, text): each caption holds until the next one starts; the last holds to the end
CAPTIONS = [
    (0.00, "you'll never make it"),
    (1.22, "says the man who quit after one bad week"),
    (3.48, "he's got opinions about my art"),
    (5.20, "he's never finished a thing"),
    (6.68, "I've been broke"),
    (7.68, "I've been laughed at"),
    (8.92, "I started over twice"),
    (10.14, "still here"),
    (11.18, "you met me at a very artistic time of my life"),
    (14.02, "that hoodie looks sick dude"),
    (15.38, "where'd you get it"),
    (16.20, "www.avrana.co"),
]
SIZE = 0.058          # font size, fraction of frame width
MAX_W = 0.70          # wrap width, fraction of frame width (0.84 ran edge to edge: "not ideal")
CENTRE_Y = 0.74       # caption block centre, fraction of frame height


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) == 2 and len(lines[1].split()) == 1 and len(lines[0].split()) > 2:   # no single-word widow
        a = lines[0].split()
        lines = [" ".join(a[:-1]), a[-1] + " " + lines[1]]
    return lines


def caption_layer(W, H, text):
    s = W / 1080
    font = ImageFont.truetype(FONT, round(SIZE * W))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap(d, text, font, MAX_W * W)
    lh = font.size * 1.12
    y = CENTRE_Y * H - lh * len(lines) / 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    for i, ln in enumerate(lines):
        x = (W - d.textlength(ln, font=font)) / 2
        ds.text((x + 2 * s, y + i * lh + 3 * s), ln, font=font, fill=(0, 0, 0, 170))
        d.text((x, y + i * lh), ln, font=font, fill=(255, 255, 255, 255), stroke_width=max(1, round(2 * s)),
               stroke_fill=(20, 20, 20, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(5 * s))
    return Image.alpha_composite(shadow, layer)


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    a = sys.argv[1:]
    src, dst = a[0], a[1]
    W, H = (int(v) for v in (a[a.index("--size") + 1] if "--size" in a else "1080x1920").split("x"))
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                           "stream=r_frame_rate:format=duration", "-of", "default=nw=1", src],
                          capture_output=True, text=True).stdout
    kv = dict(l.split("=", 1) for l in info.strip().splitlines())
    num, den = kv["r_frame_rate"].split("/")
    fps, dur = float(num) / float(den), float(kv["duration"])
    if "--srt" in a:
        with open(a[a.index("--srt") + 1], "w") as f:
            for k, (t0, text) in enumerate(CAPTIONS):
                t1 = CAPTIONS[k + 1][0] if k + 1 < len(CAPTIONS) else dur
                f.write(f"{k + 1}\n{srt_time(t0)} --> {srt_time(t1)}\n{text}\n\n")
    layers = [caption_layer(W, H, t) for _, t in CAPTIONS]
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", src, "-vf", f"scale={W}:{H}:flags=lanczos",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", f"{num}/{den}", "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                            "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-shortest", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    n = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        t = n / fps
        k = max(i for i, (t0, _) in enumerate(CAPTIONS) if t0 <= t + 1e-6)
        frame = Image.frombuffer("RGB", (W, H), buf).convert("RGBA")
        enc.stdin.write(np.asarray(Image.alpha_composite(frame, layers[k]).convert("RGB")).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"wrote {dst}: {n} frames, {len(CAPTIONS)} captions")


if __name__ == "__main__":
    main()
