#!/usr/bin/env bash
# Samsung spec masters, v5 cut (see plan.md): 1080x1920 and 2160x3840, visuals only, spec supers on.
#   bash ads/samsung-spec/fold8-ultra-12s/make_masters.sh <esrgan-python> <realesr-general-x4v3.pth> <work-dir>
# Skips an upscale whose output already exists in <work-dir> (each takes ~13 s per frame on CPU; SETUP.md).
set -euo pipefail
PY=$1; W8=$2; WK=$3
D=ads/samsung-spec/fold8-ultra-12s
mkdir -p "$WK"
[ -s "$WK/esr_4k.mp4" ] || "$PY" -u scripts/esrgan_upscale.py $D/takes/edit-v1-720.mp4 "$WK/esr_4k.mp4" --weights "$W8" --size 2160x3840
if [ ! -s "$WK/opener_4k.mp4" ]; then
  ffmpeg -loglevel error -y -i $D/takes/20261104-203734-1.mp4 -vf "trim=start_frame=0:end_frame=65,setpts=PTS-STARTPTS" \
    -c:v libx264 -crf 8 -preset slow "$WK/opener65.mp4"
  "$PY" -u scripts/esrgan_upscale.py "$WK/opener65.mp4" "$WK/opener_4k.mp4" --weights "$W8" --size 2160x3840
fi
python3 $D/add_opener.py "$WK/opener_4k.mp4" "$WK/esr_4k.mp4" "$WK/join_4k.mp4"
python3 $D/grade_logo_shot.py "$WK/join_4k.mp4" "$WK/graded_4k.mp4" --from 62
for SZ in 1080x1920 2160x3840; do
  python3 ads/spraymax/cinematic-12s/finish_film.py "$WK/graded_4k.mp4" "$WK/fin_$SZ.mp4" --no-card --size $SZ | tail -1
  ffmpeg -loglevel error -y -i "$WK/fin_$SZ.mp4" -an -c:v copy "$WK/fin_${SZ}_v.mp4"
done
python3 $D/hud_overlay.py "$WK/fin_1080x1920_v.mp4" $D/samsung-fold8-ultra-spec.mp4 --offset 62
python3 $D/hud_overlay.py "$WK/fin_2160x3840_v.mp4" $D/samsung-fold8-ultra-spec-4k.mp4 --offset 62 --crf 16
ls -la $D/samsung-fold8-ultra-spec.mp4 $D/samsung-fold8-ultra-spec-4k.mp4 | awk '{print $5, $9}'
