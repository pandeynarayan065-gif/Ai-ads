#!/usr/bin/env python3
"""Red Bull spec edit: the cleaned take minus the cliff dive (Narayan, 4 Nov: "Remove this shot from redbull").

The take's cuts (frames at 24 fps): 36 64 89 107 122 143 156 170 185 205 228 257. The cliff dive is frames 185-204
(7.71-8.54 s). Everything else plays in real time, unchanged: 289 - 20 = 269 frames, 11.21 s.
Works on the 720p take or its 4K upscale (frame numbers are the same).

  python3 ads/redbull-spec/cinematic-12s/edit_redbull.py <in.mp4> <out.mp4>
"""
import subprocess
import sys

FPS = 24
KEEP = [(0, 185), (205, 289)]        # (start frame, end frame), end exclusive


def main():
    src, dst = sys.argv[1:3]
    parts = [f"[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[v{k}]" for k, (a, b) in enumerate(KEEP)]
    parts.append("".join(f"[v{k}]" for k in range(len(KEEP))) + f"concat=n={len(KEEP)}:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-filter_complex", ";".join(parts), "-map", "[o]",
                    "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS), dst], check=True)
    n = sum(b - a for a, b in KEEP)
    print(f"wrote {dst}: {n} frames = {n / FPS:.2f} s")


if __name__ == "__main__":
    main()
