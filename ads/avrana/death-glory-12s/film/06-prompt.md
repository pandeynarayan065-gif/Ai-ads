# 06 Prompt: avrana / death-glory-12s — version 2
- Prompt file: `ads/avrana/death-glory-12s/prompt-seedance-12s.md` (1507 words, 8535 characters; the lint counts 1529)
- Refs in --ref order: Image 1 = `ads/avrana/death-glory-12s/refs/01-death-glory-hoodie-black-front-official.jpg` (hoodie front: cut, hood, pocket, cuffs, hem, colour, chest print; not its pose or volume) ; Image 2 = `ads/avrana/death-glory-12s/refs/02-death-glory-hoodie-black-back-official.jpg` (the antlered skull print only). No Image 3: ref 04 is out of the run (fix 1).
- Mode / length / resolution / platform: reference images ; 12 s ; 720p ; kie (the first-frame inserts for shots 1 and 4 are separate requests and are not in this prompt)
- Lint: WARN (`--kind seedance --faceless`, no FAIL)
  - "product lies down (00:00.0, 00:01.4, 00:03.4)": on purpose, as in version 1. Shots 1, 2 and 4 say "empty, no body inside, hood folded flat", the never-render list bans an empty hoodie that stands up or inflates, shots 1 and 4 have 4 s first-frame inserts planned, and upright frames get trimmed.

## Changes in this version (from reality-check round 1, numbered to match its fixes)
1. Asset mapping: Image 3 (ref 04, peach wall and roses) is dropped, not cleaned. Every Image 3 mention is gone, including "as in Image 3" in the scale sentence. The worn look is now in words in the product truth, after the scale sentence: "Worn and seen from behind with the hood up, it hangs loose and relaxed: the hood stands up round and full over the head, its lower edge resting on the upper back just above the antler tips; the shoulders drop slightly; the body falls straight in soft vertical folds to the hem; the sleeves hang loose and bunch a little above the cuffs." (I read this from ref 04.) The `--ref` list is now Image 1 and Image 2 only.
2. Real photography: cut "real white smoke, real embers" and the true-size sentence. It now ends "real wind from frame left. Natural film grain…".
3. 00:00.0: "drops into frame from above" → "falls straight down away from the lens". The ash veil that fell back is now "a thin grey haze of it hangs over the hoodie".
4. 00:04.8: the whole shot is the report's rewrite. The frame runs from the nape to the shoulder blades and the head stays above the top edge. "Two hands with no rings" lift the hood out of the top of frame. "bare" is gone and there is no "gloves".
5. 00:06.7: added "the top edge of frame never rises above the collarbone". The hidden hard backlight is now "the smoke behind them bright, even grey-white in the overcast daylight".
6. 00:07.9: the ember glow no longer edges the skull. The embers rise "through the foreground only; the person and the skull print stay in cool overcast light".
7. Product truth ends with the same adult in every shot, in plain matte black trousers and plain black boots, with no logos, labels or print. "the trousers" is added to the never-render list. 00:09.0 now says only "in plain black boots,".
8. Length: every cut the report listed is in: summary, lens and rig list, fleece and ash wording, "vertical 9:16", "top light" in the global look, the drawstring and zip line in the never-render list, "one twentieth", the tine sentence in 00:02.4, and the charcoal-grey and veil repeats in 00:00.0, 00:01.4, 00:03.4, 00:05.8 and 00:10.2. The report's Image 3 trim is moot after fix 1. The prompt went from 8,878 to 8,535 characters, which is 162 more than the report's 8,373 because the worn-hang sentence replaces Image 3. That is 6% over the proven 8,026 (accepted risk "Residual length").
- Nothing else changed. I put back "official product photo" for Image 2, because the scratch draft had dropped "product" and no fix asked for that.

## Storyboard → prompt map (shot # → timestamp)
| Shot | Timestamp | Dur (s) | Prompt beat |
|---|---|---|---|
| 1 | [00:00.0] | 1.4 | Top-down, the empty hoodie falls away from the lens face-down into ash, a thin ash haze hangs over it; locked-off |
| 2 | [00:01.4] | 1.0 | Macro of a printed antler tip, flakes settle; drifts slowly to the right |
| 3 | [00:02.4] | 1.0 | A real bleached antler on burnt earth, no hoodie; pushes in slowly |
| 4 | [00:03.4] | 1.4 | Near top-down, a gust blows the ash veil off and the skull comes clear; pushes in slowly |
| 5 | [00:04.8] | 1.0 | From behind, nape to shoulder blades, hands lift the hood out of the top of frame, never over the print; locked-off |
| 6 | [00:05.8] | 0.9 | Macro of cuff and hem, a gust bounces ash grains; locked-off |
| 7 | [00:06.7] | 1.2 | Front, collarbone to hem, walks out of even grey-white smoke, the chest print sharpens; pushes in slowly |
| 8 | [00:07.9] | 1.1 | From behind, one stop darker, embers in the foreground only, skull in cool light; drifts slowly to the left |
| 9 | [00:09.0] | 1.2 | Low from behind, climbs an ash slope in plain black boots; handheld follow |
| 10 | [00:10.2] | 1.8 | Wide hero, left of centre on the ridge, right 60% empty sky; locked-off, real time to the end |
