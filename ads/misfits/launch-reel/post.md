# Misfits — first post: launch reel

**File:** `misfits-launch-reel.mp4` (1080×1920, 30 fps, 18.6 s, one continuous camera move, no cuts)
**Cover:** `cover.jpg` (the "you just watched this for 0:09" frame; text sits inside the 3:4 grid crop)
**Pin it** as post 1 of 3.

## Concept: the attention test
A feed of identical grey ad cards scrolls by. One card turns lime and tilts off-axis (the misfit, same idea
as the logo). The rest of the feed falls away. A timer shows how long you've been watching. The card shows
real client work (Spraymax), then locks into the Misfits symbol: end card + "Comment FILM".

| Time | Voiceover (Kokoro, voice `am_michael`, free/local) | On screen |
|---|---|---|
| 0.3 | Every ad in your feed looks the same. | EVERY AD LOOKS THE SAME. |
| 2.7 | Same look. Same offer. Same flick. | SAME LOOK. SAME OFFER. SAME FLICK. |
| 5.6 | Then one doesn't fit in. | THEN ONE DOESN'T FIT IN. (lime card rises, tilts) |
| 8.0 | And you just watched this for eight seconds. | YOU JUST WATCHED THIS FOR 0:08 |
| 10.6 | Imagine it was your product. | IMAGINE IT WAS YOUR PRODUCT. + Spraymax frame, "Client work · Spraymax" |
| 13.4 | Misfits. Ads that don't fit in. | Symbol assembles, MISFITS wordmark |
| 15.6 | Comment film, to start yours. | COMMENT "FILM" · misfitsagency.in |

## Caption (paste as is)

```
You just watched a tile for 8 seconds.
Imagine it was your product.

Most ads look the same, so they get the same flick. We make the ones that don't fit in, then run the campaigns that turn them into leads, sales and bookings.

AI ad production + paid ads, under one roof.
Client work in this reel: Spraymax.

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
