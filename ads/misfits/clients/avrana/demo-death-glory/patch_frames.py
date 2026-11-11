#!/usr/bin/env python3
"""Replace frames of a video with copies of other frames (same length, audio untouched).

Used on the Avrana platform shots, where the wearer stands still in front of a motion-blurred train: the frames
that still carried a trace of the print's glow are replaced with clean frames from the same shot, which is
invisible there. Frame numbers are 0-based and ranges inclusive; DST and SRC ranges must be the same length.

  python3 patch_frames.py <in.mp4> <out.mp4> --copy 34-41=26-33 --copy 47=48 [--crf 10]
"""
import argparse
import subprocess


def frame_count(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-count_packets", "-show_entries",
                          "stream=nb_read_packets", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return int(out.strip())


def rng(s):
    a, _, b = s.partition("-")
    return int(a), int(b or a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--copy", action="append", required=True, help="DST=SRC frame ranges, e.g. 34-41=26-33")
    ap.add_argument("--crf", type=int, default=10)
    args = ap.parse_args()
    n = frame_count(args.src)
    source = list(range(n))
    for spec in args.copy:
        (d0, d1), (s0, s1) = (rng(x) for x in spec.split("="))
        assert d1 - d0 == s1 - s0 and d1 < n and s1 < n, spec
        for k in range(d1 - d0 + 1):
            source[d0 + k] = s0 + k
    runs = []  # consecutive source runs -> trim segments
    for s in source:
        if runs and s == runs[-1][1] + 1:
            runs[-1][1] = s
        else:
            runs.append([s, s])
    fc = f"[0:v]split={len(runs)}" + "".join(f"[s{i}]" for i in range(len(runs))) + ";"
    fc += "".join(f"[s{i}]trim=start_frame={a}:end_frame={b + 1},setpts=PTS-STARTPTS[v{i}];"
                  for i, (a, b) in enumerate(runs))
    fc += "".join(f"[v{i}]" for i in range(len(runs))) + f"concat=n={len(runs)}:v=1:a=0[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.src, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                    "-c:v", "libx264", "-crf", str(args.crf), "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy",
                    args.out], check=True)
    print(f"Saved {args.out}: {n} frames, {sum(1 for i, s in enumerate(source) if i != s)} replaced, "
          f"{frame_count(args.out)} written")


if __name__ == "__main__":
    main()
