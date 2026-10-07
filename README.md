# AI Ads

A Claude Code workspace for generating ad copy and creative concepts.

## Quick start

1. `/new-brand Acme Coffee`: Claude asks questions and writes `brand/acme-coffee.md`
2. `/new-brief acme-coffee Fall Launch`: writes `briefs/YYYY-MM-DD-fall-launch.md`
3. `/generate-ads briefs/YYYY-MM-DD-fall-launch.md`: writes `ads/acme-coffee/fall-launch/<platform>.md`
4. `/critique` or `/variations` to iterate

## Layout

| Path | What |
|---|---|
| `CLAUDE.md` | Rules Claude follows when writing ads |
| `brand/` | One profile per brand (`_template.md` to start) |
| `briefs/` | One brief per campaign (`_template.md` to start) |
| `ads/` | Generated ads, `ads/<brand>/<campaign>/<platform>.md` |
| `reference/` | Platform specs, copywriting frameworks, output format |
| `scripts/check_limits.py` | Validates character limits: `python3 scripts/check_limits.py ads/` |
| `.claude/commands/` | The slash commands above |

Supported platforms: Google Search, Google Display, Meta (Facebook/Instagram), LinkedIn, TikTok, X.

## Image generation with kie.ai

1. Get your key at https://kie.ai/api-key.
2. Add it as the environment variable `KIE_API_KEY` in this cloud environment's settings
   (environment menu in the session title bar → Edit → environment variables), then start a new session.
   Running locally instead: put `KIE_API_KEY=...` in a `.env` file in the repo root (it's gitignored).
3. `python3 scripts/kie_generate.py credits` checks your balance.
4. `python3 scripts/kie_generate.py image --prompt-file <prompt.md> --out <dir> --ref product.jpg`
   does a dry run first. Add `--yes` to actually generate and spend credits.
