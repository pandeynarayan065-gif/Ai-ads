#!/usr/bin/env python3
"""Ultra Male spec edit, frame-exact, from the take and two inserts (Narayan, 4-5 Nov).

- v2: the spray shot (take frames 208-221) replaced by the storm shot's lightning strike (storm frames 46-65).
- v3 (default): v2 plus the lavender gust (lavender frames 26-49) between the studio half and the sea half, right after
  the side silhouette (take frame 139): 295 + 24 = 319 frames, 13.29 s. --no-lavender builds v2.
Works on the 720p take and inserts, or on their 4x upscales (all inputs the same size).

  python3 ads/jpg-spec/ultra-male-12s/edit_ultra_male.py <take> <storm> <lavender> <out.mp4> [--no-lavender]

Upscaled inserts that start at the kept frame: pass --storm-from 0 --lavender-from 0.
"""
import subprocess
import sys

FPS = 24
SILHOUETTE_END = 139         # first frame of the deck shot
SPRAY = (208, 222)           # the spray shot, cut
STORM = (46, 20)             # (first frame, length) in the storm take
LAVENDER = (26, 24)          # (first frame, length) in the lavender take


def main():
    a = sys.argv[1:]
    take, storm, lav, dst = a[:4]
    s0 = int(a[a.index("--storm-from") + 1]) if "--storm-from" in a else STORM[0]
    l0 = int(a[a.index("--lavender-from") + 1]) if "--lavender-from" in a else LAVENDER[0]
    edl = [(0, 0, SILHOUETTE_END)]
    if "--no-lavender" not in a:
        edl.append((2, l0, l0 + LAVENDER[1]))
    edl += [(0, SILHOUETTE_END, SPRAY[0]), (1, s0, s0 + STORM[1]), (0, SPRAY[1], None)]
    parts, labels = [], ""
    for k, (src, f0, f1) in enumerate(edl):
        end = f":end_frame={f1}" if f1 is not None else ""
        parts.append(f"[{src}:v]trim=start_frame={f0}{end},setpts=PTS-STARTPTS,setsar=1[s{k}]")
        labels += f"[s{k}]"
    parts.append(f"{labels}concat=n={len(edl)}:v=1:a=0,format=yuv420p[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", take, "-i", storm, "-i", lav, "-filter_complex",
                    ";".join(parts), "-map", "[o]", "-c:v", "libx264", "-crf", "10", "-preset", "slow", "-r", str(FPS),
                    dst], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of",
                          "csv=p=0", dst], capture_output=True, text=True).stdout.strip()
    print(f"wrote {dst}: {out} frames")


if __name__ == "__main__":
    main()
