#!/usr/bin/env python3
"""Samsung spec edit: take 1 with its chip shot replaced (Narayan, 4 Nov: "Remake shot").

Take 1's chip shot (frames 159-176, 6.62-7.38 s) carried fake text on the chip lid. It is replaced, frame for frame, by
the best 18 frames of the remake (takes/20261104-195802-1.mp4: from a blank-lid first frame), where the light line crosses
the lid. Everything else plays unchanged: 289 frames, 12.04 s. Works at 720p or on 4x upscales of both (same frames).

  python3 ads/samsung-spec/fold8-ultra-12s/edit_samsung.py <take.mp4> <remake.mp4> <out.mp4>
"""
import subprocess
import sys

FPS = 24
CHIP = (159, 177)            # take 1 frames to replace
REMAKE_FROM = 36             # remake frames 36-53 (1.50-2.21 s): the light line sweeping across the blank lid


def main():
    take, remake, dst = sys.argv[1:4]
    n = CHIP[1] - CHIP[0]
    fc = (f"[0:v]trim=start_frame=0:end_frame={CHIP[0]},setpts=PTS-STARTPTS[a];"
          f"[1:v]trim=start_frame={REMAKE_FROM}:end_frame={REMAKE_FROM + n},setpts=PTS-STARTPTS,scale=iw:ih,setsar=1[b];"
          f"[0:v]trim=start_frame={CHIP[1]},setpts=PTS-STARTPTS[c];"
          "[a][b][c]concat=n=3:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", take, "-i", remake, "-filter_complex", fc, "-map", "[o]",
                    "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), dst], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of",
                          "csv=p=0", dst], capture_output=True, text=True).stdout.strip()
    print(f"wrote {dst}: {out} frames")


if __name__ == "__main__":
    main()
