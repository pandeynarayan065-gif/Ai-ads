#!/usr/bin/env bash
# Ultra Male spec masters: Real-ESRGAN 4x of the take, then finish_film.py --no-card at 1080x1920 and 2160x3840,
# visuals only. Skips the upscale if <work-dir>/esr_4k.mp4 exists (~13 s per frame on CPU; SETUP.md).
#   bash ads/jpg-spec/ultra-male-12s/make_masters.sh <esrgan-python> <realesr-general-x4v3.pth> <work-dir>
set -euo pipefail
PY=$1; W8=$2; WK=$3
D=ads/jpg-spec/ultra-male-12s
TAKE=$D/takes/20261104-225549-1.mp4
mkdir -p "$WK"
[ -s "$WK/esr_4k.mp4" ] || "$PY" -u scripts/esrgan_upscale.py $TAKE "$WK/esr_4k.mp4" --weights "$W8" --size 2160x3840
for SZ in 1080x1920 2160x3840; do
  python3 ads/spraymax/cinematic-12s/finish_film.py "$WK/esr_4k.mp4" "$WK/fin_$SZ.mp4" --no-card --size $SZ | tail -1
done
ffmpeg -loglevel error -y -i "$WK/fin_1080x1920.mp4" -an -c:v copy -movflags +faststart $D/jpg-ultra-male-spec.mp4
ffmpeg -loglevel error -y -i "$WK/fin_2160x3840.mp4" -an -c:v copy -movflags +faststart $D/jpg-ultra-male-spec-4k.mp4
ls -la $D/jpg-ultra-male-spec.mp4 $D/jpg-ultra-male-spec-4k.mp4 | awk '{print $5, $9}'
