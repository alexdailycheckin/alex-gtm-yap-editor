#!/usr/bin/env python3
"""Preflight check for the tiktok-yap-editor pipeline.
Verifies the exact tools the pipeline depends on and prints install hints for
anything missing. Run this first so you fail fast with a clear fix instead of
discovering a missing dependency three steps into a render."""
import shutil, subprocess, os, glob, sys

ok = True
def check(label, passed, hint=""):
    global ok
    mark = "OK " if passed else "MISSING"
    print(f"  [{mark}] {label}")
    if not passed:
        ok = False
        if hint: print(f"          fix: {hint}")

print("=== tiktok-yap-editor preflight ===")

# ffmpeg + ffprobe
has_ffmpeg = shutil.which("ffmpeg") is not None
check("ffmpeg", has_ffmpeg, "brew install ffmpeg")
check("ffprobe", shutil.which("ffprobe") is not None, "comes with ffmpeg")

# caption filters. Preferred path is the .ass filter (build_ass.py + compose_ass.sh).
# overlay is the fallback path (caption_frames.py + compose.sh, no libass needed).
if has_ffmpeg:
    filters = subprocess.run(["ffmpeg","-hide_banner","-filters"],
                             capture_output=True, text=True).stdout
    check("overlay filter (Pillow fallback path)", " overlay " in filters,
          "ffmpeg build lacks overlay; reinstall ffmpeg")
    has_ass = " ass " in filters or " subtitles " in filters
    check("libass / ass filter (preferred .ass caption path)", has_ass,
          "the default `ffmpeg` bottle lacks libass. Install the full build:\n"
          "          brew install ffmpeg-full && brew link --overwrite --force ffmpeg-full\n"
          "          (if a later `brew upgrade` relinks the minimal ffmpeg and this "
          "breaks, re-run the link command. Until then, fall back to "
          "caption_frames.py + compose.sh.)")

# whisper.cpp
has_w = shutil.which("whisper-cli") is not None
check("whisper-cli (whisper.cpp)", has_w, "brew install whisper-cpp")

# model
models = glob.glob(os.path.expanduser("~/.whisper-models/ggml-*.bin"))
check("whisper ggml model in ~/.whisper-models/", len(models) > 0,
      "mkdir -p ~/.whisper-models && curl -L -o ~/.whisper-models/ggml-small.en.bin "
      "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin")
if models:
    print(f"          found: {', '.join(os.path.basename(m) for m in models)}")

# Pillow
try:
    import PIL  # noqa
    check("Python Pillow", True)
except Exception:
    check("Python Pillow", False, "pip3 install Pillow")

# caption fonts. The .ass presets reference families by name via fontconfig:
#   minimal/native -> Montserrat,  bold -> Anton. Arial Black is the Pillow
#   fallback font. Missing preset fonts degrade gracefully (libass substitutes),
#   but the look will be off, so flag them.
def fc_has(family):
    try:
        out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
        return family.lower() in out.lower()
    except Exception:
        return False

check("Arial Black font (Pillow fallback)",
      os.path.exists("/System/Library/Fonts/Supplemental/Arial Black.ttf"),
      "any heavy sans .ttf works; update FONT path in caption_frames.py")
for fam in ["Montserrat Black", "Anton"]:
    check(f"{fam} font (.ass preset)", fc_has(fam),
          "run: bash scripts/setup_fonts.sh  (installs fonts + a static "
          "Montserrat Black; the cask alone ships a variable font that renders Thin)")

print("=== " + ("ALL GOOD" if ok else "FIX THE MISSING ITEMS ABOVE") + " ===")
sys.exit(0 if ok else 1)
