#!/usr/bin/env python3
"""Samsung spec edit v2: the iPhone Duo opener in front of the v1 edit (Narayan, 4 Nov: "create the clip before shot 1
showing the iphone fold duo").

The opener (takes/20261104-203734-1.mp4) is clean for frames 0-64: the iPhone Duo reveal pushing in to its Apple logo.
From frame ~66 its Fold8 "reflection" fades in as a flat copy of the reference photo, so it is cut there, and the film
hard-cuts into v1's own shot 1 (the chrome logo macro, whose reflection reads as real). 65 + 289 = 354 frames, 14.75 s.
Works at 720p or on 4x upscales of both (same frames).

  python3 ads/samsung-spec/fold8-ultra-12s/add_opener.py <opener.mp4> <edit-v1.mp4> <out.mp4>
"""
import subprocess
import sys

FPS = 24
OPENER = (0, 65)             # opener frames kept, end exclusive; the HUD runs with --offset 65


def main():
    opener, edit, dst = sys.argv[1:4]
    fc = (f"[0:v]trim=start_frame={OPENER[0]}:end_frame={OPENER[1]},setpts=PTS-STARTPTS,setsar=1[a];"
          "[1:v]setpts=PTS-STARTPTS,setsar=1[b];[a][b]concat=n=2:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", opener, "-i", edit, "-filter_complex", fc, "-map", "[o]",
                    "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), dst], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of",
                          "csv=p=0", dst], capture_output=True, text=True).stdout.strip()
    print(f"wrote {dst}: {out} frames")


if __name__ == "__main__":
    main()
