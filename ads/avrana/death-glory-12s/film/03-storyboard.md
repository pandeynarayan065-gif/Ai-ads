# 03 Storyboard: avrana / death-glory-12s — 12 s, 10 shots
| # | Time | Dur (s) | Framing | Subject | One action | One camera move | Cut out | Product in frame (view, size, upright/lying, print readable?) | Beat / job |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.0 | 1.4 | Top-down wide | Empty black hoodie, no body inside, hood folded flat, on charcoal-grey ash | Hoodie drops from above frame and lands face-down, back up; ash ring bursts out, then falls back as a thin veil over the skull | Locked-off | Hard cut as the veil settles | Back, whole garment, LYING flat face-down, mid-size; skull faint under ash veil, outline only; do not rely on the script reading | Hook: product at once |
| 2 | 00:01.4 | 1.0 | Extreme macro | Tip of one printed antler on the lying back, cracked-matte white on black fleece | Grey flakes settle on the antler tip | Drift right | Cut on the match from printed antler to real antler | Back, about 5% of garment, LYING, no letters in frame, antler tip only | Texture |
| 3 | 00:02.4 | 1.0 | Low macro | Bleached plain antler on burnt ground (no product) | Wind lifts ash grains past the antler | Push in | Cut on grain pass | No product; antler only, no skull | Product-truth echo |
| 4 | 00:03.4 | 1.4 | High-angle close, looking almost straight down | Empty hoodie, face-down, back up, in ash, lying flat, hood folded flat | Steady gust from frame left blows the veil of dust off; white skull comes clear | Slow push in | Cut when skull is clear | Back, skull about 70% of frame, LYING face-down back up, print must read (outline, 4 points per antler) | Product truth / escalation |
| 5 | 00:04.8 | 1.0 | Close, behind, shoulder height | Faceless figure, ribbed cuffs | Two hands in the cuffs pull the hood up; ash drifts | Locked-off | Cut on hood settling | Back, upper half, upright worn; skull partly hidden by hood, hands never cross print, no rings | Use |
| 6 | 00:05.8 | 0.9 | Macro | Ribbed cuff and hem | Gust bounces ash grains off the fleece | Locked-off | Cut on gust peak | Cuff and hem only, upright worn, no print in frame | Texture |
| 7 | 00:06.7 | 1.2 | Medium, top of frame at the collarbone, hood up, head out of frame | Faceless figure in white smoke walking toward camera | Walks forward out of the smoke as it thins | Push in slowly | Cut on print sharpening | Front, collarbone to hem, upright worn, chest print grows as figure nears; filigree reads, script may not (cut if garbled) | Escalation |
| 8 | 00:07.9 | 1.1 | Medium-wide, same burnt ground, low grey overcast but darker | Figure from behind about 3 m back; out-of-focus embers rising from smouldering ground in foreground | Embers drift up; figure stands still; embers light the skull warm from low at the side | Drift left | Cut as embers cross frame | Back, upright worn, hood up, mid-size, reads as skull shape; embers never touch the garment | Escalation, one warm accent |
| 9 | 00:09.0 | 1.2 | Low follow, from behind | Hooded figure on grey ash slope, plain black boots | Climbs, steps kick up puffs, hem moves in wind | Handheld follow | Cut on a step | Back, upright worn, about 40% of frame, skull should read | Use |
| 10 | 00:10.2 | 1.8 | Wide | Figure left of centre on burnt ridge, right 60% empty grey sky | Stands still; ash drifts | Locked-off, real time | End | Back, upright worn, hood up, small to mid in frame, skull reads, about 3 m | Hero; tagline space |

## Shots needing special handling (lying product, first-frame remake, blank surfaces, people)
- **Run plan**: the 12 s run is reference images only (`--ref`): Image 1 = ref 01, Image 2 = ref 02, Image 3 = ref 04. No first frame in the run. Shot 1 is written in words inside the run.
- **Refs**: Image 1 and 2 for print, colour and cut only, not pose or volume (ghost-mannequin photos with hollow bodies). Image 3 (ref 04): use only for how the hoodie hangs worn from behind, hood up; ignore the peach background and the flowers.
- Shots 1, 2, 4: product LYING. Board and prompt it as "empty, lying flat on the ash, no body inside, hood folded flat" or the model inflates or stands it up. Trim any upright frames in the edit. Shot 4 is a top-down view, face-down, back up (matches Image 2's flat view), not a grazing angle.
- **Separate 4 s inserts, cut in after the run** (each its own request: no `--ref`, `--aspect adaptive`, 9:16 stills prepared first). Prepared still = hoodie face-down on charcoal-grey ash, top-down, flat overcast, skull from ref 02 under a thin ash veil, outline faint; ref 05 only a guide to fabric folds (ref 05 itself is NOT a usable first frame: hard sun, skateboard, cup, 45 deg, square). Also make the same still with the hoodie removed (empty ash plate).
  - Shot 1 insert: first frame = ash plate, last frame = prepared still, so the drop survives.
  - Shot 4 insert: first frame = prepared still; the gust clears the veil.
- Blank surfaces: shot 2 antler tip only, no letters. Shot 7 chest script is the fake-text risk; cut, not fix. Shot 1 script too small to read (about 120 px at 720p): never rely on it.
- Shots 4 and 8-10: skull must match ref 02 (shaded distressed engraving, about 4 points per antler). Check every frame for extra points.
- People: all faceless (hood up, from behind, cropped, hands only). Shot 5 hands under 1 s, no rings, never over the print. Shot 7: top of frame at collarbone, push in (a pull-back would show the head); do not write "headless"; backup is a POV swap (research idea 11). Boots plain, no logos.
- Shot 8: embers never land on the hoodie, hoodie never burns. Shot 3 has no product, no skull.
- No drawstrings, zip or extra logos [VERIFY on real garment].

## Continuity notes (things that must match across cuts)
- Palette: black, ash grey, bone white; ember orange only in shot 8. Flat low grey overcast throughout (shot 8 darker, with warm low side glow from embers), backlit shot 7. No night anywhere.
- Same ash (charcoal-grey flakes, not snow) and same burnt ground in shots 1-10. Wind from frame left in 4; drift continues.
- Hoodie lands face-down in shot 1 and is face-down in shot 4 in the same ash (veil from shot 1 is what the gust clears in 4). Chest print gets its moment in shot 7.
- Printed antler (shot 2) matches to the real bleached antler (shot 3); push-ins in 3 and 4 read as one gesture into the reveal.
- Same hoodie in every shot: matte black fleece, ribbed cuffs and hem, same skull and filigree prints.
- Same faceless figure build and outfit from shot 5 on; hood up from shot 5 onward, including shot 7.
- Real time throughout, no slow-mo. Last 1.8 s hero is locked-off with clean empty sky on the right for "Create Yourself" and avrana.co (post).
