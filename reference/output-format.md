# Ads File Format

One file per platform: `ads/<brand-slug>/<campaign-slug>/<platform>.md`.

The front matter `platform:` must be one of the checker keys in `platform-specs.md`.
Each field is a bullet in the form `- **Field name:** text` so the checker can count it.

```markdown
---
brand: acme-coffee
campaign: fall-launch
platform: meta
brief: briefs/2026-10-05-fall-launch.md
---

# Meta ads — Fall Launch

## Variation 1 — Pain (PAS)
- **Primary text:** Tired of bitter office coffee? ...
- **Headline:** Smooth coffee, delivered weekly
- **Description:** Free shipping on first box
- **CTA button:** Shop Now
- **Visual:** Close-up of a steaming mug on a desk at sunrise, warm tones.
- **Image prompt:** photorealistic close-up of a ceramic coffee mug ...

## Variation 2 — Social proof
...
```

For Google Search, list each asset as its own bullet:

```markdown
## Headlines
- **Headline:** Fresh Roasted Coffee Beans
- **Headline:** Free Shipping On First Box

## Descriptions
- **Description:** Small-batch beans roasted to order and delivered in 48 hours. Try it now.

## Paths
- **Path 1:** coffee
- **Path 2:** subscription
```
