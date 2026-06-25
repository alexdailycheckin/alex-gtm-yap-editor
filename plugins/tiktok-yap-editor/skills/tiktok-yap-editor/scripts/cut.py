#!/usr/bin/env python3
"""Transcript-first cutter for talking-head yaps.

You hand it an ORDERED list of clauses (the story you shaped from the
transcript). It trims interior dead air, protects quiet trailing words, adds
alternating zoom punch-ins to mask the jump cuts, and concatenates to a tight
vertical cut. The clause selection is the editorial decision and stays human;
this script only handles the deterministic mechanics.

clauses.json:
  [
    {"src": "/abs/IMG_7489.MOV", "start": 0.00, "end": 3.30, "label": "hook"},
    {"src": "/abs/IMG_7487.MOV", "start": 17.05, "end": 36.55, "label": "why"},
    ...
  ]

Usage:
  python cut.py --clauses clauses.json --workdir _edit --out tight_cut.mp4 \
                [--silence-db -19] [--no-zoom]

Notes baked in from hard experience:
- ffmpeg gets -nostdin everywhere: inside a loop it otherwise swallows stdin.
- Cuts are driven by AUDIO ENERGY (silencedetect), never whisper word times,
  which drift. The silence threshold is content-dependent: outdoor/noisy audio
  floors around -19 to -25 dB, so tune --silence-db per clip if needed.
- The last speech run in every clause is force-extended to the clause end so a
  quiet trailing word (e.g. a soft "period") is never mistaken for silence and
  clipped. Short clauses with no detected speech are kept whole for the same
  reason.
- Output is an intermediate. Always finish with compose.sh (re-encode) before
  shipping: a concat of copied streams can play black in QuickTime.
"""
import argparse, json, os, re, subprocess

def silences(wav, thr, d=0.25):
    r = subprocess.run(["ffmpeg","-nostdin","-i",wav,"-af",
        f"silencedetect=noise={thr}dB:d={d}","-f","null","-"],
        capture_output=True, text=True).stderr
    sil=[]; st=None
    for l in r.splitlines():
        m=re.search(r"silence_start:\s*([\d.]+)",l)
        if m: st=float(m.group(1))
        m=re.search(r"silence_end:\s*([\d.]+)",l)
        if m and st is not None: sil.append((st,float(m.group(1)))); st=None
    return sil

def speech_in(sil, cs, ce):
    pts=[(s,e) for s,e in sil if e>cs and s<ce]; sp=[]; cur=cs
    for s,e in pts:
        s=max(cs,s); e=min(ce,e)
        if s>cur: sp.append((cur,s))
        cur=max(cur,e)
    if cur<ce: sp.append((cur,ce))
    return sp

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--clauses",required=True)
    ap.add_argument("--workdir",default=".yap_build")
    ap.add_argument("--out",default="tight_cut.mp4")
    ap.add_argument("--silence-db",type=float,default=-19.0)
    ap.add_argument("--no-zoom",action="store_true")
    a=ap.parse_args()

    wd=a.workdir; os.makedirs(f"{wd}/audio",exist_ok=True); os.makedirs(f"{wd}/segs",exist_ok=True)
    clauses=json.load(open(a.clauses))

    # silence map per unique source (extract 16k mono once)
    SIL={}
    for src in {c["src"] for c in clauses}:
        wav=f"{wd}/audio/{os.path.splitext(os.path.basename(src))[0]}.wav"
        if not os.path.exists(wav):
            subprocess.run(["ffmpeg","-nostdin","-y","-i",src,"-ar","16000","-ac","1",
                wav,"-hide_banner","-loglevel","error"],check=True)
        SIL[src]=silences(wav,a.silence_db)

    PADL,PADR,MINKEEP,BIGGAP=0.07,0.12,0.10,0.40
    keeps=[]  # (src,a,b,clause_idx)
    for ci,c in enumerate(clauses):
        src,cs,ce=c["src"],float(c["start"]),float(c["end"])
        sp=speech_in(SIL[src],cs,ce)
        if not sp:                                  # whole clause quiet -> keep
            keeps.append((src,max(0,cs-PADL),ce+PADR,ci)); continue
        runs=[]; s0,e0=sp[0]
        for s,e in sp[1:]:
            if s-e0>BIGGAP: runs.append((s0,e0)); s0=s
            e0=e
        runs.append((s0,e0))
        runs[-1]=(runs[-1][0],ce)                   # protect trailing quiet word
        for s,e in runs:
            A=max(cs,s-PADL); B=min(ce+PADR,e+PADR)
            if B-A>=MINKEEP: keeps.append((src,A,B,ci))

    # alternating zoom punch-ins: change level at clause change or every ~4s
    zl=[1.00,1.08,1.13,1.05,1.11]; zi=0; acc=0.0; last=-1; out=[]
    for src,s,e,ci in keeps:
        if ci!=last:
            if last!=-1: zi=(zi+1)%len(zl)
            last=ci; acc=0.0
        elif acc>=4.0:
            zi=(zi+1)%len(zl); acc=0.0
        acc+=e-s; out.append((src,s,e,1.0 if a.no_zoom else zl[zi]))

    # extract each keep segment (reframed to 1080x1920, 30fps) then concat
    concat=f"{wd}/concat.txt"; open(concat,"w").close()
    for i,(src,s,e,z) in enumerate(out):
        o=f"{wd}/segs/seg_{i:03d}.mp4"; W=round(1080*z); H=round(1920*z)
        if W%2: W+=1
        if H%2: H+=1
        vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30")
        subprocess.run(["ffmpeg","-nostdin","-y","-ss",f"{s:.3f}","-to",f"{e:.3f}",
            "-i",src,"-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","18",
            "-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","2","-b:a","192k",
            "-video_track_timescale","30000",o,"-hide_banner","-loglevel","error"],check=True)
        open(concat,"a").write(f"file '{os.path.abspath(o)}'\n")

    subprocess.run(["ffmpeg","-nostdin","-y","-f","concat","-safe","0","-i",concat,
        "-c","copy",a.out,"-hide_banner","-loglevel","error"],check=True)
    dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",a.out],capture_output=True,text=True).stdout)
    print(f"{len(out)} keep-segments -> {a.out}  ({dur:.2f}s)")
    print("INTERMEDIATE: run compose.sh next to burn captions + loudnorm + clean re-encode")

if __name__=="__main__":
    main()
