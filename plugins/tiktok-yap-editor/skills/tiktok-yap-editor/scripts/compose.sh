#!/usr/bin/env bash
# Final pass: composite caption frames onto the cut, normalize loudness, and
# re-encode to clean constant-frame-rate 30fps.
#
# Usage: compose.sh <cut.mp4> <capframes_dir> <out.mp4>
#
# Three jobs in one pass, each for a reason:
# - overlay the PNG frame sequence (our text layer; see caption_frames.py)
# - loudnorm to -14 LUFS: TikTok normalizes toward ~-14, raw phone audio is
#   usually ~-22 and sounds thin against the feed.
# - re-encode CFR 30fps: a concat of copied streams (from cut.py) can play
#   black in QuickTime due to irregular timestamps; this clean pass fixes it.
set -euo pipefail
CUT="$1"; FRAMES="$2"; OUT="$3"

ffmpeg -nostdin -y -i "$CUT" -framerate 30 -i "${FRAMES}/f_%05d.png" \
  -filter_complex "[0:v]fps=30,setsar=1[v];[v][1:v]overlay=0:0:format=auto[o]" \
  -map "[o]" -map 0:a \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 \
  -video_track_timescale 30000 -c:a aac -b:a 192k -movflags +faststart \
  "$OUT" -hide_banner -loglevel error

echo "wrote $OUT"
echo "--- QA: loudness (target ~-14 LUFS) ---"
ffmpeg -nostdin -i "$OUT" -af ebur128=peak=true -f null - 2>&1 \
  | grep -A1 "Integrated loudness" | tail -2
ffprobe -v error -show_entries format=duration:stream=r_frame_rate \
  -select_streams v:0 -of default=noprint_wrappers=1 "$OUT"
