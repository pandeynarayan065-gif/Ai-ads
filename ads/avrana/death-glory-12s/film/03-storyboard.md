# 03 Storyboard: avrana / death-glory-12s — 12 s, 10 shots
| # | Time | Dur (s) | Framing | Subject | One action | One camera move | Cut out | Product in frame (view, size, upright/lying, print readable?) | Beat / job |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.0 | 1.4 | Top-down wide | Black hoodie on charcoal-grey ash | Hoodie drops from above frame, lands flat; ash ring puffs out | Locked-off | Hard cut on the puff | Front, whole garment, LYING flat, chest print up, mid-size; print need not read, filigree shape only | Hook: product at once |
| 2 | 00:01.4 | 1.0 | Extreme macro | One corner of chest filigree, cracked-matte white on black fleece | Grey flakes settle on the print | Drift right | Cut to low scale change | Front, about 5% of garment, lying, blank (no letters in frame, filigree only) | Texture |
| 3 | 00:02.4 | 1.0 | Low macro | Bleached plain antler on burnt ground (no product) | Wind lifts ash grains past the antler | Push in | Cut on grain pass | No product; antler only, no skull | Product-truth echo |
| 4 | 00:03.4 | 1.4 | Low macro, across the back | Hoodie back, face-down in ash | Steady gust from frame left blows dust off, white skull comes clear | Slow push in | Cut when skull is clear | Back, skull fills about 70% of frame, LYING face-down, print must read (outline, 4 points per antler) | Product truth / escalation |
| 5 | 00:04.8 | 1.0 | Close, behind, shoulder height | Faceless figure, ribbed cuffs | Two hands in the cuffs pull the hood up; ash drifts | Locked-off | Cut on hood settling | Back, upper half, upright worn; skull partly hidden by hood, hands never cross print, no rings | Use |
| 6 | 00:05.8 | 0.9 | Macro | Ribbed cuff and hem | Gust bounces ash grains off the fleece | Locked-off | Cut on gust peak | Cuff and hem only, upright worn, no print in frame | Texture |
| 7 | 00:06.7 | 1.2 | Medium, chest height, cropped at shoulders | Headless figure in white smoke | Walks forward out of the smoke as it thins | Slow pull back | Cut on print sharpening | Front, chest to hem, upright worn, chest print about chest-wide, backlit; filigree reads, script may not (cut if garbled) | Escalation |
| 8 | 00:07.9 | 1.1 | Medium-wide, night rooftop | Figure from behind about 3 m away; blurred orange embers in foreground | Embers drift up; figure stands still | Drift left | Cut as embers cross frame | Back, upright worn, hood up, skull lit by warm side glow, mid-size, reads as skull shape; embers never touch the garment | Escalation, one warm accent |
| 9 | 00:09.0 | 1.2 | Low follow, from behind | Hooded figure on grey ash slope, plain black boots | Climbs, steps kick up puffs, hem moves in wind | Handheld follow | Cut on a step | Back, upright worn, about 40% of frame, skull should read | Use |
| 10 | 00:10.2 | 1.8 | Wide | Figure left of centre on burnt ridge, right 60% empty grey sky | Stands still; ash drifts | Locked-off, real time | End | Back, upright worn, hood up, small to mid in frame, skull reads, about 3 m | Hero; tagline space |

## Shots needing special handling (lying product, first-frame remake, blank surfaces, people)
- Shots 1, 2, 4: product LYING. Seedance stands products up. Use ref 05 (lying flat, ignore skateboard and cup) as first frame for 1; fallback is a 4 s first-frame insert (`--aspect adaptive`). Shot 4 needs a back-down lying view: no ref exists, so flag a first-frame remake (flip of ref 02 on ash) if it stands up. Ref 05 stays out of the `--ref` set per story; use it only as a first frame.
- Blank surfaces: shot 2 filigree only, no letters. Shot 7 chest script is the fake-text risk; cut, not fix.
- Shot 4 and shots 8-10: skull must match ref 02 (shaded distressed engraving, about 4 points per antler). Check every frame for extra points.
- People: all faceless (hood up, from behind, cropped, hands only). Shot 5 hands under 1 s, no rings, never over the print. Shot 7 face leak: swap to POV (research idea 11). Boots plain, no logos.
- Shot 8: embers never land on the hoodie, hoodie never burns. Shot 3 has no product, no skull.
- No drawstrings, zip or extra logos [VERIFY on real garment].
- Refs: Image 1 = ref 01, Image 2 = ref 02, Image 3 = ref 04.

## Continuity notes (things that must match across cuts)
- Palette: black, ash grey, bone white; ember orange only in shot 8. Overcast flat light except shot 8 (night, warm side glow) and backlit shot 7.
- Same ash (charcoal-grey flakes, not snow) in shots 1-6, 9-10. Same wind direction (from frame left in 4; drift continues).
- Same hoodie in every shot: matte black fleece, ribbed cuffs and hem, same skull and filigree prints.
- Same faceless figure build and outfit from shot 5 on; hood up from shot 5 onward (shot 7 may be hood down only if no head shown; prefer hood up).
- Real time throughout, no slow-mo. Last 1.8 s hero is locked-off with clean empty sky on the right for "Create Yourself" and avrana.co (post).
