#!/usr/bin/env bash
# One-time environment setup for the .ass caption path. Idempotent.
# Installs: (1) libass-enabled ffmpeg, (2) the default preset fonts
# (Montserrat Black/ExtraBold, Anton), and (3) the brand-capable fonts
# (Bricolage Grotesque ExtraBold + Space Mono) used by brand caption presets.
#
# Run once on a new machine, then `python3 scripts/preflight.py` should be green.
set -euo pipefail
FONTDIR="$HOME/Library/Fonts"; mkdir -p "$FONTDIR"

echo "=== 1/4 libass-enabled ffmpeg ==="
if ffmpeg -hide_banner -filters 2>/dev/null | grep -q " ass "; then
  echo "  ass filter already present, skipping"
else
  brew install ffmpeg-full
  brew link --overwrite --force ffmpeg-full
fi

echo "=== 2/4 preset fonts (Montserrat, Anton) ==="
brew install --cask font-montserrat font-anton 2>&1 | tail -2 || true

echo "=== 3/4 static heavy Montserrat (Black, ExtraBold) ==="
python3 -c "import fontTools" 2>/dev/null || pip3 install --quiet fonttools
python3 - <<'PY'
import os
from fontTools import ttLib
from fontTools.varLib.instancer import instantiateVariableFont
home=os.path.expanduser("~")
src=os.path.join(home,"Library/Fonts/Montserrat[wght].ttf")
if os.path.exists(src):
    for wght,suffix,fam in [(900,"Black","Montserrat Black"),(800,"ExtraBold","Montserrat ExtraBold")]:
        out=os.path.join(home,f"Library/Fonts/Montserrat-{suffix}.ttf")
        if os.path.exists(out): print("  exists:",out); continue
        f=ttLib.TTFont(src); instantiateVariableFont(f,{"wght":wght},inplace=True,updateFontNames=True)
        nm=f["name"]
        for nid,val in [(1,fam),(2,"Regular"),(4,fam),(6,fam.replace(" ","")),(16,fam),(17,"Regular")]:
            nm.setName(val,nid,3,1,0x409)
        f.save(out); print("  wrote:",out)
else:
    print("  Montserrat variable font not found (cask may not have installed); skipping")
PY

echo "=== 4/4 brand fonts (Bricolage Grotesque ExtraBold + Space Mono) ==="
# Static TTFs from fontsource (avoids variable-font 'renders thin' fallback).
TMP="$(mktemp -d)"
dl(){ curl -fsSL -o "$2" "$1"; }
dl "https://cdn.jsdelivr.net/fontsource/fonts/bricolage-grotesque@latest/latin-800-normal.ttf" "$TMP/bricolage-800.ttf"
dl "https://cdn.jsdelivr.net/fontsource/fonts/space-mono@latest/latin-700-normal.ttf" "$FONTDIR/SpaceMono-Bold.ttf"
dl "https://cdn.jsdelivr.net/fontsource/fonts/space-mono@latest/latin-400-normal.ttf" "$FONTDIR/SpaceMono-Regular.ttf"
# Give Bricolage a unique family so libass/fontconfig targets the heavy weight exactly.
python3 -c "import fontTools" 2>/dev/null || pip3 install --quiet fonttools
python3 - "$TMP/bricolage-800.ttf" "$FONTDIR/BricolageGrotesque-ExtraBold.ttf" <<'PY'
import sys
from fontTools import ttLib
f=ttLib.TTFont(sys.argv[1]); fam="Bricolage Grotesque ExtraBold"; nm=f["name"]
for nid,val in [(1,fam),(2,"Regular"),(4,fam),(6,fam.replace(" ","")),(16,fam),(17,"Regular")]:
    nm.setName(val,nid,3,1,0x409); nm.setName(val,nid,1,0,0)
f.save(sys.argv[2]); print("  wrote:",sys.argv[2])
PY
rm -rf "$TMP"
fc-cache -f "$FONTDIR" >/dev/null 2>&1 || true
echo "=== done. run: python3 scripts/preflight.py ==="
