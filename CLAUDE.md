# AI Ads Workspace

This repo is a workspace for generating ad copy and creative concepts with Claude.

## How work flows

1. **Brand** — `brand/<brand-slug>.md` describes the business, audience, voice and rules.
   Copy `brand/_template.md` to start a new one. Never write ads for a brand without reading its file.
2. **Brief** — `briefs/<YYYY-MM-DD>-<campaign-slug>.md` describes one campaign: goal, offer,
   platforms, audience segment, deadline. Copy `briefs/_template.md`.
3. **Ads** — output goes to `ads/<brand-slug>/<campaign-slug>/<platform>.md`, one file per platform.
4. **Check** — run `python3 scripts/check_limits.py <file>` on every ads file before calling it done.

## Rules for writing ads

- Read the brand file and the brief first. If either is missing or vague on goal, offer,
  audience or platform, ask before writing.
- Follow the platform limits in `reference/platform-specs.md`. Character counts include spaces.
- Use the frameworks in `reference/frameworks.md`; label each variation with the angle/framework used.
- Default to 5 variations per ad unit unless the brief says otherwise, each with a distinct angle
  (pain, benefit, social proof, urgency, curiosity, objection-handling...), not rewordings.
- Never invent facts: no made-up stats, testimonials, awards, prices, discounts or guarantees.
  Use only claims present in the brand file or brief; mark anything needing proof as `[VERIFY]`.
- Respect the brand's banned words and compliance notes. Avoid claims platforms reject
  (personal attributes like "Are you overweight?", before/after promises, guaranteed income, etc.).
- Every variation gets a clear CTA that matches the campaign goal.
- For image/video concepts, include a visual description and, when useful, an image-generation prompt.

## Output format for an ads file

Use the structure in `reference/output-format.md` so `scripts/check_limits.py` can validate it.

## Slash commands

- `/new-brand <name>` — interview me and create a brand file
- `/new-brief <brand> <campaign>` — interview me and create a campaign brief
- `/generate-ads <brief-file>` — write ads for every platform in the brief, then run the checker
- `/variations <ads-file> [angle]` — add more variations to an existing ads file
- `/critique <ads-file>` — score and improve existing ads

## Image generation (kie.ai)

- `scripts/kie_generate.py` calls kie.ai; the key comes from the `KIE_API_KEY` env var. Never ask
  the user to paste the key in chat, never print it, never commit it.
- Credits are scarce. Always run `credits` first, then a dry run (no `--yes`) and show the user
  the final prompt. Only add `--yes` after the user approves that exact prompt.
- Save prompts to `ads/<brand>/<campaign>/prompt-<n>.md` and images to `ads/<brand>/<campaign>/images/`.
- Ad text in images: keep it short (headline + CTA, ideally under ~8 words) and spell it out in
  quotes in the prompt. Use real product/logo photos as `--ref` images whenever available.
