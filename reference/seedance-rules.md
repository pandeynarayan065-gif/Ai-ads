# Seedance 2.5 rulebook (the film crew's single source)

Every rule and hard-won lesson for Seedance 2.5 in one page. All the `.claude/agents/` crew read this before they
work. Each line names where it came from: **[PB]** `reference/ai-video-playbook.md`, **[QA]** `reference/ai-video-qa.md`,
**[QR]** `reference/quick.md`, **[LOG]** `ads/<brand>/prompt-log.md`, **[HF]** / **[0x]** / **[PR]** the creator
studies in `reference/creators/` (Higgsfield Ex Nihilo, @0xROAS, Prada glass reel), **[N]** Narayan in chat (date).
**[VERIFY]** = not confirmed by the repo, kie.ai docs or Narayan: ask before relying on it.

## 1. Money and safety (never break)

1. **No credits without Narayan's yes on the exact prompt.** Order: `python3 scripts/kie_generate.py credits` →
   dry run (no `--yes`) → show the exact prompt, refs, mode, resolution, length and cost → wait. A "go" before he
   has seen the final prompt is not approval. Tests cost credits too. [CLAUDE.md]
2. **Agents never run the generator with `--yes`.** Only the main session does, after the yes. [crew rule]
3. **Never print, paste or commit the kie key** (`KIE_API_KEY`, env var or git-ignored `.env`). Don't echo `.env`.
   If he pastes a key in chat, never copy it into any file. [CLAUDE.md, SETUP.md]
4. **No real person's likeness** (including Narayan's own photo, on hold since 3 Nov), **no copyrighted characters
   or look-alikes** (e.g. a game or anime hero), **no other brand's product or logo** in a client ad. Spec ads of
   a real brand use that brand's own official photos and are captioned "Spec ad. Not affiliated with …". [N, 0x]
5. **No invented claims**: no stats, benefits, prices, awards or specs that aren't in the brand file, brief or the
   brand's official page. Transcribe any generated speech: models ad-lib benefit claims. [CLAUDE.md, QA, 0x]
6. **"Stop" means stop**: kill running work, change nothing more. [N 4 Nov, 14 Nov]

## 2. Seedance 2.5 on kie: facts we have confirmed

| Fact | Value | Source |
|---|---|---|
| Model / command | `bytedance/seedance-2-5`, `python3 scripts/kie_generate.py seedance` | [PB §4] |
| Length | **4–30 s** per run. 3 s is refused ("Value must be within the specified range", 500, uncharged). We have run 4 s and 12 s | [N 17 Nov, QR] |
| Cost per second of output | 480p 28 cr, 720p 63 cr, 1080p 158 cr (1 cr = $0.005). Reference images are free; a reference video is billed | [PB §4] |
| Modes | Reference images (`--ref`, Image 1, 2, … = order given) **or** first frame (`--first-frame`, optional `--last-frame`). Never both in one request | [PB §5.5] |
| First-frame aspect | Must be `--aspect adaptive`; 9:16 is rejected (422, uncharged) | [QR, Samsung chip remake] |
| Audio | Off by default (`--audio` turns it on). We always generate silent and build sound in post | [PB, all takes] |
| Draft | `--draft` = 480p; `seedance-final` renders 1080p from the draft (price not listed by kie) [VERIFY] | [PB §5.5] |
| 480p fallback | 4 s at 480p (112 cr) upscaled with Real-ESRGAN cut in cleanly next to 720p footage | [LOG jpg storm, lavender] |
| Max reference images | We have used 1–3. The upper limit is **[VERIFY]** | |
| Higgsfield website | Same model, prompt pasted by hand; up to 20 s per run [N 17 Nov]; credit cost per second **[VERIFY]** | |
| Multi-shot capacity | 12–15 timestamped hard-cut shots in 12 s have worked (Spraymax 15 → 14 visible cuts at its own spacing; Red Bull 13; Samsung 13; JPG 12) | [LOG] |

## 3. Prompt structure that has worked (copy the order)

Proven files: `ads/spraymax/cinematic-12s/prompt-seedance-12s.md`, `ads/redbull-spec/cinematic-12s/prompt-seedance-12s.md`,
`ads/samsung-spec/fold8-ultra-12s/prompt-seedance-12s.md`, `ads/jpg-spec/ultra-male-12s/prompt-seedance-12s.md`.

1. **Asset mapping.** "Image 1 is [whose official photo] of the real [product], [view]. Use Image 1 only for
   [shape, proportions, colour, print]; ignore its white background. Define … as <Subject 1>. <Subject 1> is
   identical in every shot." Each reference gets exactly **one job**. [PB, 0x, HF]
2. **Product truth**: the product-lock text **word for word** (`brand/<brand>/product-lock.md`), with real size,
   proportions ("two and a quarter times as tall as it is wide") and a scale anchor against a hand. Narayan checks
   that sizes are in the prompt ("U gave it the product sizes…?" 4 Nov). [PB rule 5, N]
3. **One-sentence summary** of the film. [PB §5.5]
4. **Hard-cuts rule**: "Hard cuts only throughout: every shot is a completely separate camera setup. No
   transitions, no dissolves, no wipes, no fades, no motion carrying across a cut." [HF]
5. **Real-photography block** inherited by every shot: named camera and lenses (ARRI Alexa 35, macro, motion
   control), real physics and practical effects, "natural film grain, gentle lens falloff; no plastic sheen, no
   over-sharpening". [HF, 0x, PB §7]
6. **Global look**: palette in named tones, light quality, negative space; one warm accent at most. [HF, PR]
7. **Never-render list, before the shots**: text/letters/numbers/logos/captions/watermarks anywhere; other brands;
   faces; warped or resized product; extra parts; mirror floors and product reflections; visible light fixtures;
   halos; lens flares; "the product centred and fully lit in every shot". [HF, PB]
8. **Timestamped shots** `[mm:ss.s]`, start-first, no gaps, ~1 s apart (0.6–1.5 s); each 60–100 words with framing,
   subject, light, **one action** and **one camera move** written last ("Camera pushes in slowly."). [HF, PB, lint]
9. **"Throughout" line**: product keeps its exact shape, proportions, colours and print from Image 1; "Keep it
   subtitle-free, with no captions and no watermark. No music and no voices." [PB §5.5, lint]

Camera words the linter recognises: pushes in, pulls back, drifts left/right/up/down, tilts up/down, pans, orbits,
locked-off, holds still, handheld, rises/crane. One family per shot. [scripts/prompt_lint.py]

## 4. What Seedance 2.5 gets wrong, and what fixed it

| Failure | Seen in | Fix that worked |
|---|---|---|
| **Stands the product upright** even when told it lies on its side | Spraymax ocean (twice), seashore insert | A reference photographed lying down, or first-frame mode from a frame where it already lies; trim upright moments in the edit [LOG] |
| **Writes fake text on any surface that would carry print** | Samsung chip lid ("SALOXY SNMAD"), Red Bull gloves (a real brand's star logo), wingsuit pseudo-letters | Say "blank, no markings" for those surfaces; ask for plain gear; if it still prints, remake from a first frame with the surface wiped blank (4 s, `--aspect adaptive`) [QR, LOG] |
| **A reference used "only for a reflection" is pasted in flat** | Samsung opener: Fold8 photo faded into the Apple logo | Leave that reference out and describe the reflection in words (a thin sliver of an edge), or cut before it shows [QR] |
| Small print garbled; big wordmark usually right | Spraymax every clip | Lock small lines in post; on moving shots prefer Seedance's own label over a pasted fix (Narayan rejected the pasted one: "slapped on", "morphs") [LOG, N] |
| Product swells when a hand passes over it | Spraymax reveal (mitt wipe) | No hand ever moves over the product [LOG] |
| Hands look off (old, hairy, wrong sleeve) and pull focus | JPG spray shot (deleted by Narayan) | Avoid hand-use shots unless the story needs them; if needed, say the sleeve, the grip and the finger, and keep the shot short [N 4 Nov] |
| Compresses or merges stamps | Spraymax 15 stamps → 14 cuts | Expect ±1 cut; keep shots ≥0.6 s apart [LOG] |
| Mist from the wrong place / liquid out of a sprayer | Spraymax POV, Higgsfield adaptation | Describe the mechanism physically (side nozzle, mist sideways); a fine-mist product never shows liquid [HF, N] |
| Magic (zero-g, transformations) reads as CGI | Spraymax tethys, zero-g (both rejected) | Real-crew test: only real physical events (pour, splash, gust, drop) [LOG] |
| Real brand logos appear on gear | Red Bull | "plain gear with no logos"; check every frame [LOG] |
| Slow-motion or frozen end shot | Spraymax ocean v1 ("the endshot is stupid and lasts too long") | End shots in real time and short; no slow-mo ending [N] |
| Chrome/colour differs between cuts of the same object | Samsung iPhone → logo shot ("sloppy") | Fix in post with one fixed grade per shot, no masks (`grade_logo_shot.py`) [N] |
| Product drifts from text-only details | Veo/Seedance | Official product photos as references; collect every angle first (camera layout fixed from samsung.com) [LOG] |
| Water words in the sound line → bubbling audio | Spraymax | No water/wave/echo words in the sound line; silent generation [PB] |

## 5. Concept rules (the director and reality checker enforce these)

- **Real-crew test**: a real crew could film it in a day with real light, water, wind and the real product. [PB 1]
- **One shot = one camera move + one action + one physical cause.** [PB 2]
- **Never ask the model for words**: supers, captions, end cards, labels are post. [PB 6]
- **Faceless** for Spraymax and by default: from behind, hands only, silhouette; "never turns toward the camera".
  Helmets and goggles for athletes. [N, LOG]
- **Product shown truthfully or not at all**: right size against a hand, right use. [QA gate 0]
- **No before/after, no personal-attribute hooks, no fake people posing as customers or experts.** [QA, 0x]
- **Variety Narayan expects** across a film: macro, material/texture, product in use, ritual, reveal, POV,
  elemental (water, smoke, wind, storm, botanicals), multi-pack, hero. "What abt variety tho" (Nov). [N]
- **Perfume grammar for premium products**: product → ingredient → product macro → abstract → hero; cold light with
  one warm accent; ~80% negative space; hero left of centre with the empty side for a logo. [HF]
- **Pacing**: 0.6–1.5 s per shot, longer open (~1.4 s) and close (~1.5–2 s, real time); first 1.5 s must stop the
  scroll; consecutive shots carrying the same direction feel like one gesture. [HF, PB]
- **Keep approved shots** in any re-cut unless told to drop them; a requested swap means swap, not delete. [N]
- **Style and colour**: Spraymax is blue, never purple. Ultra-real, premium, never "AI slop". [N]

## 6. After a take (the reverse engineer)

- Contact sheet first (≤800 px wide, one sheet), cut list by frame difference, then full-size crops only where
  needed. Score on `reference/ai-video-qa.md` gate 3 (0/1/2 × 9, pass ≥14/18, no zero on 1, 4, 6, 7). [QA]
- For each failure: timestamp, the prompt words that caused it, the one-change fix. Log a row in
  `ads/<brand>/prompt-log.md` (that brand's own log) and, if it is a new pattern, add it to section 4 here.
- Judge a take by its best seconds: we use 0.6–2 s of each shot. A take with one bad shot is usually kept and the
  shot is cut or replaced with a 4 s insert. [PB, LOG]
- Post, not regeneration, for: colour continuity, small print, upscaling (Real-ESRGAN), supers, captions. [QR]

## 7. Open questions for Narayan [VERIFY]

1. Maximum reference images per Seedance 2.5 request on kie.
2. Higgsfield credit cost per second and its resolution options.
3. Whether `seedance-final` (1080p from a draft) is billed, and at what rate.
4. Audio-on price difference (we have never generated with audio).
