"""Sound design + voiceover mix for the Misfits launch reel (all generated here, no licensed audio).
Clock ticks (the 'attention test'), low drone, riser into the misfit moment, impacts, logo hit, CTA pop.
Usage: python3 mix.py  -> mix.wav (48 kHz stereo)"""
import json, numpy as np, soundfile as sf
SR, DUR = 48000, 18.6
n = int(SR * DUR); t = np.arange(n) / SR
rng = np.random.default_rng(7)
mus = np.zeros(n)

def env(a, d, length):
    x = np.arange(int(length * SR)) / SR
    return np.minimum(x / max(a, 1e-4), 1) * np.exp(-x / d)

def place(buf, sig, at, gain=1.0):
    i = int(at * SR); j = min(n, i + len(sig)); buf[i:j] += gain * sig[: j - i]

def lowpass(x, a):  # one-pole
    y = np.empty_like(x); acc = 0.0
    for k, v in enumerate(x): acc += a * (v - acc); y[k] = acc
    return y

# drone: A1 + E2 + A2, slow breathing, swells at the misfit and the logo
drone = sum(np.sin(2 * np.pi * f * t + p) * g for f, p, g in [(55, 0, 1), (82.4, 1, .5), (110, 2, .3), (164.8, 0.5, .12)])
shape = 0.35 + 0.15 * np.sin(2 * np.pi * 0.11 * t)
shape += 0.5 * np.clip((t - 5.0) / 1.5, 0, 1) * np.clip((13.0 - t) / 2.0, 0, 1)
shape *= np.clip(t / 1.2, 0, 1) * np.clip((DUR - t) / 1.5, 0, 1)
mus += 0.10 * drone * shape

# clock ticks every second until the logo lands
for s in range(0, 13):
    L = int(0.05 * SR); x = np.arange(L) / SR
    f = 2600 if s % 2 else 2000
    tick = np.sin(2 * np.pi * f * x) * np.exp(-x / 0.006) + 0.4 * rng.standard_normal(L) * np.exp(-x / 0.002)
    place(mus, tick, s + 0.0, 0.10 if s < 5 else 0.14)

# riser into 5.6 s
L = int(1.1 * SR); x = np.arange(L) / SR
noise = lowpass(rng.standard_normal(L), 0.08)
riser = noise * (x / x[-1]) ** 2 + 0.3 * np.sin(2 * np.pi * (200 + 900 * (x / x[-1]) ** 2) * x) * (x / x[-1]) ** 3
place(mus, riser, 4.5, 0.35)

def impact(at, g, f0=55):
    L = int(1.2 * SR); x = np.arange(L) / SR
    sub = np.sin(2 * np.pi * (f0 + 60 * np.exp(-x / 0.05)) * x) * np.exp(-x / 0.35)
    click = rng.standard_normal(L) * np.exp(-x / 0.004)
    place(mus, sub + 0.3 * click, at, g)

impact(5.6, 0.55)
# whoosh as the feed falls away
L = int(1.6 * SR); x = np.arange(L) / SR
wh = lowpass(rng.standard_normal(L), 0.03) * np.sin(np.pi * x / x[-1]) ** 2
place(mus, wh, 6.8, 0.9)
# product reveal shimmer
for k, f in enumerate([880, 1320, 1760]):
    place(mus, np.sin(2 * np.pi * f * np.arange(int(1.5 * SR)) / SR) * env(0.01, 0.4, 1.5), 10.55 + k * 0.05, 0.05)
# logo: three soft lands then a hit
for k in range(3):
    impact(13.6 + k * 0.12, 0.18, 90)
impact(13.95, 0.6, 45)
# CTA pop
L = int(0.15 * SR); x = np.arange(L) / SR
place(mus, np.sin(2 * np.pi * (500 + 900 * x / x[-1]) * x) * np.exp(-x / 0.04), 15.6, 0.25)

# voiceover
lines = json.load(open("vo/lines.json")); starts = [0.3, 2.7, 5.6, 8.0, 10.6, 13.4, 15.6]
vo = np.zeros(n); duck = np.zeros(n)
for i, (ln, st) in enumerate(zip(lines, starts)):
    a, sr = sf.read(f"vo/line{i}.wav")
    a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a)  # resample 24k -> 48k
    place(vo, a, st, 1.0)
    i0, i1 = int(st * SR), min(n, int((st + len(a) / SR) * SR)); duck[i0:i1] = 1
duck = lowpass(duck, 0.0008)
mix = mus * (1 - 0.45 * duck) + vo * 1.15
mix /= np.max(np.abs(mix)) / 0.89
st = np.stack([mix, mix], 1)
# slight stereo width on the music only
st[:, 0] += 0.02 * np.roll(mus, 240); st[:, 1] -= 0.02 * np.roll(mus, 240)
sf.write("mix.wav", st, SR); print("ok", st.shape)
