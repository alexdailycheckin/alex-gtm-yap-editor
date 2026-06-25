#!/usr/bin/env python3
"""Render burned-caption + hook frames as transparent PNGs.

Why PNG frames instead of an .ass/subtitles/drawtext filter: many ffmpeg builds
(including the common Homebrew one on this machine) ship WITHOUT libass /
freetype / drawtext, so those filters simply do not exist. The overlay filter
is always present, so we render text with Pillow and composite the frame
sequence with overlay (see compose.sh). This path works on any ffmpeg build.

Caption style is a STABLE phrase block (default 3 words) with the active word
highlighted in yellow and slightly larger. This reads smooth. The tempting
alternative, a line that accumulates words then resets, looks "erratic" because
the text box keeps growing and clearing, so we avoid it by default.

Input is whisper -dtw word-level JSON (accurate timing). Optional corrections
JSON fixes transcriber slips without re-rendering the audio:
  {"drop": [110,111], "fix": {"117": "Be", "122": "They"}}

Usage:
  python caption_frames.py --words words.json --out capframes \
    [--hook "YOU'LL REGRET THIS|IN 10 YEARS"] [--corrections corr.json] \
    [--cap-y 1300] [--hook-y 360] [--group 3] [--fps 30] \
    [--active-color 255,222,0]
"""
import argparse, json, math, os, re, bisect
from PIL import Image, ImageDraw, ImageFont

FONT_DEFAULT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
W, H = 1080, 1920

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--words",required=True)
    ap.add_argument("--out",default="capframes")
    ap.add_argument("--hook",default="")          # lines separated by |
    ap.add_argument("--corrections",default="")
    ap.add_argument("--font",default=FONT_DEFAULT)
    ap.add_argument("--cap-y",type=int,default=1300)
    ap.add_argument("--hook-y",type=int,default=360)
    ap.add_argument("--group",type=int,default=3)
    ap.add_argument("--fps",type=int,default=30)
    ap.add_argument("--active-color",default="255,222,0")
    ap.add_argument("--hook-secs",type=float,default=2.5)
    a=ap.parse_args()

    YEL=tuple(int(x) for x in a.active_color.split(","))+(255,)
    WHITE=(255,255,255,255); BLK=(0,0,0,255)
    d=json.load(open(a.words))
    words=[[s["offsets"]["from"]/1000.0,s["offsets"]["to"]/1000.0,s["text"].strip()]
           for s in d["transcription"] if s["text"].strip()]

    if a.corrections:
        c=json.load(open(a.corrections)); drop=set(c.get("drop",[]))
        fix={int(k):v for k,v in c.get("fix",{}).items()}
        words=[[w[0],w[1],fix.get(i,w[2])] for i,w in enumerate(words) if i not in drop]

    eos=lambda t: t.rstrip()[-1:] in ".?!"
    disp=lambda t: re.sub(r"[.,!?;:]+$","",t).upper()

    # stable phrase groups
    groups=[]; cur=[]
    for w in words:
        cur.append(w)
        if len(cur)>=a.group or eos(w[2]): groups.append(cur); cur=[]
    if cur: groups.append(cur)

    G=[]
    for gi,g in enumerate(groups):
        gs=g[0][0]; ge=groups[gi+1][0][0] if gi+1<len(groups) else g[-1][1]+0.30
        toks=[disp(w[2]) for w in g]
        wins=[(g[k][0], g[k+1][0] if k+1<len(g) else ge) for k in range(len(g))]
        G.append((gs,ge,toks,wins))
    gstarts=[x[0] for x in G]

    S_ACT,S_OTH,SP=98,84,26
    fa=ImageFont.truetype(a.font,S_ACT); fo=ImageFont.truetype(a.font,S_OTH)
    fhook=ImageFont.truetype(a.font,78)
    HOOK=[s for s in a.hook.split("|") if s] if a.hook else []
    DUR=words[-1][1]+0.35; NF=math.ceil(DUR*a.fps)

    def ww(t,f): b=f.getbbox(t,stroke_width=1); return b[2]-b[0]
    def draw_group(dr,toks,active,cy):
        fonts=[fa if i==active else fo for i in range(len(toks))]
        cols=[YEL if i==active else WHITE for i in range(len(toks))]
        widths=[ww(t,f) for t,f in zip(toks,fonts)]
        total=sum(widths)+SP*(len(toks)-1); scale=1.0
        if total>1000:
            scale=1000/total
            fonts=[ImageFont.truetype(a.font,int((S_ACT if i==active else S_OTH)*scale)) for i in range(len(toks))]
            widths=[ww(t,f) for t,f in zip(toks,fonts)]
            total=sum(widths)+SP*scale*(len(toks)-1)
        x=(W-total)/2; sw=max(6,int(11*scale))
        for t,f,c,w in zip(toks,fonts,cols,widths):
            asc,desc=f.getmetrics(); y=cy-(asc+desc)/2
            dr.text((x,y),t,font=f,fill=c,stroke_width=sw,stroke_fill=BLK); x+=w+SP*scale

    def hook_a(t):
        if t<0.15: return t/0.15
        if t>a.hook_secs: return 0
        if t>a.hook_secs-0.25: return (a.hook_secs-t)/0.25
        return 1.0

    os.system(f"rm -rf {a.out}; mkdir -p {a.out}")
    for f in range(NF):
        t=f/a.fps
        img=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(img)
        if HOOK and t<a.hook_secs:
            al=hook_a(t)
            if al>0:
                hy=a.hook_y
                for ln in HOOK:
                    bb=fhook.getbbox(ln,stroke_width=8); lw=bb[2]-bb[0]; lh=bb[3]-bb[1]
                    dr.text(((W-lw)/2,hy),ln,font=fhook,fill=YEL[:3]+(int(255*al),),
                            stroke_width=9,stroke_fill=(0,0,0,int(255*al))); hy+=lh+24
        gi=bisect.bisect_right(gstarts,t)-1
        if 0<=gi<len(G):
            gs,ge,toks,wins=G[gi]
            if gs<=t<ge:
                act=0
                for k,(ws,we) in enumerate(wins):
                    if ws<=t<we: act=k; break
                    if t>=we: act=k
                draw_group(dr,toks,act,a.cap_y)
        img.save(f"{a.out}/f_{f:05d}.png")
    print(f"{NF} frames -> {a.out}/  ({len(groups)} phrase-groups, dur~{DUR:.2f}s)")

if __name__=="__main__":
    main()
