# Creator studies

Breakdowns of AI ad creators and demos we've studied: their prompts (verbatim, with links), what their outputs
look like, why they work, and what to adopt or avoid for our brands. These are a long-term memory. Read the
relevant file before writing prompts in that style. Add a new file whenever we study someone new, and keep
"Adopt / Avoid" honest.

| File | Who / what | Use it for |
|---|---|---|
| `higgsfield-seedance-ex-nihilo.md` | Higgsfield's Seedance 2.5 luxury perfume film (one product sheet + one timestamped prompt) | Premium multi-shot product films in one generation |
| `0xroas.md` | @0xROAS on X: AI UGC ads (Seedance etc.) | UGC-style ads, reference-video motion, jump-cut montages |

How to study a new creator (what worked for X, where profiles and mirrors are blocked):
- **Fetch single posts** through Twitter's syndication endpoint:
  `https://cdn.syndication.twimg.com/tweet-result?id=<STATUS_ID>&token=4c2mmul6mnh&lang=en`. The JSON
  holds the text, expanded links, the parent and quoted posts, and mp4 video variants.
- **Find the post IDs** with web search, then crawl outward through `parent`, `quoted_tweet` and links in
  the text.
- **Export linked Google Docs** as text: `https://docs.google.com/document/d/<ID>/export?format=txt`.
- **Read every video,** don't just transcribe the prompts:
  - make a contact sheet (a frame every 0.5 s) and a cut list (histogram);
  - measure the motion per frame with optical flow (that's how we copied the "bro carrying" reel's camera
    moves).
