#!/usr/bin/env python3
"""Ad 2 (ocean) with a hero end card (Narayan, 3 Nov: "Make a hero end card for the ocean ... use one of the existing
clips"). No new generation.

The hero is the take's last shot, the bottle standing on the wet rock with the sun on the horizon and open sky above
it (take frames 247-288, 1.75 s, real time: no slow-down or freeze, after "the endshot is stupid and lasts too long").
It was shot 9 of the v4 edit, so it moves to the end rather than playing twice; the wave crash now sits between
the beach and the hero, so the two standing-bottle shots stay apart. Every shot is kept.

Built at 4K from the Real-ESRGAN upscales (v4 edit, frame-exact; the hero shot upscaled on its own):
  v4[0:209] shots 1-8 | v4[260:288] beach | v4[238:260] wave crash | hero[0:42]   = 301 frames, 12.54 s

  python3 ads/spraymax/cinematic-12s-ocean/edit_ad2_endcard.py <v4_4k.mp4> <hero_4k.mp4> <out_4k.mp4>
then (white logo + BORN IN HIMACHAL over the sky, soft top scrim, fading in 0.2 s into the hero):
  python3 ads/spraymax/cinematic-12s/finish_film.py out_4k.mp4 fin.mp4 --card 320,160,440,0.55 --card-at 11.0 \\
      --fade 0.45 --size 1080x1920            (and --size 2160x3840)
  ffmpeg -i fin.mp4 -an -c:v copy -movflags +faststart spraymax-ocean-12s-endcard.mp4      (visuals only)
"""
import subprocess
import sys

FPS = 24
PARTS = [(0, 0, 209), (0, 260, 288), (0, 238, 260), (1, 0, 42)]   # (input, start frame, end frame)


def main():
    v4, hero, out = sys.argv[1:4]
    f = []
    for k, (src, s, e) in enumerate(PARTS):
        f.append(f"[{src}:v]trim=start_frame={s}:end_frame={e},setpts=PTS-STARTPTS,setsar=1[v{k}]")
    f.append("".join(f"[v{k}]" for k in range(len(PARTS))) + f"concat=n={len(PARTS)}:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", v4, "-i", hero, "-filter_complex", ";".join(f),
                    "-map", "[o]", "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-r", str(FPS), out], check=True)
    n = sum(e - s for _, s, e in PARTS)
    print(f"wrote {out}: {n} frames = {n / FPS:.3f} s; hero from {(n - 42) / FPS:.3f} s")


if __name__ == "__main__":
    main()
