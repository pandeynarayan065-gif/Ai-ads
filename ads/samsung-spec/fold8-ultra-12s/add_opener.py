#!/usr/bin/env python3
"""Samsung spec edit v2: the iPhone Duo opener in front of the v1 edit (Narayan, 4 Nov: "create the clip before shot 1
showing the iphone fold duo").

The opener (takes/20261104-203734-1.mp4) is clean for frames 0-64: the iPhone Duo reveal pushing in to its Apple logo. Narayan cut it to 2.6 s (62 frames).
From frame ~66 its Fold8 "reflection" fades in as a flat copy of the reference photo, so it is cut there, and the film
hard-cuts into v1's own shot 1 (the chrome logo macro, whose reflection reads as real). 62 + 289 = 351 frames, 14.63 s.
Works at 720p or on 4x upscales of both (same frames).

v3 tried dropping v1's shot 1 (the black-chrome logo) so the opener cut straight to the Fold8 reveal; Narayan: "Bring
back old chrome logo shot everything else is good". So v4 = v2's cut (opener, then v1 whole: 351 frames, 14.63 s; HUD
--offset 62) with v3's clean supers. --drop-logo-shot rebuilds v3 (313 frames; HUD --offset 24).

  python3 ads/samsung-spec/fold8-ultra-12s/add_opener.py <opener.mp4> <edit-v1.mp4> <out.mp4> [--drop-logo-shot]
"""
import subprocess
import sys

FPS = 24
V1_SHOT2 = 38                # v1's first frame after its logo shot
OPENER = (0, 62)             # opener frames kept (2.58 s), end exclusive; the HUD runs with --offset 62


def main():
    opener, edit, dst = sys.argv[1:4]
    v1_from = V1_SHOT2 if "--drop-logo-shot" in sys.argv else 0
    fc = (f"[0:v]trim=start_frame={OPENER[0]}:end_frame={OPENER[1]},setpts=PTS-STARTPTS,setsar=1[a];"
          f"[1:v]trim=start_frame={v1_from},setpts=PTS-STARTPTS,setsar=1[b];[a][b]concat=n=2:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", opener, "-i", edit, "-filter_complex", fc, "-map", "[o]",
                    "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), dst], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of",
                          "csv=p=0", dst], capture_output=True, text=True).stdout.strip()
    print(f"wrote {dst}: {out} frames")


if __name__ == "__main__":
    main()
