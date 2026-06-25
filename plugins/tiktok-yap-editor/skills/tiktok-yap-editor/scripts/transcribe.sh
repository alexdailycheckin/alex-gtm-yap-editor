#!/usr/bin/env bash
# Transcribe one clip with whisper.cpp, producing word-level timestamps.
# Usage: transcribe.sh <video> <out_prefix> [--words]
#   default  : sentence-level .txt + .json (use for reading/story-shaping)
#   --words  : word-level with DTW alignment (use for caption sync)
#
# Why DTW for captions: plain whisper word END-times drift and are unreliable
# for cutting, but -dtw gives accurate per-word timing that captions need to
# land on the actual speech. We extract 16kHz mono first because that's what
# whisper.cpp expects.
set -euo pipefail
VIDEO="$1"; OUT="$2"; MODE="${3:-}"
MODEL="${WHISPER_MODEL:-$HOME/.whisper-models/ggml-small.en.bin}"
WAV="${OUT}.wav"

ffmpeg -nostdin -y -i "$VIDEO" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV" \
  -hide_banner -loglevel error

if [ "$MODE" = "--words" ]; then
  # -ml 1 -sow = one token per segment (word-level); -dtw = accurate alignment
  whisper-cli -m "$MODEL" -f "$WAV" -ml 1 -sow -dtw small.en -oj -of "$OUT" \
    2>/dev/null >/dev/null
  echo "word-level timestamps: ${OUT}.json"
else
  whisper-cli -m "$MODEL" -f "$WAV" -otxt -oj -of "$OUT" 2>/dev/null >/dev/null
  echo "transcript: ${OUT}.txt  (json: ${OUT}.json)"
fi
