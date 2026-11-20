#!/usr/bin/env python3
"""Spraymax cinematic edit on the 'Why do we fall' audio, using only the shots from the K2 edit (taken from the
clean Higgsfield sources hf1/hf2, not the re-encoded edit).

  python3 cut.py <dir with hf1.mp4 hf2.mp4 bat.mp4> <out.mp4> [--size 1080x1920]
"""
import subprocess, sys
src, out = sys.argv[1], sys.argv[2]
size = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--size" else "1080x1920"
W, H = size.split("x")
A0, A1 = 9.6, 24.9          # the audio: "Why do we fall?" ... "Never."
# (source, start in source, duration) in edit order; total 15.28 s
SHOTS = [
    ("hf1", 12.64, 1.30),  # silhouette from behind          "Why do we fall?"
    ("hf1", 15.58, 1.10),  # silhouette, light and spray behind
    ("hf2", 3.92, 0.90),   # profile, eyes down
    ("hf2", 14.46, 0.70),  # hair macro
    ("hf2", 8.06, 0.74),   # sprays his hair, from behind
    ("hf2", 9.04, 0.66),   # spray macro                       "So that we can"
    ("hf2", 10.50, 1.00),  # hair toss                         "learn to pick"
    ("hf2", 15.80, 1.10),  # stands, bottle in hand            "ourselves up"
    ("hf1", 7.04, 0.70),   # bottle in the splash
    ("hf1", 14.04, 0.70),  # bottle macro
    ("hf2", 5.75, 0.70),   # hands, bottle
    ("hf1", 11.08, 0.60),  # bottle on the ledge, dust
    ("hf2", 18.42, 1.63),  # looks into the lens               "I just haven't given up on me"
    ("hf1", 9.75, 1.13),   # sprays, backlit
    ("hf2", 17.06, 1.30),  # bottle in smoke
    ("hf1", 19.02, 1.00),  # bottle + his silhouette, hero     "Never."
]
T = round(sum(d for _, _, d in SHOTS), 3)
inputs, parts = [], []
idx = {}
for name in ("hf1", "hf2"):
    idx[name] = len(inputs) // 2; inputs += ["-i", f"{src}/{name}.mp4"]
inputs += ["-ss", str(A0), "-t", str(T), "-i", f"{src}/bat.mp4"]
fc = []
for i, (n, s, d) in enumerate(SHOTS):
    fc.append(f"[{idx[n]}:v]trim=start={s}:duration={d},setpts=PTS-STARTPTS,fps=24,scale={W}:{H}:flags=lanczos,setsar=1[v{i}]")
fc.append("".join(f"[v{i}]" for i in range(len(SHOTS))) + f"concat=n={len(SHOTS)}:v=1:a=0,"
          "eq=contrast=1.06:saturation=0.9,colorbalance=bs=0.03:bm=0.01,unsharp=5:5:0.45,noise=alls=5:allf=t,format=yuv420p[v]")
fc.append(f"[2:a]atrim=0:{T},asetpts=PTS-STARTPTS,afade=t=in:d=0.12,afade=t=out:st={T-0.35}:d=0.35,loudnorm=I=-14:TP=-1.5[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-maxrate", "60M", "-bufsize", "120M",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out], check=True)
print(f"Saved {out}: {T} s, {len(SHOTS)} shots, {size}")
