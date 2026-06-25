#!/usr/bin/env python3
"""Cover / thumbnail builder for a finished vertical video.

Two modes:

1) Contact sheet (pick the frame):
   python3 cover.py --video final.mp4 --contact-sheet --out .cover_cand [--interval 2]
   Extracts a candidate frame every N seconds so you (and Alex) can pick the
   strongest one: clear face, eyes open, good expression, no mid-blink/mid-word.

2) Build the cover:
   python3 cover.py --video final.mp4 --frame 6.4 --title "FIRST TIME OFF|IN MY WHOLE LIFE" \
     --out cover.jpg [--no-text] [--title-y 520] [--yt]

Design (2025-26 best practice, on-brand minimal):
- Vertical cover is 1080x1920. The Instagram grid crops covers to the CENTRE
  1080x1080 square, so the title + face must live inside that square. We keep the
  title in x[140..940], inside the centre square vertically.
- Title style matches the minimal caption look: Montserrat Black, white, heavy
  black stroke, ALL CAPS. A soft dark scrim sits behind the text for legibility.
  Keep it clean, not clickbait (no neon, no giant arrows).
- --yt also exports a 1280x720 thumbnail (subject scaled onto a blurred fill of
  the same frame) for YouTube repurposes.

Pick a frame with eye contact and an expressive (not neutral) face: it lifts CTR.
"""
import argparse, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FONT_CANDIDATES = [
    os.path.expanduser("~/Library/Fonts/BricolageGrotesque-ExtraBold.ttf"),
    os.path.expanduser("~/Library/Fonts/Montserrat-Black.ttf"),
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
]


def font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def grab(video, t, out):
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-ss", str(t), "-i", video,
                    "-frames:v", "1", out, "-hide_banner", "-loglevel", "error"], check=True)


def duration(video):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", video], capture_output=True, text=True).stdout
    return float(o.strip())


def contact_sheet(video, out, interval):
    os.makedirs(out, exist_ok=True)
    dur = duration(video)
    t = 0.5
    while t < dur:
        grab(video, t, os.path.join(out, f"f_{t:05.1f}.jpg"))
        t += interval
    print(f"candidates in {out}/ (every {interval}s up to {dur:.1f}s)")


def draw_title(img, title, title_y):
    dr = ImageDraw.Draw(img)
    lines = [l for l in title.split("|") if l]
    fs = 96
    f = font(fs)
    # fit width
    def wide(ls, ff):
        return max(ff.getbbox(l.upper(), stroke_width=10)[2] for l in ls)
    while wide(lines, f) > (940 - 140) and fs > 48:
        fs -= 4; f = font(fs)
    # soft dark scrim band behind the text for legibility
    lh = f.getbbox("Ay", stroke_width=10)[3] + 18
    band_h = lh * len(lines) + 60
    scrim = Image.new("RGBA", (W, band_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    sd.rectangle([0, 0, W, band_h], fill=(0, 0, 0, 110))
    scrim = scrim.filter(ImageFilter.GaussianBlur(30))
    img.alpha_composite(scrim, (0, max(0, title_y - 30)))
    y = title_y
    for l in lines:
        t = l.upper()
        bb = f.getbbox(t, stroke_width=10); lw = bb[2] - bb[0]
        dr.text(((W - lw) / 2, y), t, font=f, fill=(255, 255, 255, 255),
                stroke_width=10, stroke_fill=(0, 0, 0, 255))
        y += lh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--image", help="use a still (already 1080x1920, caption-free) instead of grabbing from --video")
    ap.add_argument("--contact-sheet", action="store_true")
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--frame", type=float)
    ap.add_argument("--title", default="")
    ap.add_argument("--no-text", action="store_true")
    ap.add_argument("--title-y", type=int, default=520)
    ap.add_argument("--yt", action="store_true")
    ap.add_argument("--out", default="cover.jpg")
    a = ap.parse_args()

    if a.contact_sheet:
        contact_sheet(a.video, a.out, a.interval)
        return
    if a.frame is None and not a.image:
        raise SystemExit("give --frame T (use --contact-sheet first to pick) or --image")

    with tempfile.TemporaryDirectory() as td:
        if a.image:
            raw = a.image
        else:
            raw = os.path.join(td, "f.png"); grab(a.video, a.frame, raw)
        img = Image.open(raw).convert("RGBA")
        if img.size != (W, H):
            img = img.resize((W, H))
        if a.title and not a.no_text:
            draw_title(img, a.title, a.title_y)
        img.convert("RGB").save(a.out, quality=92)
        print(f"wrote {a.out}  (frame {a.frame}s)")

        if a.yt:
            # 1280x720: blurred fill of the frame + the subject scaled to fit height
            bg = img.convert("RGB").resize((1280, 1280)).filter(ImageFilter.GaussianBlur(40))
            bg = bg.crop((0, 280, 1280, 1000))  # centre 16:9 band
            scale = 720 / H; fw = int(W * scale)
            fg = img.convert("RGB").resize((fw, 720))
            bg.paste(fg, ((1280 - fw) // 2, 0))
            ytout = os.path.splitext(a.out)[0] + "_yt.jpg"
            bg.save(ytout, quality=92)
            print(f"wrote {ytout}  (1280x720)")


if __name__ == "__main__":
    main()
