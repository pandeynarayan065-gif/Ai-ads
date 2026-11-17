# 07 Reality check, round 1: prompt-seedance-12s.md (version 1)
## Verdict: FAIL

No lint FAIL. Eight fixes I would bet credits on. All are text edits except fix 1, which needs a cleaned copy of
ref 04 and costs no credits. With all eight applied, the prompt is 8,373 characters and 1,480 words (lint 1,502).
The lint result stays the same: WARN, only the intended "product lies down".

## Fixes (numbered; each: where [shot/timestamp or block], the problem, how Seedance will misread it, the exact rewrite)

1. **[Asset mapping, Image 3 = refs/04]** Ref 04 has a strong peach wall and a bank of coloured roses on both
   sides, touching the arms. Shots 8, 9 and 10 use the same view (from behind, hood up, skull centred). Seedance
   pastes a reference whose view matches, so expect a peach cast, flowers or a warm backdrop in the cold hero.
   The film's only warm accent belongs in shot 8. "Ignore its peach background and the flowers" is not enough;
   this is the "reference it will paste" failure.
   **Rewrite:** before the run, make `refs/04b-death-glory-hoodie-worn-back-hood-up-clean.jpg`. Keep the figure
   and hoodie pixel for pixel and fill everything else flat white, like Images 1 and 2. The hoodie is dark and
   low-saturation, so a mask works: dark + low saturation, keep the largest region, fill its holes (the print).
   Then crop to the figure. Pass that file as Image 3 and change "ignore its peach background and the flowers." →
   "ignore its white background." If the clean ref is not made, drop Image 3 entirely; don't send ref 04 as it is.

2. **[Real-photography block]** "real white smoke, real embers" sit in a block that says "inherited by every
   shot". Seedance follows this literally, so smoke and orange embers leak into other shots, and the "one warm
   accent only" rule breaks. Smoke and embers are already written into 00:06.7 and 00:07.9.
   **Rewrite:** "real wind from frame left, real white smoke, real embers. The hoodie is a real garment,
   physically placed and shot at its true size. Natural" → "real wind from frame left. Natural". The deleted
   size sentence repeats the product-truth scale line.

3. **[00:00.0]** (a) "drops into frame from above" with a camera "directly overhead": Seedance reads "from above"
   as the top edge of the frame. The hoodie then slides down the screen across a ground seen from overhead,
   which is impossible. A real drop seen from an overhead rig falls away from the lens and shrinks. (b) "bursts
   outward, then falls back over the hoodie as a thin grey veil" chains two events in 1.4 s, and ash does not
   settle into an even veil that fast. Seedance either skips the drop or buries the hoodie and blurs the skull.
   **Rewrite:** "drops into frame from above and lands lying flat face-down" → "falls straight down away from the
   lens and lands lying flat face-down"; and "On impact a ring of ash bursts outward, then falls back over the
   hoodie as a thin grey veil, the skull print only a faint outline beneath it." → "On impact a ring of ash bursts
   outward and a thin grey haze of it hangs over the hoodie, the skull print only a faint outline beneath it."

4. **[00:04.8]** With the hood lowered and the head in frame, the back of the head, hair and ears are visible.
   People who reach back with both arms turn their heads, so a cheek or profile is likely, which is a zero on QA
   line 7. "bare hands" is also a needless skin word.
   **Rewrite (whole shot):** "[00:04.8] Close shot at shoulder height on a person wearing <Subject 1>, seen only
   from behind: the frame runs from the nape of the neck down to the shoulder blades, and the head stays above
   the top edge of frame. The lowered hood covers the top of the skull print. Soft overcast light from above; ash
   drifts through the frame on the wind. Two hands with no rings, wrists in the ribbed black cuffs, grip the
   hood's side edges and lift it up out of the top of frame, never crossing the print. Camera locked-off."
   Don't write "no gloves": the lint flags "gloves" as a print surface.

5. **[00:06.7]** (a) "backlit by a hard low light whose source stays hidden in the smoke" makes god rays, a
   glowing halo and flares in thick smoke. All three are on the never-render list, and they break the global
   "flat... overcast... no hard shadows in every shot". (b) "framed from the collarbone down" with a push-in and
   a subject walking closer: Seedance likes to reframe up to find a head. This is the only front-facing person in
   the film.
   **Rewrite:** "framed from the collarbone down to the hem, so the head and face are never in frame;" → "framed
   from the collarbone down to the hem; the top edge of frame never rises above the collarbone, so the head and
   face are never in frame;". Also "backlit by a hard low light whose source stays hidden in the smoke behind
   them, with soft grey daylight on the front." → "the smoke behind them bright, even grey-white in the overcast
   daylight, with soft grey daylight on the front."

6. **[00:07.9]** "their faint warm glow from low frame right edges the skull print": this fails the real-crew
   test. A few embers near the lens can't light a print three metres away in daylight. To make it happen,
   Seedance will add a fire or glowing ground next to the wearer, move the embers onto the hoodie, or tint the
   skull orange. Those break "never touch the hoodie", "flames" and the bone-white print.
   **Rewrite:** "Out-of-focus orange embers from smouldering ground near the lens climb through the foreground and
   never touch the hoodie; their faint warm glow from low frame right edges the skull print, the only warm colour
   in the film." → "Out-of-focus orange embers from smouldering ground beside the lens climb through the
   foreground only; the person and the skull print stay in cool overcast light, and the embers are the only warm
   colour in the film."

7. **[Product truth, last line; never-render list; 00:09.0]** The wearer's lower half shows in shots 7, 9 and
   10, but trousers are never mentioned, and the build isn't fixed from shot 5 on. Seedance will invent
   trousers: cargo pants with logo patches, printed joggers, ripped jeans with skin showing, or shorts. That
   means fake text and other brands, and the body may change between shots.
   **Rewrite:** after "It has no drawstrings, no zip and no other logos." add "The wearer is the same adult in
   every shot, in plain matte black trousers and plain black boots, with no logos, labels or print on either."
   In the never-render list, "including on the boots, the ground and the sky;" → "including on the boots, the
   trousers, the ground and the sky;". In 00:09.0, "in plain black boots with no logos," → "in plain black
   boots,".

8. **[Whole prompt: length]** The prompt is 8,878 characters and 1,566 words. The longest proven prompt is
   8,026 (Spraymax), and this preamble (730 words) is longer than any proven one (494–665). We don't know kie's
   limit or how Seedance handles a long text. If anything gets dropped or truncated, it is the end: the hero shot
   and the Throughout line. The cuts below are all repeats or words the model can't use:
   - Summary paragraph → "A 12-second vertical streetwear film for the Avrana black hoodie: the empty hoodie
     falls face-down into ash, the wind clears its skull print, and a faceless wearer walks out of smoke and
     climbs to a burnt ridge." (The palette and the "cold world" are already in the global look.)
   - Real photography: "with 100 mm macro, 50 mm, 35 mm and 24 mm prime lenses, on tripods, sliders and an
     overhead rig," → "with macro and prime lenses,". Naming rigs invites visible gear. Also "Real matte
     cotton-look fleece with real weight and real folds, real matte screen print, real dry charcoal-grey wood
     ash" → "Real matte fleece with real weight and folds, real matte screen print, real dry wood ash".
   - Global look: delete "vertical 9:16, ". Change "Flat low grey overcast daylight, a large soft top light with
     no hard shadows, in every shot." → "Flat low grey overcast daylight with no hard shadows in every shot."
     "Top light" can come out as a visible fixture.
   - Never render: delete "drawstrings, a zip or extra logos on the hoodie; ". The product truth already says
     it. Keep the director's "any lettering on the back of the hoodie".
   - Asset mapping: "Use Image 3 only for how the hoodie hangs on a body seen from behind with the hood up;" →
     "Use Image 3 only for how it hangs on a body;".
   - 00:01.4: delete ", about one twentieth of the garment visible". One twentieth of a hoodie is a palm-sized
     patch, which contradicts "only the tip of one printed antler" and pulls the frame out to the whole skull.
     Change "Fine charcoal-grey ash flakes" → "Fine ash flakes".
   - 00:02.4: delete ", its tine curving the same way as the printed antler tip". The model can't see across
     cuts.
   - 00:00.0: "a flat bed of dry charcoal-grey wood ash" → "a flat bed of charcoal-grey ash".
   - 00:03.4: "Even overcast top light." → "Even overcast light."; "blows the veil of charcoal-grey ash off the
     back" → "blows the ash veil off the back".
   - 00:05.8: "and charcoal-grey ash grains bounce" → "and ash grains bounce". 00:10.2: "Charcoal-grey ash drifts
     past" → "Ash drifts past".
   - Result with fixes 1–8: 8,373 characters. Still 4% over the proven maximum; see accepted risks.

## Accepted risks (things that may still go wrong, with the post fix or the 4 s insert plan)

- **Hoodie stands up or inflates in 00:00.0, 00:01.4 and 00:03.4** (lint WARN; no lying reference, and ref 05 is
  rightly excluded). Plan as boarded: separate 4 s first-frame inserts for shots 1 and 4 (`--aspect adaptive`, no
  `--ref`, prepared ash-plate and face-down stills; 480p is 112 cr each, upscaled). Trim any upright frames in the
  run. Shot 2 is a macro, so a wrong pose barely shows.
- **"Avrana" script garbled in 00:06.7**: the chest print sharpens as the wearer approaches. Use the frames where
  smoke still softens the script, or cut before it is sharp. No pasted fix (Narayan rejected pasted labels on
  moving shots). The backup is the POV swap from the storyboard.
- **A head enters the frame in 00:06.7** despite fix 5. Use only the frames before it. If the usable range is
  under 0.6 s, swap in the POV backup.
- **Skull drawn with extra antler points or as a cartoon** (00:03.4, 00:07.9–00:12.0). Check every frame against
  Image 2; cut the drifting frames. The hero can be trimmed to 1.2 s.
- **Hoodie reads charcoal instead of black** (ref 04's garment is washed-looking). Use one fixed grade per shot in
  post, no masks.
- **Hands in 00:04.8** look off or cross the print. Keep under 1 s and cut on the hood leaving the frame.
- **Stamp compression**: 10 stamps may give 9 cuts. Expect ±1, as in every 12 s run.
- **Embers render as flames or land on the hoodie** in 00:07.9. They are on the never-render list. Cut the shot,
  or use a 4 s insert from a first frame with the embers only in the foreground.
- **Locked-off hero reads as frozen** (1.8 s, a still figure). Ash drift gives motion. If it still reads frozen,
  trim to 1.2 s; never slow it.
- **Residual length** (8,373 vs the proven 8,026). If kie refuses it, the request is uncharged. Check the take for
  a missing 00:10.2 hero or for captions (those would mean the end got dropped), and recover with a 4 s hero insert.
- **Budget**: 159 credits against 756 for a 12 s 720p run. The brief says this test spends no credits.

## Lint output
```
$ python3 scripts/prompt_lint.py ads/avrana/death-glory-12s/prompt-seedance-12s.md --kind seedance --faceless
WARN  ads/avrana/death-glory-12s/prompt-seedance-12s.md  [seedance, 1589 words]
   warn  product lies down ([00:00.0], [00:01.4], [00:03.4]): Seedance stands products upright; use a reference photographed lying down or a first frame where it already lies, and trim upright moments
```
No FAIL. The one WARN is intended and is covered by the insert plan above. Linting a draft with fixes 1–8
applied gives the same single WARN, at 1,502 lint words.
