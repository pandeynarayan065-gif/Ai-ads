# Spraymax bottle: real-world spec (from Narayan's hand-held photos, 2026-10-13)

Use this wording in every prompt. References, in this order:
1. `assets/bottle-real-front-crop.jpg`: real photo, front, close
2. `assets/bottle-real-hand-wide.jpg`: real photo, whole bottle in hand (scale)
3. `assets/label-front-panel.jpg`: label print artwork (exact letters)
Never use `bottle-front-render.jpg` / `bottle-ref-clean.jpg` as the main reference: they are
CG renders and make the output look like a render.

| Part | Real look |
|---|---|
| Bottle plastic | Slightly greyish off-white, semi-matte / satin. NOT glossy, NOT bright white |
| Size | 100 ml, about the length of an adult palm (roughly 14 cm with cap); slim cylinder, rounded dome shoulder |
| Label | Bright white paper sticker, a shade whiter than the bottle. Starts just below the shoulder, ends ~1 cm above the base; edges slightly visible; back-label text peeks at the sides |
| Wordmark | "Spraymax", vertical, reading top to bottom, royal indigo-blue, rounded geometric font |
| Tagline | Small dark "Instant Hair Volume & Texture" just above the wave band |
| Wave band | Dark navy ocean-wave photo, bottom third of the label; white "FOR ALL HAIR TYPES" (bold) and "100ml/3.38fl.oz" (thin) |
| Collar | Matte white, fine vertical ribs, narrower than the body |
| Pump | White actuator with a small round nozzle hole |
| Overcap | Cloudy / frosted translucent plastic (not crystal clear); pump visible inside |
| Wear | Light real-world specks and scuffs are normal |

## Why the Manali cafe image looked real (and still 2 did not)

| Manali (worked) | Still 2 (looked fake) |
|---|---|
| "candid iPhone photo by a traveller", "not an advertisement" | "high-speed product commercial footage", Phantom Flex4K: summons CGI packshot imagery |
| Real hand-held photo as reference | CG render as main reference: output inherits the render look |
| Bottle described as greyish semi-matte, fingerprints, sticker edges | "glossy white", "perfectly sharp": produced a spotless render |
| Ordinary believable situation (bottle on a cafe railing next to chai) | Staged situation (bottle in a splash crown) the model only knows from CGI ads |
| Soft overcast light: easy for the model to match | Hard midday sun + splash: lighting mismatch, bottle looks pasted |
| Contact with surface, real props, wood grain, stains | Bottle floating in water, no contact shadow |
| Asked for imperfection: 2 degree tilt, shadow noise, "avoid perfectly arranged, CGI" | Asked for perfection |
| Second pass: edit the real-looking photo, change only the bottle | Single shot |
