# Spraymax: 3 UGC demo ads (0xROAS techniques, our rules)

Built from `reference/creators/0xroas.md` ("For Spraymax: Adopt"): his inherited phone-realism block, one hand
action per shot, ~1 s ritual montage cuts and the hands-only whiteboard. Our rules stay on top: faceless (back of
head, hands), Seedance 2.5 only, no before/after, no fake reviewers, no words from the model, claims only from
`brand/spraymax.md`.

| # | Prompt | Format | Hook (first 2 s) |
|---|---|---|---|
| 1 | `prompt-seedance-01-demo.md` | One action per shot, morning bathroom: mist burst → shake → spray (from behind) → scrunch → twist → set down | Backlit mist burst against a window |
| 2 | `prompt-seedance-02-montage.md` | 10 × 1.2 s cuts, the same spray in 9 Indian everyday places (bike lot, college, gym, metro, rooftop, chai stall, office, bedroom, wedding) → into the backpack | Helmet hair in a parking lot |
| 3 | `prompt-seedance-03-whiteboard.md` | Hand-drawn explainer: flat hair lines → salt crystals → crystals holding two strands apart → real bottle on the ledge, circled | Written question added in post |

Refs (proven on the cinematic film): Image 1 `../cinematic-12s/refs-seedance/01-bottle-photos.jpg`, Image 2
`../cinematic-12s/refs-seedance/02-label-flat.jpg`. Lint: PASS on all three (`--kind seedance --faceless --sd 2.5`).

## Cost (dry run, not spent)
Seedance 2.5, 720p, 9:16, 12 s, audio on (natural SFX only): **756 cr ($3.78) each, 2,268 cr ($11.34) for all three.**
Balance on 7 Nov: **7 cr**, so a top-up is needed first. Budget ~1.5x for a retake or two.

```bash
python3 scripts/kie_generate.py seedance --prompt-file ads/spraymax/ugc-demos/prompt-seedance-0N-....md \
  --out ads/spraymax/ugc-demos/takes --ref ads/spraymax/cinematic-12s/refs-seedance/01-bottle-photos.jpg \
  --ref ads/spraymax/cinematic-12s/refs-seedance/02-label-flat.jpg --resolution 720p --aspect 9:16 --duration 12 --audio --yes
```

## Post (free, local)
- **Captions:** big word-by-word captions with a highlight on the key word (his format), Inter/Archivo, inside the
  Reels safe zone.
- **Voice:** instructional, not a fake customer. Kokoro (free, local) or the client's own voice. Scripts:
  1. "Shake. Spray on damp hair. Scrunch it up. Twist the top. Styled in under ten seconds." (site: "Shake. Spray.
     Style.", "in under 10 seconds")
  2. No voice: on-screen "Helmet hair? Shake. Spray. Style." then place names as one-word supers; licensed music.
  3. "Flat by two? Here's the part nobody explains. Himalayan sea salt gives every strand grip, so it holds texture.
     Matte, not sticky. No wax. No gel. Spraymax." Supers: "FLAT BY 2PM?", "SEA SALT = GRIP", "MATTE. NOT STICKY."
- **CTA:** "Shop at spraymax.in" (₹449 only if the site still shows it on posting day).
- **QA:** contact sheet per take; transcribe any generated speech (should be none); check label, nozzle direction,
  no faces, no garbled text; log in `ads/spraymax/prompt-log.md`.
