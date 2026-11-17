# 07 Reality check, round 2: prompt-seedance-12s.md (version 2)
## Verdict: PASS

All eight round-1 fixes are in, word for word where I gave the wording. The only new text is the worn-hang
sentence that replaces Image 3, and it adds no new risk I would bet credits on. Lint: WARN, only the intended
"product lies down". No FAIL. 8,535 characters, 1,507 words (lint 1,529).

Fix-by-fix check against round 1:
1. Image 3 is gone from the mapping, the scale sentence and the Throughout line. The `--ref` list is Image 1 and
   Image 2. No peach or roses can be pasted. The worn look is now in words in the product truth, under the
   condition "Worn and seen from behind". It doesn't conflict with "hood folded flat" in the empty shots.
2. "real white smoke, real embers" and the true-size sentence are out of the inherited block.
3. 00:00.0 now says "falls straight down away from the lens", and the ash is "a thin grey haze ... hangs over".
4. 00:04.8 is my rewrite verbatim: nape to shoulder blades, head above the top edge, "Two hands with no rings".
   It has no "bare" and no "gloves".
5. 00:06.7 has "the top edge of frame never rises above the collarbone". The hidden hard backlight is gone.
6. 00:07.9 has the embers in the "foreground only", and the skull is "in cool overcast light". Nothing lights the
   print.
7. The trousers and boots line is in the product truth, "the trousers" is in the never-render list, and 00:09.0
   says only "in plain black boots,".
8. All the cuts I listed are in.

## Fixes (numbered; each: where [shot/timestamp or block], the problem, how Seedance will misread it, the exact rewrite)

None I would bet credits on.

Optional, no credit risk either way: "Soft overcast top light" in 00:01.4 and 00:02.4 could become "Soft
overcast light", for the same reason as the global-look cut. Both are macros, so a visible fixture is very
unlikely there. "charcoal-grey" is still in 00:02.4 and 00:03.4. That's harmless; cut it only if you need the
characters.

## Accepted risks (things that may still go wrong, with the post fix or the 4 s insert plan)

- **Empty hoodie stands up or inflates in 00:00.0, 00:01.4 and 00:03.4** (lint WARN). The new worn-hang sentence
  ("the hood stands up round and full over the head") is the one new way for volume to leak into the empty
  shots. It is conditioned on "Worn", and those shots say "empty ... hood folded flat", so I'm not changing it.
  Plan as in round 1: 4 s first-frame inserts for shots 1 and 4, and trim any upright frames.
- **The worn shape from behind drifts** now that there's no worn reference (hood shape, fit, how the skull sits
  under the hood edge in 00:07.9–00:12.0). The text describes it. Check the frames against ref 04 by eye in QA and
  cut the frames that drift.
- **Residual length**: 8,535 characters, 6% over the proven 8,026. If kie refuses it, the request is not charged.
  If the take has no 00:10.2 hero or has captions, the end was dropped; recover with a 4 s hero insert.
- All other round-1 accepted risks stand unchanged: "Avrana" script garbled in 00:06.7, a head entering 00:06.7,
  extra antler points, charcoal instead of black, hands in 00:04.8, stamp compression ±1, embers as flames, the
  locked-off hero reading as frozen (trim it, never slow it), and the budget note.

## Lint output
```
$ python3 scripts/prompt_lint.py ads/avrana/death-glory-12s/prompt-seedance-12s.md --kind seedance --faceless
WARN  ads/avrana/death-glory-12s/prompt-seedance-12s.md  [seedance, 1529 words]
   warn  product lies down ([00:00.0], [00:01.4], [00:03.4]): Seedance stands products upright; use a reference photographed lying down or a first frame where it already lies, and trim upright moments
```
No FAIL. The one WARN is intended and is covered by the insert plan. (Without the flags the lint guesses
`--kind still` and gives a misleading word-count WARN. Always pass `--kind seedance --faceless`.)
