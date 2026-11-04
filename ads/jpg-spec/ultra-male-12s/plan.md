# Jean Paul Gaultier Ultra Male — 12 s portfolio spec ad (ad 3)

Brief (Narayan, 4 Nov 2026): "Ad 3: jean paul gartier perfumes ... need a crazy shot cinematic list. 6 seconds of
shots from this reference and the other you have to get creative". Reference: the Prada green-glass reel
(`reference/creators/prada-green-glass-reflections.md`). His link (share.google) opened Google Images on a
MyOrigines photo of the Le Male line (Le Male, Ultra Male, Le Male Le Parfum, Le Male Elixir); the product page behind
it is Ultra Male Intense, so the hero is **Ultra Male**: its deep navy glass suits the glass-reflection look, and blue
is his preference.

- Spec ad, visuals only, 9:16. Caption: "Spec ad. Not affiliated with Jean Paul Gaultier."
- Ref: `refs/01-ultra-male-official-front.jpg`, the brand's front packshot (via MyOrigines, image 39718242_P).
  The retailer's other photo (bottle beside the tin) was left out: the crop cut a shoulder, and the tin carries text.
- Product truth from the packshot: torso bottle, 2.25x as tall as wide at the shoulders; deep translucent navy glass;
  seven horizontal black stripes; silver ribbed collar with a small hanging ring; silver spray cap; no text on it.
- Shot list: 0-6 s, the reference's grammar in navy glass (light-blade reveal, glass macro, turntable + opposite orbit,
  three-quarter sweep, collar macro, side silhouette); 6-12 s, out to sea at night (ship deck and wave, seawater
  bead, anchor chain, striped-sleeve hand spraying, underwater plunge, lighthouse hero on a rock).
- Prompt `prompt-seedance-12s.md`: lint PASS, Seedance 2.5 reference mode, 720p, 12 s, 756 cr. Awaiting approval.

## Take 1 (4 Nov): keeper
- `takes/20261104-225549-1.mp4`: Seedance 2.5, 720p, 12 s, 756 cr (credits now 231). All 12 shots, in order; cuts at
  0.79 1.96 3.00 4.00 5.00 5.79 7.00 7.92 8.67 9.25 10.38 (the chain shot's fast links read as false cuts in a
  frame-difference cut list).
- Product holds: torso shape, seven stripes, silver ribbed collar and hanging ring. No fake text anywhere (collar
  macro and deck rail checked at full size). Ending moves in real time.
- Notes: the three-quarter shot's cap reads dark (chrome reflecting the black studio); the spray hand wears a black
  suit sleeve and white cuff, not the striped sleeve; the plunge goes in head-first.
- Preview `takes/preview-1080.mp4` (finish_film on the 720p take). Masters: `make_masters.sh` -> `jpg-ultra-male-spec.mp4`
  and `-4k.mp4`.
- Narayan: "Delete this shot" (the spray hand) and "generate a new shot more elemental". `edit_ultra_male.py` cuts
  take frames 208-221 -> `takes/edit-v1-720.mp4` (275 frames, 11.46 s). New shot: `prompt-storm-3s.md` (night storm on
  the deck, rain bursting off the glass, a lightning fork behind; 720p, 3 s, 189 cr: 4 s would be 252 > 231 left).
- 3 s was refused by kie ("Value must be within the specified range", uncharged): Seedance 2.5's minimum is 4 s.
