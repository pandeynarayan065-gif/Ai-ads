#!/usr/bin/env python3
"""Ad 2 (ocean) edit, v4: every shot we have, 12.0 s, visuals only; the wave crash moved between the two
standing-bottle shots, the beach capped at 1.2 s (Narayan, 3 Nov).

History: v1 ended on the rocks shot slowed and frozen under the logo ("stupid, too long"); v2 dropped the rocks
shots ("why did you remove the dark rock shot? add all shots that we have"). v3 keeps all ten shots of the take plus
the seashore insert, each at real speed, cut to fit 12 s at the reference film's pace. No end card (for now).

  python3 ads/spraymax/cinematic-12s-ocean/edit_ad2.py <take.mp4> <seashore.mp4> <out.mp4>

Masters (v4): this edit is takes/edit-v4-720.mp4; Topaz on kie failed, so it was upscaled locally, then finished per size:
  scripts/esrgan_upscale.py takes/edit-v4-720.mp4 esr.mp4 --weights realesr-general-x4v3.pth --size 2160x3840
  ads/spraymax/cinematic-12s/finish_film.py esr.mp4 fin.mp4 --no-card --size 1080x1920   (and 2160x3840)
  ffmpeg -i fin.mp4 -an -c:v copy -movflags +faststart spraymax-ocean-12s.mp4               (visuals only, no audio)
"""
import subprocess
import sys

FPS = 24
# (input 0 = take, 1 = seashore insert, start s, end s); the take's cuts: 1.08 2.29 3.75 4.92 6.04 7.21 7.92 8.83 10.29
EDL = [
    (0, 0.00, 1.08),    # 1 cliff, man in silhouette
    (0, 1.08, 2.29),    # 2 the dive
    (0, 2.29, 3.75),    # 3 the plunge, seen from underwater
    (0, 3.75, 4.92),    # 4 sinking past the lens
    (0, 4.95, 5.95),    # 5 the shipwreck
    (0, 6.10, 7.00),    # 6 landing by the wreck
    (0, 7.21, 7.91),    # 7 the school of fish
    (0, 8.83, 10.00),   # 8 the dark rock shot: lying on its side as a wave washes over it
    (0, 10.40, 11.60),  # 9 standing on the rock at sunset
    (0, 7.92, 8.83),    # 10 the wave exploding on the rocks (moved here to separate the two standing shots)
    (1, 0.85, 2.00),    # 11 the beach, 28 frames = 1.17 s (1.2 s max): foam rushing in round the bottle
]
ADJUST = 8              # frame rounding is absorbed by the standing shot (room on both sides), never by the beach
TOTAL = 12.0


def main():
    take, shore, out = sys.argv[1:4]
    # frame-exact: round every in/out to a frame, then give shot ADJUST whatever makes exactly TOTAL * FPS frames
    frames = [(src, round(s * FPS), round(b * FPS)) for src, s, b in EDL]
    short = round(TOTAL * FPS) - sum(b - s for _, s, b in frames)
    src, s0, b0 = frames[ADJUST]
    frames[ADJUST] = (src, s0, b0 + short)
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
