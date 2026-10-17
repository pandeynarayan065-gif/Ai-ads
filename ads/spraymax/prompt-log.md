# Spraymax prompt log

Every take, what happened, and the rule it gave us. Newest first. Add a row after every generation (the `/shot`
command does this). Details for each take are in the `*-notes.txt` file next to its clip or image.

Lint = today's `scripts/prompt_lint.py --faceless` result on the prompt as sent (t2v / ref / i2v kind).

## Video takes

| Shot | Model / mode | Lint | Verdict | What happened | Rule it gave us |
|---|---|---|---|---|---|
| Studio "tethys" (sea becomes mountains) | Veo 3.1 Fast, first frame | FAIL: transformation | Rejected: "Both lowk ass bro" | Water welled out of the slate and turned to rock; read as CGI | Real-crew test: no transformations |
| Studio "zero-g" (drops float round the bottle) | Veo 3.1 Fast, first frame | FAIL: magic ("gravity switches off", float) | Rejected (same) | Floating drops, CGI look; the camera didn't move (push-in added in post) | Real-crew test; one camera move, and expect to add it in post |
| Studio hero v2 (real proportions, sticker, clear cap) | Veo 3.1 Fast, first frame | FAIL: 411 words | **Kept** (in the edit) | Real-looking splash; small text garbled (fixed with `fix_text_v2.py`) | Build the first frame at real proportions; fix small text in post |
| Studio hero v1 (from the Gemini mockup) | Veo 3.1 Fast, first frame | FAIL: 340 words | Rejected: "The label sticker isn't visible and there's no gap at the bottom" | The mockup's bottle was squat. Veo kept it, and barely moved the camera (2–3%) | Still QA against the real bottle **before** animating |
| Ocean spray v2 | Veo 3.1 Fast, first frame (1080x1920 JPEG) | FAIL: 399 words | **Kept** after the handheld label lock | Bottle stayed real size; the pump dipped and mist went sideways into the hair; first lock looked like "a jpg sticker" with a yellow tint | Timed single actions work. A label lock must take the scene's light and colour |
| Ocean spray v1 | Veo 3.1 Fast, first frame | FAIL: 365 words | Rejected: "the bottle height is not realistic" | Bottle 23–27 cm next to his hand (it came from the still); camera drifted back; mist went up into the sky | Scale anchor in the still prompt and scale QA on the still. Say the mist's direction and that the camera "holds its distance" |
| Spray v1 (climber sprays hair) | Veo 3.1 Fast, reference | WARN: 302 words, "turns into" | Rejected: "this shot is so bad" | Held the bottle up to camera, nozzle at the sky; "mist" was a glowing cloud; label said "Spraymas" | Product-in-use shots need a checked still first; describe the grip and nozzle direction physically |
| Reveal v3 (mitt wipes snow off the bottle) | Veo 3.1 Fast, first frame | FAIL: 406 words | Used in v1, then cut: "the hand wiping clip looks bad" | The bottle swelled under the passing hand | No hands moving over the product |
| Reveal ref / v2 | Veo 3.1 Lite, reference / first frame | WARN / FAIL: 336 words | Not used | Same reveal idea; earlier attempts | Same as above |
| Drop into water | Veo 3.1 Fast, reference (real photos) | WARN: 277 words | **Kept** after label lock | Real cavity, bubbles and drag physics; bottle upright, no spin; label wrong (locked in post) | Real-physics events work; describe the physics in order |
| Salt macro | Veo 3.1 Fast, text-to-video | PASS | **Kept** | Snow came as a pour, not gentle fall; crystal stayed stable | Macro + one natural process is low risk |
| Helmet off, hair in the wind | Veo 3.1 Fast, text-to-video | WARN: 244 words | **Kept** (frames 22+) | Frames 10–20 showed a cheekbone | Faceless check on every frame; mark the usable range |
| K2 ridge | Veo 3.1 Fast, text-to-video | PASS | **Kept** after `clean_sky.py` | Gave a rope-mate's view, not the helicopter we asked for; dark streaks in the sky | Rigs are suggestions to Veo; environment shots are low risk |

**What the table says:**
- Every take the user rejected came from a concept problem: magic, a wrong-scale still, or a hand over the
  product. The prompts for those takes weren't simply too long.
- Every kept shot was a real physical event.
- Two long image-to-video prompts were kept (hero v2, ocean v2). So the word limit comes from Google's guidance,
  not from our own failures. Its aim is to stop us re-describing the frame and leave room to describe the
  motion precisely.

## Still takes

| Still | Model | Verdict | What the AI got wrong | Fix |
|---|---|---|---|---|
| Ocean spray (resize edit) | Nano Banana Pro edit | Kept as the v2 first frame | n/a | The resize edit fixed the scale |
| Ocean spray | Nano Banana Pro, 3 real refs | Fixed in post, then rejected for scale | Nasal-spray pump; smooth collar; label reversed with "TTFES"; bottle 13% long and oversized | `spray-ocean-fix.py`, `label_lock_still.py`, then the resize edit |
| Studio mockup (the user's, from Gemini) | Gemini | Proportions wrong | Squat bottle; "8.38 fl.oz."; watermark | Rebuilt at real proportions (`build_first_v2.py`) |

## Credits

- kie: Veo 3.1 Fast 1080p 8 s = 65 cr; Nano Banana Pro 2K = 18 cr. 1 cr = $0.005.
- Balances on 2026-10-17: new account 10 cr, old account 37 cr. Neither is enough for a Veo take; top up first.
