# Speech quirks and repetition: keep the feel, cut the noise

The line audit (SKILL step 5b) must NOT blindly trim repetition or scrub every
"um". Repetition and disfluency are often deliberate effect or authentic human
texture, and removing them flattens the video into something that reads as an ad
or as AI. The rule is **remove noise, protect feel.** A clip with zero
imperfections is a failure mode, not the goal (over-scrubbed talking-head
pattern-matches to synthetic/scripted and trust drops; native-2026 rewards a few
real human beats).

This file is the judgment the audit applies. It is grounded research, not vibes
(epizeuxis/diacope rhetoric, Clark & Fox Tree on um/uh, Levelt on repair
structure, MrBeast's 2024 "let scenes breathe" reversal, reaction-creator
practice). Read it when a repeat or a quirk is borderline.

## Two levers (use the right one)

You can remove something from the CAPTION without removing it from the AUDIO.
This is the most useful move and the one that resolves most borderline cases:

- **`corrections.json` `drop`** removes a word from the BURNED TEXT only. The
  audio is untouched. Use this to keep an authentic spoken quirk audible while
  keeping the on-screen text clean and readable (e.g. drop a stray "um" or a
  doubled word from the caption, but the viewer still HEARS the real delivery).
- **Clause in/out boundaries (re-cut)** remove from the AUDIO+VIDEO. Only use this
  when the thing is genuinely noise (dead air, a clean-up false start, a rambling
  tangent). Cutting a real effect or reaction at the clause level destroys it.

Default for a borderline quirk: leave it in the audio, clean the caption.

## Repetition: KEEP vs CUT

**KEEP (it is an effect or a reaction):**
- A rhetorical figure: epizeuxis (back-to-back, "incredible, incredible"), diacope
  ("Bond. James Bond."), anaphora/epistrophe (same word starting/ending clauses),
  a rule-of-three, or a callback/running gag. These are load-bearing structure.
- A reaction / savoring beat responding to a present stimulus: "so good, so good",
  "oh my god, oh my god", "no no no". In food/reaction content the repeat IS the
  payload and the emotional peak. Default KEEP.
- The delivery CHANGES on the repeat: louder, higher, slower, broken, falling
  pitch, heavier stress, or a deliberate beat/pause before it. Change = performed.
- It is deadpan-identical ON PURPOSE for comic effect, or it escalates.

**CUT (it is noise):**
- A redundant FACT/number/phrase repeated with no rhetorical payoff. Real example:
  "two and a half weeks" said 3x in 12s while explaining, that is clutter, trim to
  one or two. (This is different from "incredible, incredible", which is a beat.)
- A pure stall: "the the the", a word re-launched while the brain catches up.
- A clean-up restart: the relaunch says the SAME thing more fluently
  ("we shipp- we shipped it"). Keep the clean instance, cut the false start.
- Flat, identical prosody, rushed back-to-back, mid-planning (not a reaction).

## Disfluencies (um, false starts, repairs, fillers): KEEP vs CUT

| Quirk | Default | Keep when | Cut when |
|---|---|---|---|
| `um` / `uh` | cut most, keep a few | right before a key/complex line (it boosts attention + recall), or a natural thinking beat that adds humanity | mid-phrase, frequent, before trivial words |
| silent pause | trim, don't kill | between ideas as rhythm, or a beat that sets up a punchline/reveal | mid-clause dead air, or any stall-length gap |
| false start (clean-up) | cut | almost never | relaunch repeats the same content (keep the clean take) |
| repair (self-correction) | keep selectively | the fix changes a fact, hedges, or walks hype back to honesty (trust + real-time thinking) | the "fix" lands on the same meaning |
| interjection (oh, wow, hm) | keep | genuine emotion/stance/reaction energy | a hesitation-stall dressed as a reaction |
| like / you know | cut most | rare signature-voice micro-dose | repeated verbal tic |
| laugh, gasp, wince | keep | it's real emotion (personality) | (basically always keep) |

## The four signals (read together, not alone)

1. **Prosody:** does the repeat/quirk change pitch, volume, pace, stress? Change =
   intentional/keep. Flat carbon-copy = stall/cut. (Strongest tell. Check audio,
   not just transcript: `ffmpeg -af volumedetect` on the two spans, or just listen.)
2. **Timing:** a deliberate beat/pause = intentional. Rushed back-to-back = stall.
3. **Context:** reacting to a present stimulus (food, reveal, number) = keep.
   Mid-planning / searching for the word = cut.
4. **Completeness:** complete words/phrases = candidate keep. Cut-off fragments,
   partial words, repairs to the same meaning = cut.

**The removal test (the tiebreaker):** delete it in your head. If the line loses
a fact, a hedge, a correction, energy, a beat, or personality, KEEP. If it reads
identically, CUT. When still unsure, listen with audio: if the transcript loses
nothing but the audio loses energy or a beat, KEEP.

## The texture floor

After the audit, the clip must still contain 2-3 genuine human beats (a savoring
repeat, a laugh, an honest self-correction, one well-placed pause/um before a key
line). If the audit stripped everything, it over-edited: put the highest-emotion
item back. "A confident person thinking out loud", not a teleprompter, not a
nervous wreck.

## Worked examples from real edits

- "Incredible, incredible" over the food = epizeuxis + savoring reaction beat =
  KEEP in audio. (If the caption looks cluttered, drop the duplicate from the
  caption only via corrections; the spoken beat stays.) Cutting it at the clause
  level would have been the mistake.
- "Two and a half weeks" x3 while explaining the job gap = redundant fact, no
  payoff = trim to one or two (audio-level, re-cut the clause).
- "I went- I mean we went" = meaningful repair (solo -> team, plus candour) =
  KEEP. "We shipp- we shipped it" = clean-up = cut to "we shipped it".
