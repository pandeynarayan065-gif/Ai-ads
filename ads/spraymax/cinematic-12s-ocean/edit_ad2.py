#!/usr/bin/env python3
"""Ad 2 (ocean) edit: cut the Seedance take and the seashore insert into one 12.0 s film.

The take's own packshot stands the bottle upright on the rocks, and its wreck shot lands it upright in the sand;
Narayan wants the bottle lying naturally. So the wreck shot is trimmed to the landing and the sand puff, and the
film ends on the seashore insert (the bottle lying on wet sand as foam washes round it, the sun behind), which
carries the end card.

  python3 ads/spraymax/cinematic-12s-ocean/edit_ad2.py <take.mp4> <seashore.mp4> <out.mp4> [--insert-start 0.6]
"""
import subprocess
import sys

FPS = 24
# (source, start s, end s) from the take's cuts: 1.08 2.29 3.75 4.92 6.04 7.21 7.92 8.83 10.29
TAKE_CUT = [(0.00, 1.08), (1.08, 2.29), (2.29, 3.75), (3.75, 4.92), (4.92, 6.04),
            (6.04, 6.84),                 # bottle by the wreck: the landing and the sand puff only
            (7.21, 7.92), (7.92, 8.83),
            (8.83, 10.03)]                # washed up on the rocks
TOTAL = 12.0


def main():
    a = sys.argv[1:]
    take, shore, out = a[0], a[1], a[2]
    ins = float(a[a.index("--insert-start") + 1]) if "--insert-start" in a else 0.6
    used = sum(b - s for s, b in TAKE_CUT)
    tail = round(TOTAL - used, 3)
    parts, inputs = [], ["-i", take, "-i", shore]
    for k, (s, b) in enumerate(TAKE_CUT):
        parts.append(f"[0:v]trim=start={s}:end={b},setpts=PTS-STARTPTS,fps={FPS}[v{k}]")
    parts.append(f"[1:v]trim=start={ins}:end={ins + tail},setpts=PTS-STARTPTS,fps={FPS},scale=720:1280[v{len(TAKE_CUT)}]")
    n = len(TAKE_CUT) + 1
    parts.append("".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(parts), "-map", "[o]",
                    "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), out], check=True)
    print(f"wrote {out}: take {used:.2f} s + seashore {tail:.2f} s (from {ins:.2f} s); end card from {used:.2f} s")


if __name__ == "__main__":
    main()
