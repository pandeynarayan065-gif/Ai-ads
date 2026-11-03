# Higgsfield: Seedance 2.5 luxury product film (Ex Nihilo "Blue Talisman")

**Source:** Higgsfield promo reel ("Comment BLUE for a Seedance 2.5 guide…"), sent by Narayan on 2026-11-02.
The reel shows the product sheet, the prompt (scrolling) and the result. 16:9 output, about 13 cuts in
roughly 15 s of footage. The prompt's timestamps run to 22.4 s, so either the generation was about 24 s or the
reel speeds it up. That's unconfirmed.

**What it is:** one Seedance 2.5 reference-to-video generation. The inputs are one product reference sheet
(`@sheet`) and one long timestamped prompt. The output is a multi-shot luxury fragrance film: product macros
alternate with ingredient macros, then a packshot ends it.

**Our adaptation:** `ads/spraymax/seedance/prompt-seedance-15s.md` (+ `product-sheet.jpg`, `settings.md`).

## Why it works (the structure to reuse)

1. **Product truth first.** "Use @sheet as the absolute visual truth for the product in every shot", then
   every physical feature, including the printed text on the label, then "The product is identical in every
   shot."
2. **Hard cuts only.** Stated as a rule: no transitions, dissolves, wipes or fades, and no motion carried
   across a cut. This stops the model blending shots into a morph.
3. **One global look paragraph**, so every shot inherits it:
   - low-key, one hard light per shot;
   - **~80% black negative space**;
   - cold light only, with **exactly one warm accent** (the gold cap);
   - "soft where it blooms, hard where it strikes";
   - framing deliberately alternating extreme macro (product cropped, partly readable) with wide (product
     small in a black field).
4. **A "Never render" list aimed at the usual AI tells:**
   - glossy, mirrored or wet floors and reflections of the bottle;
   - visible light fixtures (neon tubes, LED rings, hoops, strips, softboxes);
   - a glowing halo or aura behind the product;
   - lens flares;
   - "the bottle centred and fully lit in every shot".
5. **Timed shots, one moment each,** about 1.2–1.6 s apart in `[mm:ss.s]` stamps. Every shot has framing,
   subject, light (source, direction, quality) and **one camera move** (push in, creep and rise, micro drift,
   lateral drift, locked still, orbit slightly).
6. **Rhythm:** product → product → ingredient → ingredient → product → product macro → ingredient → liquid →
   abstract (glass ridges, "product unreadable") → product with ingredient → product angle → 3 ingredient
   macros → product hero → vapour → packshot.
7. **The ending:** a wide packshot, product left of centre, a long hard grounding shadow, and the empty half
   of the frame left for the logo.
8. **The closing style line:** "Cinematic, photorealistic, luxury fragrance campaign. [palette]. [the one warm
   accent]. No distortion. Maintain product proportions."

## The cut, measured (2026-11-03)

Film panel cropped out of the reel (x 72-647, y 231-663 of the 720x1280 screen recording), cuts found by frame
differencing and camera moves by optical flow (Farneback; % = share of frame width per second). 17 hard cuts in
~12.6 s, then a ~4 s packshot that fades out.

| # | t (s) | Shot | Measured move |
|---|---|---|---|
| 1 | 0.00-1.40 | Gold cap ECU, a key sweeps across the lattice | push-in, zoom 7%/s |
| 2 | 1.40-2.07 | Citrus peels on blue, mist | drift, 7.5%/s |
| 3 | 2.07-2.73 | White blossom centred in black | drift left to right, 6.6%/s |
| 4 | 2.73-3.33 | Cap standing in the blossom's heart | push-in, 4.8%/s |
| 5 | 3.33-4.10 | Blue smoke curl, wave-like | the smoke moves (13%/s) |
| 6 | 4.10-5.33 | Flacon, sapphire bloom rising behind | push-in, 3.3%/s |
| 7 | 5.33-6.67 | Macro of the base, EAU DE PARFUM | push-in 5.3%/s, slight tilt |
| 8 | 6.67-7.33 | Liquid strand, a droplet travelling | the drop moves; camera locked |
| 9 | 7.33-7.97 | Fast rack across the glass ridges (streaks) | fast lateral, 14%/s |
| 10 | 7.97-8.67 | Flacon near-silhouette | creep in and rise |
| 11 | 8.67-9.33 | Wood shards, light through the gaps | lateral, 12.7%/s |
| 12 | 9.33-10.00 | Tighter on the shards | lateral, same direction, 14%/s |
| 13 | 10.00-10.63 | Pear skin with dew | still |
| 14 | 10.63-11.33 | High three-quarter on the cap | still (slight orbit) |
| 15 | 11.33-12.00 | Wood grain | diagonal drift, 10%/s |
| 16 | 12.00-12.63 | Vapour cloud | drift |
| 17 | 12.63-16.67 | Packshot with the logo lockup | near-still push, then fade |

**What makes it read as luxury:**
- The pace: 0.6-0.7 s cuts in the middle, longer at the open (1.4 s) and the close (4 s).
- Every shot moves, and each move is one of a small set: push-in, lateral drift, rise, fast rack.
- Consecutive cuts that carry the same direction (11-12) feel like one gesture.

Our version: `ads/spraymax/cinematic-12s/` (storyboard v3, `build_animatic.py`).

## The prompt, verbatim (transcribed from the reel)

```
Use @sheet as the absolute visual truth for the product in every shot: the flacon's silhouette and depth, the deep sapphire to clear vertical gradient, the champagne gold woven lattice cap and polished collar, and the fine white printing on the front face (the EX NIHILO hexagon mark, PARIS, BLUE TALISMAN, EAU DE PARFUM and the thin geometric line motifs). The product is identical in every shot.

Hard cuts only throughout: every shot is a completely separate camera setup. No transitions, no dissolves, no wipes, no fades, no continuous motion carrying across a cut.

Global look: deep low-key, one hard light source per shot, roughly eighty percent black negative space in every frame. Cold light only, icy blue and silver-white, with the champagne gold cap the only warm-toned element in the film. Light is always soft and unfocused where it blooms and hard and raking where it strikes. Framing alternates deliberately between extreme macro where the flacon is cropped and only partly readable, and wide where it sits small in a large black field.

Never render: a glossy, reflective, wet or mirrored floor; a reflection of the bottle in the ground; a visible light fixture of any kind, including neon tubes, LED rings, hoops, strips, lamps or softboxes; a glowing halo or aura directly behind the product; lens flares; the bottle centred and fully lit in every shot.

[00:00.0] Extreme close-up of the champagne gold woven lattice cap filling roughly half the frame against pure black. Camera pushes in slowly while a hard cool white key sweeps left to right across the crosshatch, igniting the gold strands band by band, the left side of the cap staying in near-total shadow.

[00:01.6] Low three-quarter from the front left, the flacon in near-silhouette against black, one hard silver specular blade running down its front vertical edge and nothing else lit. Camera creeps in and rises toward the gold collar, a faint cool bounce pooling in the thick clear base.

[00:02.8] Extreme macro of a bergamot peel and a mandarin peel twisted together, a fine burst of citrus oil misting off the fold, backlit cold blue against black so the mist catches the light. Camera holds nearly still with a micro drift as the mist expands.

[00:04.0] Medium macro of a single white orange blossom in full bloom, petals fanning open, hard backlight from behind and below rimming the petal edges silver against black. Camera drifts laterally left to right, the bloom entering in shadow, peaking at centre, exiting into darkness at the right.

[00:05.3] The flacon standing in a black void, a broad unfocused wash of sapphire light blooming behind it from an unseen source, no visible fixture and no hard edge to the light. Camera pushes in slowly as the wash rises, the light passing through the gradient so the upper glass reads deep sapphire and the clear base reads luminous ice.

[00:06.6] Macro, the push-in continuing into the thick clear base, the EAU DE PARFUM line and the base bevels magnified until they fill the frame, the sapphire wash refracting through the glass into cold vertical streaks.

[00:07.7] Extreme macro of ripe pear skin, its speckled surface scattered with fine dew droplets holding tiny silver catchlights, cool soft key from above. Camera drifts slowly as the light falls away toward black.

[00:09.0] Extreme macro, camera locked still. A strand of the perfume liquid runs diagonally across the frame, a single droplet swelling and travelling down it, backlit ice blue so the liquid glows against the dark field.

[00:10.3] Abstract macro. Camera racks fast laterally across the flacon's glass ridges, vertical bands of black and burning blue-white streaking past, sapphire flickering at the core, the product unreadable.

[00:11.5] Medium macro, symmetrical and centred. The gold lattice cap stands upright in the open heart of a white orange blossom, petals fanning either side. Camera pushes in slowly as the light blooms from near-black to full, a cold backlight rising through the petals and a hard front kicker catching the woven gold.

[00:12.8] Close-up from a high three-quarter, looking down onto the flacon's shoulder and the cap at a forty-five degree angle so the lattice weave stays visible on its side and the polished gold top is seen obliquely, never flat-on. Cool side key from the left throwing a long hard shadow across a matte black surface. Camera orbits slightly to the right.

[00:14.0] Extreme macro of pale Georgywood grain running diagonally across the frame, warm honey-toned wood under cold light, a hard cool raking key growing out of darkness and separating the fibres one ridge at a time. Camera drifts diagonally.

[00:15.3] Close-up of a fresh ginger rhizome broken open, its raw pale yellow fibrous cut face turned to camera, moist and alive rather than dried or grey, rising out of darkness as a cool overhead key comes up. Camera pushes in slowly.

[00:16.6] Macro of vertical shards of dark Akigalawood standing side by side, cold blue-white light burning through the narrow gaps between them, the wood almost silhouetted. Camera drifts laterally to the left.

[00:17.8] Tighter on the same wood, fewer and larger slabs, the glowing gaps hotter and taller. Camera continues drifting laterally to the left.

[00:19.2] The full flacon straight-on, emerging from black as a soft cool key rises behind it from an unseen source, the sapphire gradient resolving from top to bottom and the EX NIHILO PARIS mark and BLUE TALISMAN lines coming clear. Camera pushes in slowly.

[00:20.7] A slow silvery-blue vapour cloud unfurling and settling in black space, soft, weightless and translucent, lit from one side by a cold key, nothing else in frame. Camera drifts to the right through it.

[00:22.4] Wide packshot. The flacon standing left of centre on a deep blue matte surface with a long hard grounding shadow raking away to the right, a cool wash behind it, the EX NIHILO PARIS lockup set in the empty right half of the frame. Camera pushes in very slowly, almost imperceptibly.

Cinematic, photorealistic, luxury fragrance campaign. Deep black and electric sapphire palette, icy blue and silver-white light throughout, the flacon's champagne gold cap the only warm metallic accent. No distortion. Maintain product proportions.
```

## Cautions when reusing it

- **It's a fragrance pattern.** Its "liquid strand / droplet running" shot doesn't suit a fine-mist sprayer.
  Show a mist burst instead (we learned this the hard way: Narayan, "why is there liquid coming out the fine
  mist sprayer").
- **It's a demo.** Expect 3–5 takes for one clean film at about $3.50 per 15 s at 720p (2026-11 prices).
- **Small printed text still garbles in AI video.** Plan to lock the real label in post.
