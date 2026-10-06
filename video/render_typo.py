#!/usr/bin/env python3
"""Spraymax 15 s kinetic-typography ad with product motion graphics.

Renders 1080x1920 @ 30 fps frames with Pillow/numpy, synthesises SFX, and muxes
an MP4 with ffmpeg. No AI generation: the bottle is the real label artwork
wrapped around the transparent bottle cut-out, so every letter on it is exact.

Usage: python3 video/render_typo.py [--preview]   (--preview renders key stills only)
"""
import math
import subprocess
import sys
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "brand/spraymax/assets"
FONTS = ROOT / "video/fonts"
OUT = ROOT / "ads/spraymax/himalayan-launch/video"
W, H, FPS, DUR = 1080, 1920, 30, 15.0
N = int(FPS * DUR)

BG_TOP, BG_BOT = (6, 7, 26), (14, 18, 70)
WHITE = (255, 255, 255)
ICE = (158, 201, 255)
INDIGO = (70, 70, 255)

rng = np.random.default_rng(7)


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def back_out(x, s=1.7):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


# ---------- fonts / text ----------
@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)


@lru_cache(None)
def text_img(txt, name, size, color=WHITE, tracking=0, stroke=0):
    f = font(name, size)
    widths = [f.getbbox(ch)[2] - f.getbbox(ch)[0] if ch != " " else size * 0.28 for ch in txt]
    asc, desc = f.getmetrics()
    w = int(sum(widths) + tracking * (len(txt) - 1) + 20 + stroke * 2)
    h = asc + desc + 20 + stroke * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 10 + stroke
    for ch, cw in zip(txt, widths):
        if ch != " ":
            bx = f.getbbox(ch)[0]
            if stroke:
                d.text((x - bx, 10 + stroke), ch, font=f, fill=(0, 0, 0, 0), stroke_width=stroke, stroke_fill=color + (255,))
            else:
                d.text((x - bx, 10), ch, font=f, fill=color + (255,))
        x += cw + tracking
    return im.crop(im.getbbox())


def paste(canvas, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.003 or scale <= 0.01:
        return
    im = img
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def glow(img, radius=18, strength=0.55):
    g = img.filter(ImageFilter.GaussianBlur(radius))
    a = g.getchannel("A").point(lambda v: int(v * strength))
    g.putalpha(a)
    out = Image.new("RGBA", (img.width + radius * 4, img.height + radius * 4), (0, 0, 0, 0))
    gp = Image.new("RGBA", out.size, (0, 0, 0, 0))
    gp.paste(g, (radius * 2, radius * 2))
    gp = gp.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(gp)
    out.alpha_composite(img, (radius * 2, radius * 2))
    return out


@lru_cache(None)
def word(txt, name, size, color=WHITE, tracking=0, stroke=0, glow_r=0):
    im = text_img(txt, name, size, color, tracking, stroke)
    return glow(im, glow_r) if glow_r else im


# ---------- bottle: real label wrapped on the cut-out ----------
class Bottle:
    def __init__(self, height=1120):
        b = Image.open(ASSETS / "bottle-blank.png").convert("RGBA")
        b = b.crop((440, 770, 940, 2500))  # bottle bbox with margin
        self.base = np.asarray(b).astype(np.float32) / 255.0
        lab = Image.open(ASSETS / "label-flat.jpg").convert("RGB").crop((6, 6, 1396, 948))
        self.label = np.asarray(lab).astype(np.float32) / 255.0
        self.lw = self.label.shape[1]
        self.front_u = 708 - 6
        # body geometry (in crop coords): x 471..906 -> 31..466, label band y 1470..2400 -> 700..1630
        self.cx, self.r = (31 + 466) / 2, (466 - 31) / 2
        self.ly0, self.ly1 = 700, 1630
        self.scale = height / self.base.shape[0]
        self.cache = {}

    def render(self, angle_deg):
        key = int(round(angle_deg / 3.0)) % 120
        if key in self.cache:
            return self.cache[key]
        ang = math.radians(key * 3.0)
        img = self.base.copy()
        ys = np.arange(self.ly0, self.ly1)
        xs = np.arange(int(self.cx - self.r) + 1, int(self.cx + self.r))
        dx = (xs - self.cx) / self.r
        theta = np.arcsin(np.clip(dx, -1, 1))
        u = (self.front_u + (theta + ang) / (2 * math.pi) * self.lw) % self.lw
        v = (ys - self.ly0) / (self.ly1 - self.ly0) * (self.label.shape[0] - 1)
        tex = self.label[v.astype(int)][:, u.astype(int)]
        region = img[self.ly0:self.ly1, xs[0]:xs[-1] + 1]
        lum = region[:, :, :3].mean(2, keepdims=True)
        shade = np.clip(lum / 0.93, 0.25, 1.0)
        spec = np.clip((lum - 0.94) / 0.06, 0, 1) * 0.6
        col = tex * shade
        col = col + (1 - col) * spec
        edge = np.clip((1 - np.abs(dx)) * 6, 0, 1)[None, :, None]  # soften silhouette edge
        mask = region[:, :, 3:4] > 0.5
        region[:, :, :3] = np.where(mask, col * edge + region[:, :, :3] * (1 - edge), region[:, :, :3])
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA")
        im = im.resize((int(im.width * self.scale), int(im.height * self.scale)), Image.LANCZOS)
        self.cache[key] = im
        return im

    def nozzle(self, cx, cy):
        """Screen position of the spray head for a bottle pasted centred at (cx, cy)."""
        h = self.base.shape[0] * self.scale
        return cx + (self.cx - self.base.shape[1] / 2) * self.scale, cy - h / 2 + 120 * self.scale


# ---------- background + particles ----------
def make_bg():
    g = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array(BG_TOP), np.array(BG_BOT)
    arr = (top * (1 - g) + bot * g).repeat(W, 1)
    yy, xx = np.mgrid[0:H, 0:W]
    vign = 1 - 0.55 * (((xx - W / 2) / W) ** 2 + ((yy - H * 0.55) / H) ** 2) * 2.2
    arr = arr * np.clip(vign, 0.35, 1)[:, :, None]
    x = np.arange(W)
    # two Himalayan ridges: a few broad, sharp summits (piecewise-linear peaks + fine jitter)
    for floor, top, col, cap, seed, n_peaks in ((1640, 1360, (20, 25, 78), 0.32, 3, 4), (1800, 1560, (7, 9, 30), 0.0, 11, 5)):
        r = np.random.default_rng(seed)
        px = np.sort(np.concatenate(([-150, W + 150], r.uniform(0, W, n_peaks))))
        py = np.empty_like(px)
        py[::2] = r.uniform(top, top + 90, len(py[::2]))      # summits
        py[1::2] = r.uniform(floor - 120, floor, len(py[1::2]))  # saddles
        ridge = np.interp(x, px, py)
        jitter = np.cumsum(r.normal(0, 2.2, W))
        ridge = ridge + (jitter - np.convolve(jitter, np.ones(81) / 81, mode="same")) * 1.4
        yy = np.arange(H)[:, None]
        inside = yy >= ridge[None, :]
        depth = np.clip((yy - ridge[None, :]) / 70, 0, 1)
        snowcap = (1 - depth) * cap * inside
        layer = np.array(col)[None, None, :] * (1 - snowcap[..., None]) + np.array([200, 215, 245])[None, None, :] * snowcap[..., None]
        arr = np.where(inside[..., None], layer, arr)
    haze = np.clip((np.arange(H) - 1250) / 500, 0, 1)[:, None, None] * np.array([18, 22, 60])[None, None, :]
    arr = np.clip(arr + haze * 0.35, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


BG = None
FLAKES = rng.uniform(0, 1, (140, 4))  # x, y, size, speed
MIST = rng.uniform(0, 1, (260, 4))  # angle, speed, size, life


def snow(canvas, t, intensity=1.0):
    d = ImageDraw.Draw(canvas)
    for x, y, s, sp in FLAKES:
        px = (x * W + math.sin(t * 0.8 + y * 9) * 30 - t * 60 * sp) % W
        py = (y * H + t * (80 + 220 * sp)) % H
        r = 1 + s * 3.2
        a = int((60 + 120 * s) * intensity)
        d.ellipse((px - r, py - r, px + r, py + r), fill=(220, 235, 255, a))


def mist(canvas, t, t0, nx, ny, dur=1.4, kill=None):
    age_all = t - t0
    if age_all < 0 or age_all > dur + 0.6:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, (a, sp, s, life) in enumerate(MIST):
        born = (i / len(MIST)) * dur * 0.6
        age = age_all - born
        L = 0.35 + life * 0.5
        if age < 0 or age > L:
            continue
        ang = math.radians(-60 - a * 60)  # up and to the right, cone
        dist = (250 + sp * 650) * ease_out(age / L)
        px, py = nx + math.cos(ang) * dist * -1, ny + math.sin(ang) * dist
        px = nx + abs(math.cos(ang)) * dist
        r = 2 + s * 9 + age * 55
        fade = 1 - prog(t, kill, 0.3) if kill else 1
        al = int(110 * (1 - age / L) * (0.4 + s) * fade)
        d.ellipse((px - r, py - r, px + r, py + r), fill=(225, 238, 255, al))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(11)))


def flash(canvas, amount):
    if amount > 0.01:
        canvas.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * amount))))


# ---------- scenes ----------
BOTTLE = None
LOGO = None


def slam(canvas, img, t, t0, cx, cy, hold=10.0, base=1.0):
    p = prog(t, t0, 0.22)
    if p <= 0:
        return
    scale = base * (1.6 - 0.6 * ease_out(p))
    alpha = clamp(p * 2)
    if t > t0 + hold:
        q = prog(t, t0 + hold, 0.18)
        alpha *= 1 - q
        scale *= 1 + 0.15 * q
    paste(canvas, img, cx, cy, scale, alpha)


def shake(t, t0, amt=14):
    p = prog(t, t0, 0.25)
    if p <= 0 or p >= 1:
        return 0, 0
    k = (1 - p) * amt
    return math.sin(t * 90) * k, math.cos(t * 77) * k


def frame(t):
    c = BG.copy()
    snow(c, t, 0.9 if t < 12.6 else 0.6)
    ox, oy = 0, 0

    # S1 0-2: FLAT / HAIR?
    if t < 2.15:
        sx, sy = shake(t, 0.15)
        slam(c, word("FLAT", "Anton-Regular", 360, WHITE), t, 0.15, W / 2 + sx, 760 + sy, hold=1.85)
        sx, sy = shake(t, 0.75)
        slam(c, word("HAIR?", "Anton-Regular", 360, ICE, glow_r=22), t, 0.75, W / 2 + sx, 1130 + sy, hold=1.25)

    # S2 2-5: GEL? TOO STIFF. / WAX? TOO GREASY.
    for t0, q, a in ((2.05, "GEL?", "TOO STIFF."), (3.55, "WAX?", "TOO GREASY.")):
        if t0 <= t < t0 + 1.55:
            slam(c, word(q, "Anton-Regular", 300, WHITE), t, t0, W / 2, 780, hold=1.3)
            slam(c, word(a, "Anton-Regular", 150, ICE, tracking=6), t, t0 + 0.42, W / 2, 1060, hold=0.9)
            p = prog(t, t0 + 0.7, 0.2)  # strike-through
            if p > 0 and t < t0 + 1.35:
                img = word(q, "Anton-Regular", 300)
                d = ImageDraw.Draw(c)
                x0 = W / 2 - img.width / 2 - 20
                d.rectangle((x0, 770, x0 + (img.width + 40) * ease_out(p), 792), fill=INDIGO + (255,))

    # S3 5-8: MEET + spinning bottle rise + giant outline word
    if 5.0 <= t < 12.75:
        # scrolling outline wordmark behind
        p = prog(t, 5.0, 7.7)
        big = word("SPRAYMAX", "Anton-Regular", 520, (90, 100, 220), stroke=3)
        a = clamp((t - 5.0) / 0.5) * (1 - prog(t, 12.4, 0.35)) * 0.55
        paste(c, big, W / 2 + 900 - 1800 * p, 980, 1.0, a)
    if 5.0 <= t < 6.6:
        slam(c, word("INTRODUCING", "Montserrat-ExtraBold", 64, ICE, tracking=22), t, 5.0, W / 2, 330, hold=1.3)
    if 5.0 <= t < 15.0:
        if t < 8.0:  # rise + spin 2 turns, ease to front
            p = ease_out(prog(t, 5.15, 2.6))
            by = 1920 + 700 - (2620 - 1080) * p
            angle = 720 * (1 - p)
            bscale = 1.0
        elif t < 10.6:  # gentle sway, stage left
            p = ease_in_out(prog(t, 8.0, 0.6))
            by = 1080 + 140 * p
            angle = 18 * math.sin((t - 8.0) * 2.2) * p
            bscale = 1 - 0.18 * p
        elif t < 12.75:  # SHAKE / SPRAY / STYLE
            by, bscale = 1220, 0.82
            angle = 0
            if t < 11.3:
                angle = 25 * math.sin((t - 10.6) * 30) * (1 - prog(t, 10.6, 0.7))
        else:  # end card
            p = ease_out(prog(t, 12.75, 0.7))
            by = 1220 - 180 * p
            bscale = 0.82 + 0.08 * p
            angle = 360 * (1 - p)
        bx = W / 2
        if 8.0 <= t < 10.6:
            bx = W / 2 - 230 * ease_in_out(prog(t, 8.0, 0.6))
        elif 10.6 <= t < 12.75:
            bx = W / 2 - 230 + 230 * ease_in_out(prog(t, 10.6, 0.4))
        img = BOTTLE.render(angle)
        # soft glow halo behind bottle
        halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        hr = 380 * bscale
        hd.ellipse((bx - hr, by - hr * 1.4, bx + hr, by + hr * 1.4), fill=(80, 110, 255, 70))
        c.alpha_composite(halo.filter(ImageFilter.GaussianBlur(120)))
        tilt = 0
        if 10.6 <= t < 11.3:
            tilt = 9 * math.sin((t - 10.6) * 34) * (1 - prog(t, 10.6, 0.7))
        paste(c, img, bx, by, bscale, 1.0, tilt)
        nx, ny = BOTTLE.nozzle(bx, by)
        ny = by - (img.height * bscale) / 2 + 95 * bscale
        mist(c, t, 7.45, nx, ny, dur=1.0, kill=8.0)
        mist(c, t, 11.3, nx, ny, dur=1.0)

    # S4 8-10.6: claims, left-aligned right of the bottle (bottle right edge ~ x 450)
    if 8.2 <= t < 10.7:
        out = 1 - prog(t, 10.45, 0.2)
        left = 500
        for i, (tx, col) in enumerate((("HIMALAYAN", WHITE), ("SEA SALT", ICE))):
            p = ease_out(prog(t, 8.25 + i * 0.18, 0.4))
            img = word(tx, "Anton-Regular", 130, col)
            paste(c, img, left + img.width / 2 + 160 * (1 - p), 560 + i * 150, 1.0, p * out)
        for i, tx in enumerate(("INSTANT VOLUME", "MATTE TEXTURE", "ZERO GREASE")):
            p = ease_out(prog(t, 8.9 + i * 0.28, 0.35))
            img = word(tx, "Montserrat-ExtraBold", 42, WHITE, 3)
            y = 900 + i * 86
            paste(c, img, left + 34 + img.width / 2 + 100 * (1 - p), y, 1.0, p * out)
            ImageDraw.Draw(c).rectangle((left, y - 7, left + 14, y + 7), fill=INDIGO + (int(255 * p * out),))

    # S5 10.6-12.75: SHAKE. SPRAY. STYLE.
    for i, wtxt in enumerate(("SHAKE.", "SPRAY.", "STYLE.")):
        t0 = 10.6 + i * 0.7
        if t0 <= t < t0 + 0.72:
            slam(c, word(wtxt, "Anton-Regular", 260, WHITE if i != 1 else ICE, glow_r=16 if i == 2 else 0), t, t0, W / 2, 400, hold=0.5)

    # S6 12.75-15: end card
    if t >= 12.75:
        p = ease_out(prog(t, 13.0, 0.5))
        paste(c, LOGO, W / 2, 250 + 30 * (1 - p), 1.0, p)
        p2 = ease_out(prog(t, 13.35, 0.45))
        paste(c, word("BORN IN HIMACHAL.", "Anton-Regular", 96, WHITE, 4), W / 2, 1640 + 30 * (1 - p2), 1.0, p2)
        p3 = ease_out(prog(t, 13.7, 0.45))
        pill = word("₹449  ·  SPRAYMAX.IN", "Montserrat-ExtraBold", 42, (10, 12, 40), 3)
        pw, ph = pill.width + 80, pill.height + 44
        bg = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2, fill=WHITE + (255,))
        bg.alpha_composite(pill, (40, 22))
        paste(c, bg, W / 2, 1780 + 20 * (1 - p3), 1.0, p3)

    # impact flashes on key beats
    for tb in (0.15, 7.45, 12.0):
        flash(c, 0.35 * (1 - prog(t, tb, 0.18)) if t >= tb else 0)
    return c.convert("RGB")


# ---------- audio ----------
def audio(path, sr=44100):
    n = int(sr * DUR)
    out = np.zeros(n)
    tt = np.arange(n) / sr

    def kick(t0, gain=0.9):
        i = int(t0 * sr)
        L = int(0.45 * sr)
        x = np.arange(L) / sr
        f = 50 + 110 * np.exp(-x * 30)
        s = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-x * 7) * gain
        out[i:i + L] += s[: n - i]

    def noise(t0, dur, gain, lp=0.15, rise=False):
        i, L = int(t0 * sr), int(dur * sr)
        x = np.linspace(0, 1, L)
        env = (x ** 2 if rise else np.exp(-x * 5)) * gain
        w = rng.standard_normal(L)
        for _ in range(3):  # crude low-pass
            w = np.convolve(w, np.ones(int(1 / lp)) / int(1 / lp), mode="same")
        out[i:i + L] += (w * env)[: n - i]

    drone = (np.sin(2 * np.pi * 55 * tt) * 0.06 + np.sin(2 * np.pi * 82.5 * tt) * 0.03)
    drone *= np.clip(tt / 1.5, 0, 1) * np.clip((DUR - tt) / 1.0, 0, 1)
    out += drone
    for t0 in (0.15, 0.75, 2.05, 2.47, 3.55, 3.97, 10.6, 11.3, 12.0):
        kick(t0, 0.8)
    for t0 in (2.75, 4.25):
        noise(t0, 0.18, 0.5, lp=0.5)
    noise(4.6, 0.6, 0.35, rise=True)  # whoosh into product
    noise(7.45, 1.2, 0.45, lp=0.6)  # spray hiss
    noise(11.3, 0.8, 0.4, lp=0.6)
    kick(12.75, 1.0)
    out = np.tanh(out * 1.4) * 0.7
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def main():
    global BG, BOTTLE, LOGO
    OUT.mkdir(parents=True, exist_ok=True)
    BG = make_bg()
    BOTTLE = Bottle()
    logo = Image.open(ASSETS / "logo-wide.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    white = Image.new("RGBA", logo.size, WHITE + (255,))
    white.putalpha(logo.getchannel("A"))
    LOGO = white.resize((640, int(640 * logo.height / logo.width)), Image.LANCZOS)

    if "--preview" in sys.argv:
        for ts in (0.6, 1.4, 2.9, 4.4, 6.2, 7.7, 9.6, 11.0, 11.8, 14.5):
            frame(ts).save(OUT / f"preview_{ts:05.2f}.jpg", quality=88)
        print("previews written to", OUT)
        return

    wav = OUT / "sfx.wav"
    audio(wav)
    mp4 = OUT / "spraymax-typo-15s.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{N}", flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", mp4)


if __name__ == "__main__":
    main()
