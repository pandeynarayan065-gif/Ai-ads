# Misfits outreach engine

Goal (Narayan, 8 Nov): scale with clients at **$250–300 each** (≈ ₹21–25k). Sell one thing: the **Ad Sprint**,
3 video ads + 2 statics in 5 days, fixed price, 50% upfront. Upsell a monthly retainer after the sprint.

## 1. Leads (`leads.py`)
Indian D2C brands running Meta ads **right now** (they already pay for ads, so they need creative), scored and enriched
with the public business email/phone from their Facebook page. Marketplaces, apps, giants (>1M page likes or a known
corporate) and one-ad testers are filtered out. Score favours: more active ads, smaller pages, mostly-static ads
(the easiest pitch for video), `.in` domains.

```bash
cd ads/misfits/outreach
python3 leads.py search --pages 2 --max-credits 60        # 30 keywords x 2 pages ~ 60 credits
python3 leads.py enrich --max-credits 200                 # contacts for the best brands
python3 leads.py export                                   # data/leads.csv, data/outreach.csv, data/tracker.csv
```
**US (8 Nov):** `search --country US`, `enrich --country US`, `export --country US` -> `data/*-us.csv`. US pitch is
email + IG DM (no WhatsApp), $299 Ad Sprint, and a CAN-SPAM footer: a real postal address (fill in `US_ADDRESS` in
`leads.py` before sending) and an opt-out line; honour every "no thanks". First US run: 10 keywords + 20 profiles =
30 credits -> 11 brands with email (Respected Roots, Brickell Men's Products, Joah Brown, Kitsch, Hygiene Hero, ...).
Creator, media and agency pages are skipped automatically (the ad ran on a creator's page, not the brand's).
- Cost: ScrapeCreators, 1 credit per call, cached. First run (8 keywords, 1 page + 18 profiles) = 26 credits ->
  13 brands with contact details: **~2 credits per contactable lead**, so 1,000 leads ≈ 2,000–2,500 credits.
- Add keywords to `KEYWORDS` for new categories. Edit `status`, `last_contact`, `next_followup`, `notes` in
  `data/tracker.csv`; `export` keeps your edits.
- `data/outreach-<cc>.csv` has, per brand: WhatsApp message + one-tap `wa.me` link, email subject/body + `mailto:` link,
  IG DM. **A person sends each one.** No auto-sending: WhatsApp bans bulk unsolicited messages (number gets banned) and
  bulk cold email from a new domain lands in spam.
- The pitch says only what we know: we saw their Meta ads (never a count: the search sees a sample), Spraymax 121K
  views (re-check the public count before a batch), the sprint offer, a free concept.

**Free contacts (10 Nov):** `python3 webcontacts.py` reads each brand's own site (home, contact page, Shopify
contact-information policy) for a public email, phone, WhatsApp and Instagram, so credits go only on searches
(1 credit = 30 ads). 36 searches -> 331 new brands, ~270 with a contact: about 7 contactable leads per credit.
Update the live board: `python3 build_board.py && python3 update_site.py && ./deploy_vercel.sh` (keeps every lead
already on the board, and the team's claims/statuses, which live in Redis by lead id). Lead data (data/, and the
DATA line in site/index.html) stays out of git; the live site is the copy of record.

## 2. Sequence (per brand)
| Day | Channel | Message |
|---|---|---|
| 0 | WhatsApp (business number) **or** email | `whatsapp_msg` / `email_body`: who we are, proof, "can I send a free concept?" |
| 0 | IG DM | `ig_dm` (only if they post actively) |
| 3 | same channel | "Hi, just following up on this 🙂 Happy to send the concept." |
| 5 | top 10 of the week only | **The concept itself**: a 6–10 s ad of their real product (Seedream start frame + Omni Flash, ~$1), "Made this for [brand], no brief. Want 3 more?" |
| 10 | email | Break-up: "Closing the loop. If ads aren't a priority now, no worries. Concept's yours to keep." |

Rules: one message per step, working hours (10–6, Mon–Sat), stop at the first "no", mark `status` = `no`.

## 3. Daily rhythm
- 30 new contacts a day (WhatsApp + email), plus that day's follow-ups.
- 2 custom concepts a day for the highest scores (about 10 a week).
- Calls -> 30-min Calendly; send the sprint proposal the same day.

## 4. The maths (rough, to be replaced by your own numbers after week 1)
Cold outreach with a free custom concept typically gets low single-digit to ~10% replies, and a fraction of those
book and buy. Track it in `tracker.csv` (`python3 leads.py status`) and adjust. Illustration only:
1,000 contacts -> ~50 replies -> ~15 calls -> ~4–6 sprints ($1–1.8k), and the retainers come from the sprints.
