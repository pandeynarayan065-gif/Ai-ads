#!/usr/bin/env python3
"""Ad 2 (ocean) edit, v2: every shot at real speed, ending on the beach beauty shot and a short black end card.

v1 ended on the bottle washed up on its side on the rocks, slowed and frozen for ~2 s under the logo; Narayan:
"the end shot is stupid and lasts too long" (a bottle lying in the surf reads as litter, and a frozen frame drags).
v2: the take's first eight shots as cut (cliff, dive, plunge, sink, wreck, landing, fish, wave), then the seashore
insert (the bottle on the beach at sunset as the foam rushes in round it), then 1 s of black for the end card.

  python3 ads/spraymax/cinematic-12s-ocean/edit_ad2.py <take.mp4> <seashore.mp4> <out.mp4> [--no-card]
"""
import subprocess
import sys

FPS = 24
# from the take's cuts: 1.08 2.29 3.75 4.92 6.04 7.21 7.92 8.83 10.29
TAKE_CUT = [(0.00, 1.08), (1.08, 2.29), (2.29, 3.75), (3.75, 4.92), (4.92, 6.04), (6.04, 7.21), (7.21, 7.92),
            (7.92, 8.83)]
SHORE = (0.60, 2.77)                       # the foam washes in (~1.0 s) and draws back
CARD = 1.0                                 # black end card (with --no-card the beach shot runs on instead)
TOTAL = 12.0


def main():
    take, shore, out = sys.argv[1:4]
    global CARD, SHORE
    if "--no-card" in sys.argv:                            # Narayan, 3 Nov: no end card for now
        CARD = 0.0
        SHORE = (SHORE[0], SHORE[0] + TOTAL - sum(b - s for s, b in TAKE_CUT))
    used = sum(b - s for s, b in TAKE_CUT) + (SHORE[1] - SHORE[0])
    assert abs(used + CARD - TOTAL) < 0.02, used + CARD
    parts = [f"[0:v]trim=start={s}:end={b},setpts=PTS-STARTPTS,fps={FPS}[v{k}]" for k, (s, b) in enumerate(TAKE_CUT)]
    k = len(TAKE_CUT)
    parts.append(f"[1:v]trim=start={SHORE[0]}:end={SHORE[1]},setpts=PTS-STARTPTS,fps={FPS},scale=720:1280[v{k}]")
    n = k + 1
    if CARD > 0:
        parts.append(f"color=c=black:s=720x1280:r={FPS}:d={CARD}[v{k + 1}]")
        n = k + 2
    parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,trim=duration={TOTAL},format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", take, "-i", shore, "-filter_complex", ";".join(parts),
                    "-map", "[o]", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), out], check=True)
    print(f"wrote {out}: shots {used:.2f} s + end card {CARD:.2f} s")


if __name__ == "__main__":
    main()
