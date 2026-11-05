#!/usr/bin/env python3
"""Ultra Male spec edit, frame-exact, from the take and its inserts (Narayan, 4-5 Nov).

Versions (take frames at 24 fps; the spray shot is take frames 208-221, the side silhouette ends at frame 139):
- v2: spray shot -> the storm shot's lightning strike (storm frames 46-65). 295 frames.
- v3: v2 plus the lavender gust (lavender frames 26-49) after the side silhouette. 319 frames.
- v4 (default, "Replace the lavender shot with the lightning shot" / "Remove lightning"): spray shot -> the lavender
  gust; no lightning, nothing after the silhouette. 289 - 14 + 24 = 299 frames, 12.46 s.
Works on the 720p sources or their 4x upscales (all inputs the same size).

  python3 ads/jpg-spec/ultra-male-12s/edit_ultra_male.py <take> <out.mp4> --lavender <clip> [--storm <clip>]
      [--version v4|v3|v2] [--lavender-from 26] [--storm-from 46]

Upscaled inserts that start at the kept frame: pass --lavender-from 0 / --storm-from 0.
"""
import subprocess
import sys

FPS = 24
SILHOUETTE_END = 139         # first frame of the deck shot
SPRAY = (208, 222)           # the spray shot, cut
STORM_LEN, LAV_LEN = 20, 24


def opt(a, name, default=None):
    return a[a.index(name) + 1] if name in a else default


def main():
    a = sys.argv[1:]
    take, dst = a[0], a[1]
    ver = opt(a, "--version", "v4")
    srcs = [take]
    lav = storm = None
    if opt(a, "--lavender"):
        srcs.append(opt(a, "--lavender")); lav = len(srcs) - 1
    if opt(a, "--storm"):
        srcs.append(opt(a, "--storm")); storm = len(srcs) - 1
    l0, s0 = int(opt(a, "--lavender-from", 26)), int(opt(a, "--storm-from", 46))
    L = (lav, l0, l0 + LAV_LEN)
    S = (storm, s0, s0 + STORM_LEN)
    if ver == "v4":
        edl = [(0, 0, SPRAY[0]), L, (0, SPRAY[1], None)]
    elif ver == "v3":
        edl = [(0, 0, SILHOUETTE_END), L, (0, SILHOUETTE_END, SPRAY[0]), S, (0, SPRAY[1], None)]
    else:
        edl = [(0, 0, SPRAY[0]), S, (0, SPRAY[1], None)]
    if any(src is None for src, _, _ in edl):
        sys.exit(f"{ver} needs " + ("--lavender " if ver != "v2" else "") + ("--storm" if ver != "v4" else ""))
    parts, labels = [], ""
    for k, (src, f0, f1) in enumerate(edl):
        end = f":end_frame={f1}" if f1 is not None else ""
        parts.append(f"[{src}:v]trim=start_frame={f0}{end},setpts=PTS-STARTPTS,setsar=1[s{k}]")
        labels += f"[s{k}]"
    parts.append(f"{labels}concat=n={len(edl)}:v=1:a=0,format=yuv420p[o]")
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    for s in srcs:
        cmd += ["-i", s]
    subprocess.run(cmd + ["-filter_complex", ";".join(parts), "-map", "[o]", "-c:v", "libx264", "-crf", "10", "-preset",
                          "slow", "-r", str(FPS), dst], check=True)
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of",
                          "csv=p=0", dst], capture_output=True, text=True).stdout.strip()
    print(f"wrote {dst}: {out} frames ({ver})")


if __name__ == "__main__":
    main()
