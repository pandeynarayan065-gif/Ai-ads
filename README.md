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
