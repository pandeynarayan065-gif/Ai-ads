# @0xROAS ("0x ROAS"): AI UGC ads (Sora 2, Seedance 2.0/2.5, Veo 3.1, lipsync stacks)

**Studied:** 2026-11-02, at Narayan's request ("analyse this guy's prompts and creations in depth").
**Sample:**
- 43 of his posts (Oct 2025 – Oct 2026) out of ~2,194, so it's biased toward popular, search-indexed posts;
- 19 videos analysed frame by frame and transcribed;
- 2 prompt Google Docs and 1 X Article.

**About the account:** ~59k followers. He sells a paid Whop course and community; his ROAS and "$1B ad
spend" claims are unverified. His audience is marketers, so his engagement measures how appealing a
tutorial is, not how well the ad sells.

**Treat him as a technique source, not a model of practice.** Many of his ads use:
- before/after transformations;
- invented stats and fake authority ("Harvard and Stanford confirmed", fake doctors, fake podcasts);
- cloned voices of real people;
- other brands' IP;
- ragebait.

None of that is usable for us (see Avoid).

## The 6 techniques worth keeping

1. **Blocks "inherited by all scenes".** One fixed realism block that every scene inherits:
   - device, lens and depth of field, handheld jitter, practical light, "HDR auto-tone, no filters", resolution
     and frame rate;
   - an audio block;
   - authenticity keywords;
   - a long exclusion list.

   Then each scene adds only its change (one emotion or action, one line). Per him, editing the inherited
   blocks loses the "iphone look". This is the same idea as our product lock and the Higgsfield demo's
   global look: **fix the constants once, vary one thing per scene.**
2. **Each reference has exactly one job** (Seedance). His wording:
   - `@Image1 as the starting frame`;
   - `Replicate the … action from @Video1`;
   - `Reference Image1 for the character only` ("stops it from pulling the background, lighting, or
     composition out of your character image");
   - "make sure to keep everything else the same";
   - "make sure the color grading is correct and matches the original video" ("stops it from washing the clip").

   For us: **"Reference Image1 for the product only."**
3. **Timecoded beats** (`0-3s / 3-10s / 11-15s`). Seedance keeps the order and squeezes the beats into whatever
   length you pick, so match the generation length to the plan.
4. **Reference-sheet logic: exactly one of anything that must not duplicate.** In his character sheet only
   column 1 shows a face; the front body is cropped at the neck, the back view has no face, and the prompt
   ends with "exactly one visible face in the entire reference sheet". Apply the same to product sheets: each
   view distinct, one front label, no mirrored or duplicate labels.
5. **Hands-only formats that persuade without a face:**
   - the **whiteboard explainer**, his best bookmark rate: a hand writes "THINNING?", draws the mechanism,
     erases; the real product is placed on the board and circled;
   - the **one-action-per-shot demo** (pressure washer): a surprising real first use, then one hand action
     per shot with a short narrated instruction, a kit reveal, and a cart call to action;
   - the **illustrated explainer** ("Finn Explains"): labelled close-up diagrams, the packshot drawn into the
     scenes.
6. **Pay-per-use APIs, one stage per tool.** kie.ai or Flow for video; Nano Banana for stills; MiniMax or
   ElevenLabs for voice; InfiniteTalk for lipsync from one still. In Oct 2026: Seedance 2.5, with Claude
   Code automating whole batches. A screenshot shows about $1.8k of API spend in one week.

## Prompts, verbatim

**Seedance 2.5, swapping a character into a reference video** (his most-bookmarked post, 1,509 bookmarks:
https://x.com/0xROAS/status/2105719128954950142):
```
Reference Image1 for the character only.

Replace the old man in Video1 with the character in Image1, make sure to keep everything else the same.

also make sure the color grading is correct and matches the original video.
```
His framing is "You're stealing the thing that already got the views". **Don't clone other creators' videos.**
The pattern itself (Video1 = motion or layout reference, Image1 = one job) works with our own or licensed
reference clips.

**Character sheet with exactly one face** (same article, made with a GPT image model):
```
Column 1 is the only panel where the character's face is visible. Show a large chest up front portrait with the full face clearly visible, sharp eyes, pale blue irises, broad square jaw, prominent nose, large toothy grin, thick eyebrows, and tall swept back pompadour.

Column 2 shows the same character full body from the front, but crop the composition so the head is completely outside the top edge of this panel. Start the visible body at the base of the neck and continue down to the shoes. Preserve the exact blazer, tie, trousers, proportions, clasped hand pose, and body build. Do not generate a second face anywhere in this panel.

Column 3 shows the same character full body from the back. His head may remain visible only from behind so no facial features are visible. Clearly show the back of the pompadour hairstyle, blazer construction, dark elbow patches, trouser fit, posture, and shoes.

Important composition rule: exactly one visible face in the entire reference sheet, located only in the large left portrait. No duplicate face, no second frontal head, no profile face, no reflected face, no facial features in either right panel.
```

**Seedance 2.0, first frame plus motion reference, jump-cut montage**
(https://x.com/0xROAS/status/2021286284237402389 → video 2021284338982178844, 10 cuts in 10 s, music only):
```
@Image1 as the starting frame. Create a seamless cinematic montage of the woman drinking a shot of golden olive oil from a small glass multiple times. Scene Progression: > 0-3s: Replicate the drinking action from @Video1. 3-10s: A series of rhythmic jump-cuts showing her in 3 different outfits and backgrounds (kitchen, living room, sunlit balcony) taking the same shot. 11-15s: A final close-up of her face as she smiles.Visual Evolution: > Throughout the video, gradually transition her skin from having slight redness and inflammation to a hyper-realistic, glowing, and perfectly clear complexion. Use warm, natural lighting and cinematic 4k texture.
```
The "Visual Evolution" clause is a before/after health beat, **banned for us**. The montage mechanics are
fine: the same action, rotating outfits and rooms, about 1 s per cut.

**Sora 2 Pro storyboard: the inherited realism blocks** (kie.ai JSON; Google Doc
1cOqkPBQrxpDUuOc2OMf96rRYNA9jK3D5Cj44ySjL8zg, from https://x.com/0xROAS/status/1979304229207470174):
```
Cinematography (Inherited by all scenes):
Camera Shot: Medium close-up from a slightly high angle, with centered framing that keeps her head and shoulders in the shot.
Lens & DOF: IPHONE 15 PRO front camera (~24 mm equivalent), deep depth of field keeping the bathroom background in focus with a natural subtle falloff.
Camera Motion: Subtle handheld sway and jitter consistent with a selfie grip, including very slight natural arm movements as she speaks and gestures.
Lighting: Bright, soft, diffuse frontal light from a high-quality bathroom vanity light, illuminating her face evenly. Soft shadows are visible behind her.
Color & Grade: IPHONE 15 PRO HDR auto-tone; a neutral clean color palette; natural skin texture with visible pores is preserved; no filters are applied.
Resolution & Aspect Ratio: 720x1280, 30 fps, vertical. Filename realism: "IMG_8234.MOV".
Audio & Ambience (Inherited by all scenes):
Recorded through IPHONE 15 PRO mic — clear front-facing voice with a slight natural room reverb from the tiled bathroom walls.
Faint, almost imperceptible ambient room tone.
No music, one-take natural pacing.
Universal Prompt Modifiers
UGC Authenticity Keywords: smartphone selfie, handheld realism, bathroom review, bright vanity lighting, influencer-style monologue, direct-to-camera, product review, raw unfiltered TikTok aesthetic, real voice, micro hand jitters, seamless one-take.
Universal Quality Control Negatives: subtitles, captions, watermark, text overlays, words on screen, logo, branding, poor lighting, blurry footage, low resolution, artifacts, unwanted objects, inconsistent character appearance, audio sync issues, amateur quality, cartoon effects, unrealistic proportions, distorted hands, artificial lighting, oversaturation, compression noise, excessive camera shake.
```
The wrapper: `{"input":{"aspect_ratio":"portrait","n_frames":"25","image_urls":[<packshot>],"shots":[{"duration":15,"Scene":…},{"duration":5,…},{"duration":5,…}]},"model":"sora-2-pro-storyboard"}`.
Scenes 2 onward are one line each: an emotion change plus quoted dialogue. Sora shows the reference image
as frame 0, so trim it.

**Stack recipes he stated in posts:**
- Lipsync: "clone voice with elevenlabs or chatterbox / lipsync with infinitetalk".
- Talking head from one still: "upload image to gemini / ask it to generate a 1:1 json prompt / generate the voice
  with minimax audio / generate the image with nano banana 2 / lipsync with infinitetalk (open-source)".
- Veo: "flow ultra plan, 10 credits per vid"; "Kling 3 better but pricier".

**Copy analysis with Grok:** "extract and analyze the long copy native ad form. extract every detail,
copywriting trick, use of words, reading grade level…". Use it to learn a structure from ads in the
Facebook Ads Library. **Don't** use his next step, "follow [competitor]'s structure 1:1" to clone their copy.

## Formats and rhythm (measured on his videos)

| Format | Cuts | Notes |
|---|---|---|
| Selfie or talking head | none (one take, 24–60 s) | Product held beside the face, pushed toward the lens |
| Product demo / b-roll | ~4–5 s per shot | One hand action per shot + narrated instruction → kit reveal → call to action |
| Jump-cut montage | ~0.9–1 s per shot | Same action, rotating outfits and rooms |
| Whiteboard | no hard cuts (erasing is the transition) | ~85 words in 35 s; product placed and circled |
| Illustrated explainer | scene changes ~3–5 s | Labelled close-up diagrams |
| Animated drama ("Pixar") | ~2.5 s per shot | Ragebait story with the product inside it (avoid) |

**Captions** are always added in post: one big word at a time, word-by-word with a yellow highlight, or small
sentence boxes.

**Hooks he uses:**
- a surprising real use (a pressure washer blasting a wasp nest);
- a written question ("THINNING?") or a character ("MEET DAVE");
- a contrarian reframe;
- a confession ("I debated whether to even post this");
- an everyday moment ("Most guys notice it in the shower first").

**Calls to action:** "Tap below" while pointing down; a drawn "START HERE ↓"; "orange cart".

**Whiteboard script shape (35 s):** an everyday symptom → "here's the part nobody explains" → two lines of
mechanism → ingredients → product → "Tap below".

## AI tells seen in his outputs (check ours for the same)

- **Garbled text:** product packs ("Cuperfoods Greens Cummies"), signs ("SEESE"), a neon "0xPOAS".
- **Continuity:** the product floating or jumping between hands, hair changing between cuts, the glass size
  changing.
- **Leftovers:** the reference image flashing as frame 0 (Sora); a platform watermark (Jimeng).
- **Voices:** commenters spot synthetic voices; Veo shows mouth and teeth artifacts unless framed from the
  collarbone up.
- **The model ad-libbed benefit claims that weren't in the prompt** ("gut health, energy, immunity…").
  So transcribe all generated speech and check every claim (now in `reference/ai-video-qa.md`).
- **Commenters' reality check:**
  - "$1 per ad" ignores the credits burned on regenerations;
  - choosing the right first 3 seconds out of ~40 generations is the actual skill.

## For Spraymax

**Adopt:**
1. **Whiteboard / hands-only explainer.** "Flat by 2 pm?" → how sea salt adds grip and texture (only claims
   in the brand file) → the real bottle placed on the board and circled → "Tap below". The hand draws icons
   only; all words go in post.
2. **One-action-per-shot demo, faceless** (hands, back of head, over the shoulder):
   - open on a backlit mist burst, a striking first shot that's also real;
   - then shake, mist onto damp hair, scrunch upward, twist a section, air-dry;
   - one short instruction per step, ~4–5 s each;
   - end on a packshot and a call to action.
3. **Inherited realism blocks** for the phone look: rear camera, handheld micro-jitter, practical light, "no
   filters", plus his exclusion list (captions, text overlays, watermark, logo, distorted hands, excessive
   shake).
4. **"Reference Image1 for the product only"**, a one-label product sheet, and the real label locked on in
   post.
5. **Ritual montage cut on the spray**, ~1 s per cut, across Indian everyday settings (bike-helmet hair,
   college, gym, a wedding): the same action every time, **no transformation at the end**.
6. **Hook testing:** many cheap opening variants over one fixed body, judged on the first 3 seconds.

**Avoid:**
1. **Any before/after:** flat → voluminous on the same head, day 1 vs day 7, split screens, "visual
   evolution" clauses.
2. **Health or efficacy claims and invented authority:** stats, doctors, universities, "news segment
   pulled". Write the script from the brand file and check the transcript of every output.
3. **Synthetic people posing as real customers or experts** (fake reviews, fake podcasts). Disclose AI per
   platform rules and the ASCI code.
4. **Other people's likeness, voices and IP:**
   - cloning a stranger's voice;
   - swapping characters into someone else's viral video;
   - "Pixar" style;
   - implied celebrities;
   - other brands' products.
5. **Access and watermark workarounds**, ragebait drama, engagement bait ("reply prompt"), fake urgency.
6. **Overstuffed multi-beat prompts.** His outputs drift (hair, props, hands). Our rules hold: one action per
   shot, still first, no words from the video model.

## Where the raw data was

The scratchpad from 2026-11-02 holds 43 posts (JSON), 19 videos with contact sheets and transcripts, and both
docs; it may be gone. Re-fetch any post with the method in `README.md`.
