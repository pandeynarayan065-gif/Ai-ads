#!/usr/bin/env bash
# Ultra Male spec masters, v4 cut: the take with the spray shot (frames 208-221) replaced by the lavender gust
# (takes/20261105-010257-1.mp4, frames 26-49, 480p, upscaled). 299 frames, 12.46 s. Visuals only.
# Real-ESRGAN 4x of both, edit_ultra_male.py, finish_film.py --no-card at 1080x1920 and 2160x3840.
# Upscales write .part files and are renamed when complete, so an interrupted run restarts cleanly (SETUP.md).
#   bash ads/jpg-spec/ultra-male-12s/make_masters.sh <esrgan-python> <realesr-general-x4v3.pth> <work-dir>
set -euo pipefail
PY=$1; W8=$2; WK=$3
D=ads/jpg-spec/ultra-male-12s
mkdir -p "$WK"
if [ ! -s "$WK/esr_4k.mp4" ]; then
  "$PY" -u scripts/esrgan_upscale.py $D/takes/20261104-225549-1.mp4 "$WK/esr_4k.part.mp4" --weights "$W8" --size 2160x3840
  mv "$WK/esr_4k.part.mp4" "$WK/esr_4k.mp4"
fi
if [ ! -s "$WK/lav_4k.mp4" ]; then
  ffmpeg -loglevel error -y -i $D/takes/20261105-010257-1.mp4 -vf "trim=start_frame=26:end_frame=50,setpts=PTS-STARTPTS" \
    -c:v libx264 -crf 8 -preset slow "$WK/lav24.mp4"
  "$PY" -u scripts/esrgan_upscale.py "$WK/lav24.mp4" "$WK/lav_4k.part.mp4" --weights "$W8" --size 2160x3840
  mv "$WK/lav_4k.part.mp4" "$WK/lav_4k.mp4"
fi
python3 $D/edit_ultra_male.py "$WK/esr_4k.mp4" "$WK/edit_4k.mp4" --lavender "$WK/lav_4k.mp4" --lavender-from 0
for SZ in 1080x1920 2160x3840; do
  python3 ads/spraymax/cinematic-12s/finish_film.py "$WK/edit_4k.mp4" "$WK/fin_$SZ.mp4" --no-card --size $SZ | tail -1
done
ffmpeg -loglevel error -y -i "$WK/fin_1080x1920.mp4" -an -c:v copy -movflags +faststart $D/jpg-ultra-male-spec.mp4
ffmpeg -loglevel error -y -i "$WK/fin_2160x3840.mp4" -an -c:v copy -movflags +faststart $D/jpg-ultra-male-spec-4k.mp4
ls -la $D/jpg-ultra-male-spec.mp4 $D/jpg-ultra-male-spec-4k.mp4 | awk '{print $5, $9}'
