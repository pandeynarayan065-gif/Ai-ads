#!/usr/bin/env python3
"""Ad 2 (ocean) edit: cut the Seedance take and the seashore insert into one 12.0 s film.

The take's own packshot stands the bottle upright on the rocks, and its wreck shot lands it upright in the sand;
Narayan wants the bottle lying naturally. The seashore insert came back upright too, so it isn't used. The wreck
shot is trimmed to the landing and the sand puff, and the film ends on the take's washed-up shot (the bottle lying
on its side on wet rock as a wave foams over it), slowed to 0.8x, then held on its last frame for the end card.

  python3 ads/spraymax/cinematic-12s-ocean/edit_ad2.py <take.mp4> <out.mp4>
"""
import subprocess
import sys

FPS = 24
# (source, start s, end s) from the take's cuts: 1.08 2.29 3.75 4.92 6.04 7.21 7.92 8.83 10.29
TAKE_CUT = [(0.00, 1.08), (1.08, 2.29), (2.29, 3.75), (3.75, 4.92), (4.92, 6.04),
            (6.04, 6.84),                 # bottle by the wreck: the landing and the sand puff only
            (7.21, 7.92), (7.92, 8.83)]
ENDING = (8.83, 10.29)                    # washed up on the rocks, lying on its side
SLOW = 0.8
TOTAL = 12.0


def main():
    a = sys.argv[1:]
    take, out = a[0], a[1]
    used = sum(b - s for s, b in TAKE_CUT)
    s0, s1 = ENDING
    slow_len = (s1 - s0) / SLOW
    hold = round(TOTAL - used - slow_len, 3)
    parts = [f"[0:v]trim=start={s}:end={b},setpts=PTS-STARTPTS,fps={FPS}[v{k}]" for k, (s, b) in enumerate(TAKE_CUT)]
    k = len(TAKE_CUT)
    parts.append(f"[0:v]trim=start={s0}:end={s1},setpts=(PTS-STARTPTS)/{SLOW},"
                 f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,tpad=stop_mode=clone:stop_duration={hold}[v{k}]")
    n = k + 1
    parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,trim=duration={TOTAL},format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", take, "-filter_complex", ";".join(parts), "-map", "[o]",
                    "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), out], check=True)
    print(f"wrote {out}: {used:.2f} s of shots, ending {slow_len:.2f} s slowed + {hold:.2f} s hold (from {used:.2f} s)")

if __name__ == "__main__":
    main()
