#!/usr/bin/env python3
"""Ultra Male spec edit (Narayan, 4 Nov: "Delete this shot" = the hand pressing the spray cap, take frames 208-221,
8.67-9.25 s). Optionally a new shot goes in its place: --insert <clip> --from <first frame> --len <frames>.
Works on the 720p take or its 4x upscale (same frames; the inserted clip must be the same size).

  python3 ads/jpg-spec/ultra-male-12s/edit_ultra_male.py <take.mp4> <out.mp4> [--insert storm.mp4 --from 0 --len 19]
"""
import subprocess
import sys

FPS = 24
CUT = (208, 222)             # the spray shot, end exclusive


def main():
    a = sys.argv[1:]
    take, dst = a[0], a[1]
    parts = [f"[0:v]trim=start_frame=0:end_frame={CUT[0]},setpts=PTS-STARTPTS,setsar=1[a]"]
    labels = "[a]"
    if "--insert" in a:
        clip = a[a.index("--insert") + 1]
        f0 = int(a[a.index("--from") + 1])
        n = int(a[a.index("--len") + 1])
        parts.append(f"[1:v]trim=start_frame={f0}:end_frame={f0 + n},setpts=PTS-STARTPTS,setsar=1[b]")
        labels += "[b]"
    parts.append(f"[0:v]trim=start_frame={CUT[1]},setpts=PTS-STARTPTS,setsar=1[c]")
    labels += "[c]"
    k = labels.count("[")
    parts.append(f"{labels}concat=n={k}:v=1:a=0,format=yuv420p[o]")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", take]
    if "--insert" in a:
        cmd += ["-i", clip]
    subprocess.run(cmd + ["-filter_complex", ";".join(parts), "-map", "[o]", "-c:v", "libx264", "-crf", "10", "-preset",
                          "slow", "-r", str(FPS), dst], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of",
                          "csv=p=0", dst], capture_output=True, text=True).stdout.strip()
    print(f"wrote {dst}: {out} frames")


if __name__ == "__main__":
    main()
