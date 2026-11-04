#!/usr/bin/env bash
# Ultra Male spec masters, v2 cut: the take with the spray shot (frames 208-221) replaced by 20 frames of the storm
# shot (takes/20261104-231535-1.mp4, frames 46-65, the lightning strike; 480p, upscaled). 295 frames, 12.29 s.
# Real-ESRGAN 4x of both, edit_ultra_male.py, finish_film.py --no-card at 1080x1920 and 2160x3840, visuals only.
# Skips an upscale whose output already exists in <work-dir> (~11 s per 720p frame on CPU; SETUP.md).
#   bash ads/jpg-spec/ultra-male-12s/make_masters_v2.sh <esrgan-python> <realesr-general-x4v3.pth> <work-dir>
set -euo pipefail
PY=$1; W8=$2; WK=$3
D=ads/jpg-spec/ultra-male-12s
mkdir -p "$WK"
[ -s "$WK/esr_4k.mp4" ] || "$PY" -u scripts/esrgan_upscale.py $D/takes/20261104-225549-1.mp4 "$WK/esr_4k.mp4" --weights "$W8" --size 2160x3840
if [ ! -s "$WK/storm_4k.mp4" ]; then
  ffmpeg -loglevel error -y -i $D/takes/20261104-231535-1.mp4 -vf "trim=start_frame=46:end_frame=66,setpts=PTS-STARTPTS" \
    -c:v libx264 -crf 8 -preset slow "$WK/storm20.mp4"
  "$PY" -u scripts/esrgan_upscale.py "$WK/storm20.mp4" "$WK/storm_4k.mp4" --weights "$W8" --size 2160x3840
fi
python3 $D/edit_ultra_male.py "$WK/esr_4k.mp4" "$WK/edit_4k.mp4" --insert "$WK/storm_4k.mp4" --from 0 --len 20
for SZ in 1080x1920 2160x3840; do
  python3 ads/spraymax/cinematic-12s/finish_film.py "$WK/edit_4k.mp4" "$WK/fin_$SZ.mp4" --no-card --size $SZ | tail -1
done
ffmpeg -loglevel error -y -i "$WK/fin_1080x1920.mp4" -an -c:v copy -movflags +faststart $D/jpg-ultra-male-spec.mp4
ffmpeg -loglevel error -y -i "$WK/fin_2160x3840.mp4" -an -c:v copy -movflags +faststart $D/jpg-ultra-male-spec-4k.mp4
ls -la $D/jpg-ultra-male-spec.mp4 $D/jpg-ultra-male-spec-4k.mp4 | awk '{print $5, $9}'
