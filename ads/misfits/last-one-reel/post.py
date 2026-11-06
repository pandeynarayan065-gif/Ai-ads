"""Post for "The last one doesn't fit": sound design + text overlays + final encode.
Usage: python3 post.py <render_dir>   (render_dir has frames/ and timing.json from scene.py)
Writes mix.wav, overlays/*.png and misfits-last-one.mp4 next to this script. No voiceover on purpose."""
import json, os, subprocess, sys, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); RD = sys.argv[1]
tm = json.load(open(os.path.join(RD, "timing.json")))
SR, DUR, LANDS, TM = 48000, tm["dur"], tm["lands"], tm["misfit"]
n = int(SR * DUR); t = np.arange(n) / SR; rng = np.random.default_rng(3)
out = np.zeros(n)

def place(sig, at, g=1.0):
    i = int(at * SR); j = min(n, i + len(sig))
    if i < n: out[i:j] += g * sig[: j - i]
def lp(x, a):
    y = np.empty_like(x); acc = 0.0
    for k, v in enumerate(x): acc += a * (v - acc); y[k] = acc
    return y
def tock(f, dec=0.06, click=0.5, L=0.25):
    x = np.arange(int(L * SR)) / SR
    body = np.sin(2 * np.pi * f * x) * np.exp(-x / dec) + 0.5 * np.sin(2 * np.pi * f * 2.03 * x) * np.exp(-x / (dec * 0.5))
    return body + click * rng.standard_normal(len(x)) * np.exp(-x / 0.0025)

# room tone: quiet low rumble + soft air
out += 0.012 * lp(rng.standard_normal(n), 0.004) * 6 + 0.02 * np.sin(2 * np.pi * 41 * t) * np.clip(t / 1.5, 0, 1)
# each grey tile seating: a tock that climbs in pitch as the rhythm speeds up (satisfying)
for k, at in enumerate(LANDS):
    f = 190 * (1.045 ** k)
    place(tock(f), at, 0.5)
    place(tock(f * 1.5, dec=0.02, click=0.2, L=0.08), at + 0.07, 0.12)     # tiny settle bounce
# tension: everything drops out, a thin riser into the misfit
x = np.arange(int((TM - LANDS[-1]) * SR)) / SR
rise = lp(rng.standard_normal(len(x)), 0.05) * (x / x[-1]) ** 2.5 + 0.25 * np.sin(2 * np.pi * (300 + 900 * (x / x[-1]) ** 2) * x) * (x / x[-1]) ** 3
place(rise, LANDS[-1] + 0.12, 0.22)
# misfit lands: heavy thunk, two bounces, then a lime "hum" chord that holds
L = int(1.6 * SR); x = np.arange(L) / SR
thunk = np.sin(2 * np.pi * (48 + 70 * np.exp(-x / 0.04)) * x) * np.exp(-x / 0.45) + 0.6 * rng.standard_normal(L) * np.exp(-x / 0.006)
place(thunk, TM, 0.9)
place(tock(260, dec=0.05, click=0.35), TM + 0.24, 0.35); place(tock(300, dec=0.04, click=0.2), TM + 0.40, 0.2)
hold = np.arange(int((DUR - TM) * SR)) / SR
hum = sum(np.sin(2 * np.pi * f * hold) * g for f, g in [(110, 1), (164.8, .6), (220, .35), (329.6, .15)])
hum *= np.minimum(hold / 0.25, 1) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * hold)) * np.clip((DUR - TM - hold) / 0.8, 0, 1)
place(hum, TM, 0.07)
for k, f in enumerate([880, 1318.5, 1760]):
    place(np.sin(2 * np.pi * f * hold[: int(1.8 * SR)]) * np.exp(-hold[: int(1.8 * SR)] / 0.5), TM + 0.02 + k * 0.04, 0.035)
out *= 0.89 / np.max(np.abs(out))
st = np.stack([out, out], 1); st[:, 0] += 0.015 * np.roll(out, 300); st[:, 1] -= 0.015 * np.roll(out, 300)
sf.write(os.path.join(HERE, "mix.wav"), st, SR)

# ---- overlays (HTML -> transparent PNG) ----
OV = os.path.join(HERE, "overlays"); os.makedirs(OV, exist_ok=True)
fonts = os.path.join(HERE, "../../../brand/misfits/fonts")
html = f"""<!doctype html><html><head><meta charset=utf-8><style>
@font-face{{font-family:A;src:url({fonts}/Archivo-VF.ttf);font-weight:100 900;font-stretch:62% 125%}}
@font-face{{font-family:S;src:url({fonts}/InstrumentSerif-Italic.ttf);font-style:italic}}
@font-face{{font-family:M;src:url({fonts}/JetBrainsMono-Bold.ttf);font-weight:700}}
html,body{{margin:0;width:1080px;height:1920px;background:transparent}}
.c{{position:absolute;left:0;right:0;text-align:center;color:#ecede8}}
.sf{{font-family:S;font-style:italic;font-size:118px;line-height:1;text-shadow:0 6px 30px #000}}
.ar{{font-family:A;font-stretch:125%;font-weight:900;font-size:104px;letter-spacing:-3px;line-height:1;
  background:linear-gradient(180deg,#fff 20%,#c9cbc4);-webkit-background-clip:text;background-clip:text;color:transparent}}
.fit{{background:linear-gradient(180deg,#c6ff5e,#8bd346 70%);-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 0 24px #8bd346aa) drop-shadow(0 0 60px #8bd34666)}}
.m{{font-family:M;font-weight:700;font-size:32px;letter-spacing:4px;color:#8b9099}}
.i{{display:inline-block;transform:rotate(-14deg) translateY(4px)}}
</style></head><body></body></html>"""
parts = {
 "hook": '<div class="c" style="top:250px"><div class="m">● WATCH CLOSELY</div><div class="sf" style="margin-top:26px">wait for the</div><div class="ar" style="margin-top:8px">LAST ONE.</div></div>',
 "end": '<div class="c" style="top:240px"><div class="ar">ADS THAT</div><div class="sf fit" style="font-size:150px;margin-top:4px">don’t fit in.</div></div>'
        '<div class="c" style="top:1500px"><div class="ar" style="font-size:64px;letter-spacing:-1px">MISF<span class="i fit">I</span>TS</div>'
        '<div class="m" style="margin-top:22px;color:#c9cbc4">COMMENT “FILM” · MISFITSAGENCY.IN</div></div>',
}
for k, v in parts.items():
    open(os.path.join(OV, k + ".html"), "w").write(html.replace("<body></body>", "<body>" + v + "</body>"))
js = "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});" + \
     "".join(f"await p.goto('file://{os.path.join(OV, k + '.html')}');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);" \
             f"await p.screenshot({{path:{json.dumps(os.path.join(OV, k + '.png'))},omitBackground:true}});" for k in parts) + "await b.close();})();"
open(os.path.join(OV, "make.js"), "w").write(js)
subprocess.run(["node", os.path.join(OV, "make.js")], check=True)

# ---- encode: upscale frames, fade overlays in/out, add sound ----
h0, h1 = 0.0, TM - 0.25              # hook on screen until just before the misfit lands
e0 = TM + 0.55                        # end card
vf = (f"[0:v]scale=1080:1920:flags=lanczos,format=rgba[v];"
      f"[1:v]format=rgba,fade=t=out:st={h1:.2f}:d=0.25:alpha=1[h];"
      f"[2:v]format=rgba,fade=t=in:st={e0:.2f}:d=0.4:alpha=1[e];"
      f"[v][h]overlay=0:0:shortest=1[vh];[vh][e]overlay=0:0:shortest=1,format=yuv420p[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(tm["fps"]), "-i", os.path.join(RD, "frames", "%04d.png"),
    "-loop", "1", "-framerate", str(tm["fps"]), "-i", os.path.join(OV, "hook.png"),
    "-loop", "1", "-framerate", str(tm["fps"]), "-i", os.path.join(OV, "end.png"),
    "-i", os.path.join(HERE, "mix.wav"), "-filter_complex", vf, "-map", "[out]", "-map", "3:a",
    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart", os.path.join(HERE, "misfits-last-one.mp4")], check=True)
print("done")
