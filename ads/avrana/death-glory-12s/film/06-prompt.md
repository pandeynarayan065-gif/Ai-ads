# 06 Prompt: avrana / death-glory-12s — version 1
- Prompt file: `ads/avrana/death-glory-12s/prompt-seedance-12s.md` (1566 words, 8878 characters; the lint counts 1589)
- Refs in --ref order: Image 1 = `ads/avrana/death-glory-12s/refs/01-death-glory-hoodie-black-front-official.jpg` (hoodie front: cut, hood, pocket, cuffs, hem, colour, chest print; not its pose or volume) ; Image 2 = `ads/avrana/death-glory-12s/refs/02-death-glory-hoodie-black-back-official.jpg` (the antlered skull print only) ; Image 3 = `ads/avrana/death-glory-12s/refs/04-death-glory-hoodie-worn-back-hood-up-official.jpg` (how it hangs worn from behind, hood up; ignore the peach background and the flowers)
- Mode / length / resolution / platform: reference images ; 12 s ; 720p ; kie (the first- and last-frame inserts for shots 1 and 4 are separate requests and are not in this prompt)
- Lint: WARN (`--kind seedance --faceless`, no FAIL)
  - "product lies down (00:00.0, 00:01.4, 00:03.4)": this is on purpose. The storyboard has the hoodie face-down in shots 1, 2 and 4. Each of those shots says it is "empty, no body inside, hood folded flat", and the never-render list bans an empty hoodie that stands up or inflates. Shots 1 and 4 are planned as separate 4 s first-frame inserts. Any upright frames get trimmed in the edit. Ref 05 (lying flat) stays out of the run because of its skateboard, cup and hard sun.

## Changes in this version (from reality-check round N, numbered to match its fixes)
Version 1. No reality check has run yet. Director notes carried in (04-director.md):
1. Shot 1 does not mention the chest script. The script appears only in the product-truth block, which has to be the product lock word for word. The product truth also adds "The back carries the skull print only, with no lettering", and the never-render list has "any lettering on the back of the hoodie".
2. Shot 4 says "veil of charcoal-grey ash" (twice). The word "dust" appears nowhere in the prompt.

Other decisions (one line each):
- The product name "Death & Glory" is left out of the prompt. The model doesn't need it, and "death" could trip a filter. The hoodie is "the Avrana black hoodie".
- The product lock gives no size, so one scale sentence follows the lock block: adult hoodie at true size, the hem at the hips as in Image 3, a whole hand fits in the pocket.
- "No drawstrings, no zip and no other logos" matches the refs but is still [VERIFY] on the real garment (product lock).
- Shot 4 says "four points on each antler, exactly as in Image 2". It follows the DoP's "exactly 4" without contradicting the lock's "about four".
- Shot 7 crops at the collarbone and never says "headless". In shot 9, "Handheld camera follows the person" is a single move. The lint checks the last shot for slow motion, so "no slow motion" sits in the real-photography block instead.
- At 8878 characters it is longer than the longest proven prompt (Spraymax cinematic, 8026). We know of no kie length limit. Each shot is 71–90 words; the last block is 108 words including the Throughout line.

## Storyboard → prompt map (shot # → timestamp)
| Shot | Timestamp | Dur (s) | Prompt beat |
|---|---|---|---|
| 1 | [00:00.0] | 1.4 | Top-down, empty hoodie drops face-down into ash, ash veil falls back; locked-off |
| 2 | [00:01.4] | 1.0 | Macro printed antler tip, flakes settle; drifts slowly to the right |
| 3 | [00:02.4] | 1.0 | Real bleached antler on burnt earth, no hoodie; pushes in slowly |
| 4 | [00:03.4] | 1.4 | Near top-down, gust blows the veil of charcoal-grey ash off, skull clear; pushes in slowly |
| 5 | [00:04.8] | 1.0 | From behind, bare hands pull the hood up, never over the print; locked-off |
| 6 | [00:05.8] | 0.9 | Macro cuff and hem, gust bounces ash grains; locked-off |
| 7 | [00:06.7] | 1.2 | Front, collarbone to hem, walks out of white smoke, chest print sharpens; pushes in slowly |
| 8 | [00:07.9] | 1.1 | From behind, one stop darker, foreground embers, warm edge on skull; drifts slowly to the left |
| 9 | [00:09.0] | 1.2 | Low from behind, climbs ash slope, plain boots; handheld follow |
| 10 | [00:10.2] | 1.8 | Wide hero, left of centre on ridge, right 60% empty sky; locked-off, real time to the end |
