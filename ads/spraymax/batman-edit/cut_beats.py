#!/usr/bin/env python3
"""Beat-synced recreation of Narayan's 'why do we fall, sir?' edit (lv_0_20261120075217), carried on to "Never.".

Cuts sit on the score's beat grid (0.6847 s, first beat at 0.225 s; half and quarter beats for the flurries),
measured from the audio. Same shots and order as his edit, from the clean sources hf1/hf2, plus five keepers from hf3 (the fall-and-rise take).

  python3 cut_beats.py <dir with hf1.mp4 hf2.mp4 bat.mp4> <out.mp4> [--size 2160x3840]
"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, out = sys.argv[1], sys.argv[2]
size = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--size" else "1080x1920"
W, H = map(int, size.split("x"))
A0 = 9.965                                   # audio in point in bat.mp4: "Why do we fall, sir?"
B = lambda k: 0.225 + 0.6847 * k             # beat k
h = lambda k: B(k) + 0.6847 / 2              # half beat after beat k
q = lambda k, n: B(k) + 0.6847 * n / 4       # quarter beats
# (cut-in time on the edit timeline, source, source in-point); each shot runs to the next cut
CUTS = [
    (0.0,      "hf1", 0.00),   # silhouette facing us, floor light      "Why do we
    (B(1),     "hf3", 0.30),   # he falls backward                       fall, sir?"
    (B(2),     "hf1", 13.45),  # from behind, arms out                   flurry on half beats
    (h(2),     "hf1", 14.03),  # bottle macro
    (B(3),     "hf1", 16.16),  # silhouette in the light
    (h(3),     "hf1", 17.80),  # far, tiny silhouette
    (B(4),     "hf2", 2.60),   # cap macro
    (B(5),     "hf2", 8.09),   # sprays, from behind
    (B(6),     "hf1", 7.90),   # walking silhouette                     quarter-beat flurry
    (q(6, 1),  "hf2", 14.67),  # hair macro
    (q(6, 2),  "hf2", 17.55),  # bottle in smoke
    (q(6, 3),  "hf2", 18.55),  # face
    (B(7),     "hf3", 5.75),   # hand slaps the wet floor               "So that we can learn
    (B(8),     "hf1", 12.625), # from behind, arms out                  to pick ourselves up"
    (B(9),     "hf1", 11.28),  # bottle on the ledge, dust
    (B(10),    "hf2", 6.59),   # hands, bottle
    (h(10),    "hf2", 9.10),   # spray macro
    (B(11),    "hf2", 12.32),  # hair
    (h(11),    "hf2", 3.89),   # profile
    (B(13),    "hf3", 11.05),  # sea water hits him, he doesn't flinch
    (B(14),    "hf2", 18.40),  # looks into the lens                    "I just haven't given up on me"
    (B(16),    "hf3", 12.75),  # sweeps his hair back
    (B(17),    "hf1", 7.02),   # bottle in the splash
    (B(18),    "hf3", 15.45),  # gale on the coat, he stands unmoved
    (B(19),    "hf1", 9.75),   # sprays, backlit
    (B(20),    "hf2", 17.06),  # bottle in smoke
    (14.55,    "hf1", 19.04),  # hero: bottle + his silhouette          "Never."
]
END = 15.35
k = W / 1080
# caption PNG, same editorial serif as the mog intro
cap = Path(out).with_suffix(".caption.png")
FD = "/home/user/Ai-ads/brand/misfits/fonts/"
f = ImageFont.truetype(FD + "InstrumentSerif-Regular.ttf", round(96 * k))
txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
for i, line in enumerate(["why do we", "fall, sir?"]):
    d.text(((W - f.getlength(line)) / 2, round((700 + i * 98) * k)), line, font=f, fill=(255, 255, 255, 255))
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(txt.getchannel("A").filter(ImageFilter.GaussianBlur(10 * k)).point(lambda v: int(v * .55)))
c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c.alpha_composite(sh); c.alpha_composite(txt); c.save(cap)

ins = ["-i", f"{src}/hf1.mp4", "-i", f"{src}/hf2.mp4", "-i", f"{src}/hf3.mp4", "-ss", str(A0), "-t", str(END), "-i", f"{src}/bat.mp4",
       "-loop", "1", "-t", str(END), "-i", str(cap)]
ix = {"hf1": 0, "hf2": 1, "hf3": 2}
fc = []
F = lambda t: round(t * 24)               # frame-exact: every cut lands on the 24 fps grid, no drift
for i, (t, n, s) in enumerate(CUTS):
    nf = F(CUTS[i + 1][0] if i + 1 < len(CUTS) else END) - F(t)
    s0 = F(s)
    fc.append(f"[{ix[n]}:v]fps=24,trim=start_frame={s0}:end_frame={s0 + nf},setpts=PTS-STARTPTS,scale={W}:{H}:flags=lanczos,setsar=1[v{i}]")
fc.append("".join(f"[v{i}]" for i in range(len(CUTS))) + f"concat=n={len(CUTS)}:v=1:a=0,"
          "eq=contrast=1.06:saturation=0.9,colorbalance=bs=0.03:bm=0.01,unsharp=5:5:0.45,noise=alls=5:allf=t[base]")
fc.append("[4:v]format=rgba,fade=t=in:st=0.15:d=0.25:alpha=1,fade=t=out:st=1.3:d=0.25:alpha=1[cap]")
fc.append("[base][cap]overlay=0:0:shortest=1,format=yuv420p[v]")
fc.append(f"[3:a]atrim=0:{END},asetpts=PTS-STARTPTS,afade=t=in:d=0.08,afade=t=out:st={END-0.35}:d=0.35,loudnorm=I=-14:TP=-1.5[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-maxrate", "40M", "-bufsize", "80M",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out], check=True)
print(f"Saved {out}: {END} s, {len(CUTS)} shots, {size}")
for t, n, s in CUTS: print(f"  {t:6.3f}  {n} {s}")
