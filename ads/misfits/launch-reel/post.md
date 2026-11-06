# Misfits — first post: launch reel

**File:** `misfits-launch-reel.mp4` (1080×1920, 30 fps, 18.6 s, one continuous camera move, no cuts; v2 with bloom glow, 3D tiles, particles, gradient)
**Cover:** `cover.jpg` (the "you just watched this for 0:09" frame; text sits inside the 3:4 grid crop)
**Pin it** as post 1 of 3.

## Concept: the attention test
Open: the camera dives in fast while a lime scan line sweeps the feed and the cards pop up in its wake.
A feed of identical grey ad cards scrolls by. One card turns lime, glows and tilts off-axis (the misfit, same
idea as the logo), lighting up the cards around it. The rest of the feed falls away. A REC timer shows how long
you've been watching. The card cycles through vector product silhouettes (spray bottle, perfume, can: "your
product"), then locks into the Misfits symbol: end card + "Comment FILM".

| Time | Voiceover (Kokoro, voice `am_michael`, free/local) | On screen |
|---|---|---|
| 0.3 | Every ad in your feed looks the same. | EVERY AD LOOKS THE SAME. |
| 2.7 | Same look. Same offer. Same flick. | SAME LOOK. SAME OFFER. SAME FLICK. |
| 5.6 | Then one doesn't fit in. | THEN ONE DOESN'T FIT IN. (lime card rises, tilts) |
| 8.0 | And you just watched this for eight seconds. | YOU JUST WATCHED THIS FOR 0:08 |
| 10.6 | Imagine it was your product. | IMAGINE IT WAS YOUR PRODUCT. + silhouettes: spray bottle → perfume → can |
| 13.4 | Misfits. Ads that don't fit in. | Symbol assembles, MISFITS wordmark |
| 15.6 | Comment film, to start yours. | COMMENT "FILM" · misfitsagency.in |

## Caption (paste as is)

```
You just watched a tile for 8 seconds.
Imagine it was your product.

Most ads look the same, so they get the same flick. We make the ones that don't fit in, then run the campaigns that turn them into leads, sales and bookings.

AI ad production + paid ads, under one roof.

💬 Comment FILM and we'll DM you to start yours.
🌐 misfitsagency.in

#misfits #aiads #adagency #creativeagency #productads #reelsmarketing #d2cindia #motiondesign
```

## Posting checklist
- Upload the mp4 as a Reel; pick `cover.jpg` as the cover; check the grid crop.
- Share to story with a "Comment FILM" sticker; add to the **Work** highlight.
- Reply to every FILM comment by DM the same day (that's the promise in the CTA).

## Rebuild
```bash
python3 vo.py <kokoro_model_dir> am_michael   # voiceover lines -> vo/
python3 mix.py                                 # sound design + VO -> mix.wav
NODE_PATH=<dir with three + playwright> node render.js <three.module.js> video.mp4 30
ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5 -c:a aac -b:a 192k -shortest misfits-launch-reel.mp4
```
Kokoro model files: `kokoro-v1.0.onnx` + `voices-v1.0.bin` from the kokoro-onnx GitHub releases (`pip install kokoro-onnx`).
three.js 0.170.0 from npm. Colours are the live site's: ink `#08090b`, paper `#ecede8`, fit `#8bd346`.

---

# Carousel (album) — 5 photos, 1080×1350

Files: `carousel/slide-1.png` … `slide-5.png` (rebuild: `node carousel/render_carousel.js`). Backgrounds are clean frames
from the reel's 3D scene, so the reel and the album look like one launch.

1. **Hook:** STAND OUT / OR SCROLL PAST. (glowing misfit tile over the feed)
2. **Problem:** SAME LOOK. SAME OFFER. SAME FLICK. + the split-second line from the site
3. **What we do:** WE MAKE THE AD. THEN WE MAKE IT WORK. Make / Run lists (from the site's services)
4. **Proof:** Spraymax, 121K views · 7,365 likes · 131 comments (public counts on @spraymaxindia, both reels, Nov 2026)
5. **CTA:** YOUR BRAND COULD BE NEXT. Comment "FILM" · book a call

Caption:
```
Stand out or scroll past. 👀

Most ads look the same, so they get the same flick. Misfits makes the ones that don't fit in, then runs the campaigns that turn them into leads, sales and bookings.

Swipe to see how, and what it did for Spraymax →

💬 Comment FILM and we'll DM you to start yours.
🌐 misfitsagency.in

#misfits #aiads #adagency #creativeagency #productads #performancemarketing #d2cindia #metaads
```
Post the reel first, then the album a day or two later (or the same day if you want both on the grid at launch).
Before posting slide 4, re-check the Spraymax counts on their profile and update them if they've grown.
