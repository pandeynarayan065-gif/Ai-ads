#!/usr/bin/env python3
"""Spraymax 20 s UGC combo ad from real phone footage (9:16), Hinglish captions.

Hook -> how-to -> same-day before/after proof -> close-up result -> product -> lifestyle
-> combo offer -> end card. Source clips are portrait phone videos (864x1920 after rotation)
from the Drive folder; the front-camera bottle shot is mirrored so the label reads correctly.

  python3 video/render_real.py <real_clips_dir> [--preview]
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_combo as rc  # noqa: E402
import render_beach as rb  # noqa: E402
from render_brand import ease_out_quint, reveal  # noqa: E402
from render_typo import prog  # noqa: E402

W, H, FPS = rc.W, rc.H, rc.FPS
OUT = rc.OUT
WHITE = (255, 255, 255)
YELLOW = (255, 214, 64)

# key: (file, start s, dur s, crop x0, crop y0, crop w, flip)  crop height = w * 16/9
CLIPS = {
    "before": ("r5_1002_181712.mp4", 1.0, 2.6, 0, 192, 864, False),
    "spray":  ("r5_1002_181712.mp4", 33.0, 2.1, 0, 100, 864, False),
    "scrunch": ("r5_1002_181712.mp4", 52.2, 2.1, 0, 150, 864, False),
    "bef_half": ("r5_1002_181712.mp4", 12.5, 0.1, 0, 470, 864, False),
    "aft_half": ("r5_1002_181712.mp4", 78.3, 0.1, 0, 380, 864, False),
    "close": ("r6_1002_181932.mp4", 0.0, 2.6, 0, 150, 864, False),
    "bottle": ("r4_0919_190940.mp4", 2.0, 1.6, 0, 200, 864, True),
    "out":   ("r2_0904_201243.mp4", 2.0, 1.6, 0, 250, 864, False),
}
FR = {}


def load(d):
    for k, (f, t0, dur, x0, y0, cw, flip) in CLIPS.items():
        half = k.endswith("_half")                       # stacked before/after panels, 1080x960
        ch = 768 if half else int(round(cw * 16 / 9))
        ow, oh = (W, H // 2) if half else (W, H)
        vf = f"fps=30,crop={cw}:{ch}:{x0}:{y0},scale={ow}:{oh}:flags=lanczos" + (",hflip" if flip else "")
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-t", f"{dur}", "-i", str(Path(d) / f),
                              "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        FR[k] = np.frombuffer(raw, np.uint8).reshape(-1, oh, ow, 3)


def grade(a):
    x = a.astype(np.float32) / 255
    x = np.clip((x - 0.5) * 1.06 + 0.5 + 0.01, 0, 1)
    lum = x.mean(2, keepdims=True)
    x = lum + (x - lum) * 1.05
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def clip_img(k, lt):
    fr = FR[k]
    return Image.fromarray(grade(fr[min(len(fr) - 1, int(lt * FPS))])).filter(
        ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2)).convert("RGBA")


def bottom_shade(c, start=1150, strength=0.7):
    y = np.arange(H, dtype=np.float32)[:, None]
    g = np.clip((y - start) / (H - start), 0, 1) ** 1.2 * strength
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s.putalpha(Image.fromarray((np.repeat(g, W, 1) * 255).astype(np.uint8)))
    c.alpha_composite(s)


def shadow_text(c, txt, y, size, lt, t0, color=WHITE, weight="InterTight-800"):
    """Reels-style caption: bold type with a soft drop shadow, rises in and holds."""
    im = rc.txt(txt, weight, size, color)
    pad = 30
    sh = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sil = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sil.putalpha(im.getchannel("A").point(lambda v: int(v * 0.75)))
    sh.alpha_composite(sil, (pad + 4, pad + 6))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    sh.alpha_composite(im, (pad, pad))
    reveal(c, sh, W / 2, y, lt, t0, 0.4)


def tag(c, label, x, y, lt, t0, fill=(16, 4, 158), color=WHITE):
    q = prog(lt, t0, 0.3)
    if q <= 0:
        return
    sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
    rc.put(c, rc.pill(rc.txt(label, "InterTight-800", 40, color, tracking=3), fill, pad=(26, 12)), x, y, alpha=min(1, q * 3), scale=sc)


def shot(k, lines, tags=()):
    def scene(lt, dur):
        c = clip_img(k, lt)
        bottom_shade(c)
        for txt, y, size, t0, *col in lines:
            shadow_text(c, txt, y, size, lt, t0, col[0] if col else WHITE)
        for label, x, y, t0 in tags:
            tag(c, label, x, y, lt, t0)
        return c, "paper"
    return scene


def s_split(lt, dur):
    """Same-day before (top) / after (bottom), held stills with a slow push-in."""
    c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    z = 1.0 + 0.04 * lt / dur
    for k, y in (("bef_half", 0), ("aft_half", H // 2)):
        im = clip_img(k, 0)
        big = im.resize((int(W * z), int(H // 2 * z)), Image.BICUBIC)
        c.alpha_composite(big.crop(((big.width - W) // 2, (big.height - H // 2) // 2, (big.width - W) // 2 + W, (big.height - H // 2) // 2 + H // 2)), (0, y))
    ImageDraw.Draw(c).rectangle((0, H // 2 - 4, W, H // 2 + 4), fill=WHITE + (255,))
    tag(c, "BEFORE", 170, 80, lt, 0.1, fill=(40, 40, 48))
    tag(c, "AFTER", 160, H // 2 + 80, lt, 0.45)
    q = prog(lt, 0.8, 0.35)
    if q > 0:
        sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
        rc.put(c, rc.pill(rc.txt("Same din. Same banda.", "InterTight-800", 54, rc.INDIGO), WHITE, pad=(34, 16)), W / 2, H // 2,
               alpha=min(1, q * 3), scale=sc)
    return c, "paper"


def s_offer(lt, dur):
    c = rc.INDIGO_SET.copy()
    reveal(c, rc.txt("COMBO MEIN AUR SASTA.", "InterTight-800", 78, WHITE), W / 2, 250, lt, 0.05, 0.5)
    rb.card(c, 50, 525, 400, 1500, 2, lt, 0.15)
    rb.card(c, 555, 1030, 400, 1500, 3, lt, 0.3)
    q = prog(lt, 1.4, 0.35)
    if q > 0:
        sc = 0.6 + 0.4 * (1 + 2.7 * (q - 1) ** 3 + 1.7 * (q - 1) ** 2) if q < 1 else 1.0
        rc.put(c, rc.pill(rc.txt("BEST VALUE", "InterTight-800", 36, rc.INDIGO, tracking=2), (205, 225, 255), pad=(22, 10)),
               950, 400, alpha=min(1, q * 3), scale=sc)
    r = ease_out_quint(prog(lt, 1.7, 0.5))
    rc.put(c, rc.txt("Free shipping across India", "InterTight-600", 44, (215, 215, 255)), W / 2, 1640 + 12 * (1 - r), alpha=r)
    return c, "indigo"


def s_end(lt, dur):
    c = rc.PAPER_PLAIN.copy()
    p = ease_out_quint(prog(lt, 0.05, 0.5))
    rc.put(c, rc.LOGO, W / 2, 330 + 24 * (1 - p), alpha=p)
    reveal(c, rc.txt("Himalayan sea salt spray", "InterTight-800", 60, rc.INK), W / 2, 460, lt, 0.15, 0.45)
    k = ease_out_quint(prog(lt, 0.1, 0.6))
    rc.bottles(c, [dict(x=W / 2 - 150, base=1262 + 60 * (1 - k), h=600, angle=-12, alpha=k),
                   dict(x=W / 2 + 150, base=1262 + 60 * (1 - k), h=600, angle=12, alpha=k),
                   dict(x=W / 2, base=1272 + 60 * (1 - k), h=650, angle=0, alpha=k)])
    q = ease_out_quint(prog(lt, 0.35, 0.45))
    rc.put(c, rc.pill(rc.txt("Shop now  ·  spraymax.in", "InterTight-800", 46, WHITE), rc.INDIGO, pad=(48, 24)), W / 2, 1450 + 18 * (1 - q), alpha=q)
    r = ease_out_quint(prog(lt, 0.5, 0.45))
    rc.put(c, rc.txt("Pack of 2  ·  ₹799        Pack of 3  ·  ₹999", "InterTight-600", 38, (70, 70, 90)), W / 2, 1580 + 10 * (1 - r), alpha=r)
    rc.put(c, rc.txt("Free shipping across India", "InterTight-600", 34, (110, 110, 130)), W / 2, 1650 + 10 * (1 - r), alpha=r)
    return c, "paper"


TL = [
    (shot("before", [("FLAT HAIR?", 1420, 150, 0.15), ("Roz subah yahi scene?", 1580, 58, 0.5)], tags=[("BEFORE", W / 2, 1740, 0.8)]), 2.5),
    (shot("spray", [("Bas spray karo…", 1500, 96, 0.1)]), 2.0),
    (shot("scrunch", [("…aur haathon se scrunch.", 1500, 76, 0.1)]), 2.0),
    (s_split, 2.5),
    (shot("close", [("VOLUME. TEXTURE.", 1470, 104, 0.15), ("Chipchipa bilkul nahi.", 1610, 60, 0.6, YELLOW)]), 2.5),
    (shot("bottle", [("Himalayan sea salt spray", 1560, 70, 0.1)]), 1.5),
    (shot("out", [("College ready. Office ready.", 1560, 66, 0.1)]), 1.5),
    (s_offer, 3.5),
    (s_end, 2.0),
]
DUR = sum(d for _, d in TL)


def render_t(t, i):
    acc = 0.0
    for k, (fn, dur) in enumerate(TL):
        if t < acc + dur or k == len(TL) - 1:
            c, kind = fn(t - acc, dur)
            return rc.grain(c, i, 9.0 if kind == "indigo" else 3.0)
        acc += dur


def audio(path, sr=44100):
    """Placeholder upbeat bed, 100 BPM: kick/clap groove, bass, swish on each cut, chime at the end."""
    n = int(sr * DUR)
    out = np.zeros(n)
    rng = np.random.default_rng(9)

    def add(t0, sig):
        i = int(t0 * sr)
        if i < n:
            out[i:i + len(sig)] += sig[: n - i]

    def sm(x, k):
        return np.convolve(x, np.ones(k) / k, mode="same")

    beat = 0.6
    roots = [55.0, 65.41, 49.0, 43.65]
    t, k = 0.0, 0
    while t < DUR - 2.0:
        x = np.arange(int(0.3 * sr)) / sr
        add(t, np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-x * 32)) / sr) * np.exp(-x * 9) * 0.7)
        if k % 2:
            L = int(0.16 * sr)
            w = rng.standard_normal(L)
            add(t, (sm(w, 2) - sm(w, 12)) * np.exp(-np.arange(L) / sr * 30) * 0.2)
        L = int(0.03 * sr)
        w = rng.standard_normal(L)
        add(t + beat / 2, (w - sm(w, 3)) * np.exp(-np.arange(L) / sr * 150) * 0.05)
        L = int(0.5 * sr)
        x = np.arange(L) / sr
        add(t, np.sin(2 * np.pi * roots[(k // 4) % 4] * x) * np.minimum(1, x * 50) * np.exp(-x * 3) * 0.2)
        t += beat
        k += 1
    acc = 0.0
    for _, d in TL[:-1]:
        acc += d
        L = int(0.2 * sr)
        w = rng.standard_normal(L)
        add(acc - 0.2, (sm(w, 3) - sm(w, 30)) * np.linspace(0, 1, L) ** 2 * 0.15)
    x = np.arange(int(1.8 * sr)) / sr
    add(DUR - 2.0, sum(a * np.sin(2 * np.pi * f * x) for f, a in ((440, 0.1), (554.4, 0.07), (659.3, 0.06))) * np.exp(-x * 2))
    out = np.tanh(out * 1.3)
    out *= 0.82 / np.max(np.abs(out))
    out[-int(0.3 * sr):] *= np.linspace(1, 0, int(0.3 * sr))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((out * 32767).astype(np.int16).tobytes())


def main():
    rc.setup()
    load(sys.argv[1])
    if "--preview" in sys.argv:
        (OUT / "preview").mkdir(parents=True, exist_ok=True)
        acc = 0.0
        for _, d in TL:
            t = acc + d - 0.05
            render_t(t, int(t * FPS)).save(OUT / "preview" / f"real_{t:05.2f}.jpg", quality=88)
            acc += d
        print("previews written")
        return
    wav = OUT / "_real.wav"
    audio(wav)
    mp4 = OUT / "combo-real-ugc-20s.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-b:v", "9M", "-maxrate", "12M", "-bufsize", "20M",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(DUR * FPS))):
        p.stdin.write(render_t(i / FPS, i).tobytes())
    p.stdin.close()
    p.wait()
    wav.unlink()
    print("wrote", mp4, DUR)


if __name__ == "__main__":
    main()
