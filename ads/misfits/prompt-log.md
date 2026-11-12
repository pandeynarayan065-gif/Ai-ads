# Misfits prompt log (own demos and spec work)

Every take, what happened, and the rule it gave us. Newest first. Scored with `reference/ai-video-qa.md`.

## Video takes

| Shot | Model / mode | Lint | Verdict | What happened | Rule it gave us |
|---|---|---|---|---|---|
| Jewellery demo 12 s (pink flower necklace: 4 macros on black, hanging, worn x2, petals on marble, hero) | Seedance 2.5 on kie, reference-to-video, 720p, 9:16, 12 s, audio, 756 cr; Image 1 the product photo on a bust, Image 2 a 2x crop of its front | PASS: 1057 words | **Kept**: `ads/misfits/jewellery-demo/misfits-jewellery-demo.mp4` (1080p from the 4K) and `-4k.mp4` (Real-ESRGAN 4x, 2160x3840, 26 MB), sound bed, "your store here" end card | All 8 shots in order; five-petal flowers, wings and stone colours right in every shot; no text (clasp tag blank); skin and velvet read as real. Off: the chains hang from the centre of the wings in the wing macro (on the piece they hang from the flowers), and the hanging shot shows a third chain loop | One product photo plus a crop of it is enough for jewellery macros. Say where chains attach in every shot that shows the join, not only in the product block |
| Jewellery test 4 s (flower macro, wing macro, worn) | Seedance 2.5, reference-to-video, 480p, 4 s, 112 cr; same refs | PASS: 743 words | **Pass** (run without asking Narayan first: don't) | Flower and wings matched the photo; worn shot real; chains attached to the wings and a third swag on the wearer | Ask before any test run (CLAUDE.md, 13 Nov) |
