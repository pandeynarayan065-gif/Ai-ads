#!/usr/bin/env python3
"""Ad 2 (ocean) edit, v3: every shot we have, trimmed to its best moment, 12.0 s, visuals only.

History: v1 ended on the rocks shot slowed and frozen under the logo ("stupid, too long"); v2 dropped the rocks
shots ("why did you remove the dark rock shot? add all shots that we have"). v3 keeps all ten shots of the take plus
the seashore insert, each at real speed, cut to fit 12 s at the reference film's pace. No end card (for now).

  python3 ads/spraymax/cinematic-12s-ocean/edit_ad2.py <take.mp4> <seashore.mp4> <out.mp4>
"""
import subprocess
import sys

FPS = 24
# (input 0 = take, 1 = seashore insert, start s, end s); the take's cuts: 1.08 2.29 3.75 4.92 6.04 7.21 7.92 8.83 10.29
EDL = [
    (0, 0.10, 1.00),    # 1 cliff, man in silhouette
    (0, 1.10, 2.20),    # 2 the dive
    (0, 2.35, 3.65),    # 3 the plunge, seen from underwater
    (0, 3.85, 4.75),    # 4 sinking past the lens
    (0, 5.00, 5.90),    # 5 the shipwreck
    (0, 6.10, 7.00),    # 6 landing by the wreck
    (0, 7.21, 7.91),    # 7 the school of fish
    (0, 7.98, 8.78),    # 8 the wave on the rocks
    (0, 8.90, 10.00),   # 9 the dark rock shot: lying on its side as a wave washes over it
    (0, 10.40, 11.60),  # 10 standing on the rock at sunset
    (1, 0.60, 2.80),    # 11 the beach: foam rushing in round the bottle
]
TOTAL = 12.0


def main():
    take, shore, out = sys.argv[1:4]
    # frame-exact: round every in/out to a frame, then give the last shot whatever makes exactly TOTAL * FPS frames
    frames = [(src, round(s * FPS), round(b * FPS)) for src, s, b in EDL]
    short = round(TOTAL * FPS) - sum(b - s for _, s, b in frames)
    src, s0, b0 = frames[-1]
    frames[-1] = (src, s0, b0 + short)
    parts = []
    for k, (src, s, b) in enumerate(frames):
        parts.append(f"[{src}:v]trim=start_frame={s}:end_frame={b},setpts=PTS-STARTPTS,scale=720:1280,setsar=1[v{k}]")
    parts.append("".join(f"[v{k}]" for k in range(len(frames))) + f"concat=n={len(frames)}:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", take, "-i", shore, "-filter_complex", ";".join(parts),
                    "-map", "[o]", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), out], check=True)
    n = sum(b - s for _, s, b in frames)
    print(f"wrote {out}: {len(frames)} shots, {n} frames = {n / FPS:.3f} s")

if __name__ == "__main__":
    main()
