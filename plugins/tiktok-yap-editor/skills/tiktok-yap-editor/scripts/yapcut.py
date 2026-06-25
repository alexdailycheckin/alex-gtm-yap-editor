#!/usr/bin/env python3
"""Single-pass yap cutter: clause selection + dead-air removal + tight tails,
all in ONE clean CFR 30fps encode. Replaces cut.py + auto-editor (whose VFR
output caused 1-frame black flashes at every jump cut).

- Tight trailing pad (PADR) removes the look-down-at-script frames.
- Multi-source: each clause carries its own "src", so the shared CTA clip
  (IMG_7740 ~2:03->end) can be appended in the same pass for any content clip.
- Per-clause "protect_tail": true keeps a quiet final word (no tail trim).

Usage: yapcut.py --clauses c.json --workdir D --out OUT.mp4
       [--silence-db -42] [--padr 0.04] [--padl 0.08] [--min-gap 0.30] [--d 0.10]
clauses: [{"src":"/abs.MOV","start":6.5,"end":16.6,"label":"hook",
           "protect_tail":false}, ...]
"""
import argparse, json, os, re, subprocess

def silences(wav, thr, d):
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
    ap.add_argument("--out",required=True)
    ap.add_argument("--silence-db",type=float,default=-42.0)
    ap.add_argument("--padl",type=float,default=0.08)
    ap.add_argument("--padr",type=float,default=0.04)
    ap.add_argument("--min-gap",type=float,default=0.30)
    ap.add_argument("--d",type=float,default=0.10)
    ap.add_argument("--min-keep",type=float,default=0.10)
    a=ap.parse_args()

    wd=a.workdir; os.makedirs(f"{wd}/audio",exist_ok=True)
    outbase=os.path.splitext(os.path.basename(a.out))[0]   # parallel-safe scratch
    segdir=f"{wd}/segs_{outbase}"; os.makedirs(segdir,exist_ok=True)
    clauses=json.load(open(a.clauses))

    SIL={}
    for src in {c["src"] for c in clauses}:
        wav=f"{wd}/audio/{os.path.splitext(os.path.basename(src))[0]}.wav"
        if not os.path.exists(wav):
            subprocess.run(["ffmpeg","-nostdin","-y","-i",src,"-ar","16000","-ac","1",
                wav,"-hide_banner","-loglevel","error"],check=True)
        SIL[src]=silences(wav,a.silence_db,a.d)

    keeps=[]   # (src, a, b, gain_db)
    for c in clauses:
        src,cs,ce=c["src"],float(c["start"]),float(c["end"])
        protect=bool(c.get("protect_tail",False))
        g=float(c.get("gain_db",0))
        if c.get("keep_whole",False):        # no silence processing; keep as-is
            keeps.append((src,max(0,cs-a.padl),ce,g)); continue
        sp=speech_in(SIL[src],cs,ce)
        if not sp:
            keeps.append((src,max(0,cs-a.padl),ce,g)); continue
        # merge runs separated by < min-gap (keep natural micro-pauses)
        runs=[]; s0,e0=sp[0]
        for s,e in sp[1:]:
            if s-e0>a.min_gap: runs.append((s0,e0)); s0=s
            e0=e
        runs.append((s0,e0))
        for i,(s,e) in enumerate(runs):
            A=max(cs,s-a.padl)
            last = (i==len(runs)-1)
            if last and protect:
                B=ce                          # keep quiet trailing word
            else:
                B=min(ce, e+a.padr)           # tight tail -> no look-down
            if B-A>=a.min_keep: keeps.append((src,A,B,g))

    concat=f"{wd}/concat_{outbase}.txt"; open(concat,"w").close()
    # alternating STATIC crop (hard cut, no animation) masks pose-match jump-cut
    # stutter: every consecutive segment toggles scale so a cut always changes framing.
    ALT=[1.00,1.06]
    for i,(src,s,e,gain) in enumerate(keeps):
        o=f"{segdir}/yc_{i:03d}.mp4"
        af=f"volume={gain}dB" if gain else "anull"
        z=ALT[i%len(ALT)]; W=round(1080*z); H=round(1920*z)
        if W%2: W+=1
        if H%2: H+=1
        vf=(f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=30")
        subprocess.run(["ffmpeg","-nostdin","-y","-ss",f"{s:.3f}","-to",f"{e:.3f}",
            "-i",src,"-vf",vf,"-af",af,"-c:v","libx264","-preset","veryfast","-crf","18",
            "-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","2","-b:a","192k",
            "-video_track_timescale","30000",o,"-hide_banner","-loglevel","error"],check=True)
        open(concat,"a").write(f"file '{os.path.abspath(o)}'\n")

    subprocess.run(["ffmpeg","-nostdin","-y","-f","concat","-safe","0","-i",concat,
        "-c","copy",a.out,"-hide_banner","-loglevel","error"],check=True)
    dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","csv=p=0",a.out],capture_output=True,text=True).stdout)
    print(f"{len(keeps)} segments -> {a.out}  ({dur:.2f}s)")

if __name__=="__main__":
    main()
