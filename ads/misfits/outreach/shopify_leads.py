"""Small-brand leads from a public Shopify store list (growthenginenowoslawski/shopify-master-list on GitHub, a
company-level CSV: domain, name, monthly visits, TikTok followers, technologies; no personal data).

Filter (in the caller's candidate file): runs the Facebook/Meta pixel (they buy Meta ads), 2K-10K TikTok followers,
1-50 people, not dropshipping / print-on-demand, 5+ products. This script then reads each store's own website to
  - decide the country (store currency, phone country code, address): keeps India and US only,
  - find a public email / phone / WhatsApp / Instagram (webcontacts.visit), and
  - write data/shopify_leads.json in the lead-board row format.

  python3 shopify_leads.py <candidates.json> [--max 700] [--workers 14]"""
import argparse, json, random, re, sys, urllib.parse
from concurrent.futures import ThreadPoolExecutor

import leads, webcontacts

OUT = leads.DATA / "shopify_leads.json"
US_STATES = r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\s+\d{5}\b"


def country_of(html, dom, info):
    cur = re.search(r'Shopify\.currency\s*=\s*\{"active":"([A-Z]{3})"', html)
    cur = cur.group(1) if cur else ""
    ph = re.sub(r"[^\d+]", "", (info.get("phone") or "") or (info.get("whatsapp") or ""))
    d = ph.lstrip("+")
    in_phone = d.startswith("91") and len(d) == 12
    us_phone = (d.startswith("1") and len(d) == 11) or (len(d) == 10 and not d.startswith(("0", "6", "7", "8", "9")))
    # country pickers list every country and currency, so page text alone proves nothing
    india = dom.endswith(".in") or cur == "INR" or in_phone
    us = not india and (us_phone or dom.endswith(".us") or bool(re.search(US_STATES, html)))
    return "IN" if india else "US" if us else ""


def messages(name, cc):
    wa = (f"Hi {name} team! I'm the founder of Misfits (misfitsagency.in). Came across {name} and loved the products. "
          "We make short product videos for growing D2C brands (AI product films + UGC-style ads) that look shot, "
          "without a shoot. Our two reels for Spraymax have 121K views on their page. "
          f"Can I send a free ad concept for {name}? Who should I send it to?")
    if cc == "US":
        subj = f"Free video ad concept for {name}"
        email = (f"Hi {name} team,\n\nI run Misfits (misfitsagency.in), a creative studio that makes AI product films "
                 f"and UGC-style video ads for growing DTC brands. Came across {name} and think your products would "
                 "look great in short-form video.\n\nOne offer: an Ad Sprint, 3 video ads + 2 statics in 5 days for "
                 "$299, fixed. Two reels we made for Spraymax have 121K views on their Instagram (public counts).\n\n"
                 "I'd like to make one concept ad of your product first, free, so you can judge the quality. Worth a "
                 "look?\n\nBook 15 min: calendly.com/misfitsagency-in/30min\n\nMisfits\nmisfitsagency.in\n"
                 f"{leads.US_ADDRESS}\nNot interested? Reply \"no thanks\" and I won't email again.")
        wa = ""
    else:
        subj = f"An ad concept for {name}"
        email = (f"Hi {name} team,\n\nI run Misfits (misfitsagency.in), an AI ad studio for D2C brands. Came across "
                 f"{name} and think your products would look great in short-form video.\n\nProof: two reels we made "
                 "for Spraymax have 121K views on their Instagram (public counts).\n\nOffer: an Ad Sprint, 3 video "
                 "ads + 2 statics in 5 days, fixed price. Happy to make one concept ad for you first, free, so you "
                 "can judge.\n\n15 minutes this week? calendly.com/misfitsagency-in/30min\n\n— Misfits\nmisfitsagency.in")
    dm = (f"Hey! Love what {name} is building. We're Misfits, we make AI product films + UGC-style ads for small "
          "brands (our Spraymax reels: 121K views). Made a quick concept idea for you, can I send it here?")
    return wa, subj, email, dm


def work(c):
    dom = c["domain"]
    html = webcontacts.fetch(f"https://{dom}/")
    if not html:
        return None
    _, info = webcontacts.visit(dom)
    cc = country_of(html, dom, info)
    if not cc:
        return None
    return c, info, cc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cands"); ap.add_argument("--max", type=int, default=700); ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--skip-first", type=int, default=0, help="mark the first N stores of the fixed order as already visited")
    a = ap.parse_args()
    have = set()
    if (leads.DATA / "board.json").exists():
        have = {r["domain"] for r in json.load(open(leads.DATA / "board.json"))}
    done = json.loads(OUT.read_text()) if OUT.exists() else []
    have |= {r["domain"] for r in done}
    board = {r["domain"] for r in json.load(open(leads.DATA / "board.json"))} if (leads.DATA / "board.json").exists() else set()
    allc = [c for c in json.load(open(a.cands)) if c["domain"] not in board]
    ind = [c for c in allc if c["domain"].endswith(".in")]
    rest = [c for c in allc if c["domain"].endswith((".com", ".us", ".co", ".shop", ".store"))]
    random.Random(7).shuffle(rest)
    order = ind + rest                               # same order every run
    chk_f = leads.DATA / "shopify_checked.json"     # every store already visited, kept or not
    checked = set(json.loads(chk_f.read_text())) if chk_f.exists() else set()
    if a.skip_first:
        checked |= {c["domain"] for c in order[: a.skip_first]}
    todo = [c for c in order if c["domain"] not in have and c["domain"] not in checked][: a.max]
    print(f"checking {len(todo)} stores ({len(ind)} .in first)", flush=True)
    n = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for res in ex.map(work, todo):
            n += 1
            if res:
                c, info, cc = res
                name = re.sub(r"\s+", " ", c["name"] or leads.brand_from_domain(c["domain"])).strip()[:60]
                phone = info.get("phone") or ""
                digits = re.sub(r"\D", "", info.get("whatsapp") or phone)
                if len(digits) == 10 and cc == "IN":
                    digits = "91" + digits
                wa_ok = cc == "IN" and re.fullmatch(r"91[6-9]\d{9}", digits)
                wa, subj, email, dm = messages(name, cc)
                score = 40 + (10 if info.get("email") else 0) + (5 if info.get("instagram") else 0) \
                    + (5 if 1000 <= c["visits"] <= 40000 else 0) + (5 if wa_ok else 0)
                done.append({
                    "id": re.sub(r"[^a-z0-9-]", "-", c["domain"])[:80], "country": cc, "brand": name,
                    "domain": c["domain"], "score": score, "category": "Shopify store", "searched": "shopify list",
                    "source": "shopify", "tiktok_followers": c["tiktok"], "monthly_visits": c["visits"],
                    "ads_seen": 0, "page_likes": 0, "video_share": 0, "running_since": "", "fb_page": "",
                    "website": f"https://{c['domain']}", "email": info.get("email") or "", "phone": phone,
                    "instagram": info.get("instagram") or "",
                    "has_contact": bool(info.get("email") or phone or wa_ok),
                    "contact_source": "website",
                    "wa_link": f"https://wa.me/{digits}?text={urllib.parse.quote(wa)}" if wa_ok and wa else "",
                    "msg_whatsapp": wa, "email_subject": subj, "msg_email": email, "msg_dm": dm,
                    "sample_ad": "", "status": "new", "next_followup": "", "notes": "",
                })
            checked.add(todo[n - 1]["domain"])
            if n % 25 == 0:
                chk_f.write_text(json.dumps(sorted(checked)))
                OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False))
                print(f"{n}/{len(todo)} checked, {len(done)} India/US leads, "
                      f"{sum(1 for d in done if d['has_contact'])} with contact", flush=True)
    OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False)); chk_f.write_text(json.dumps(sorted(checked)))
    print(f"done: {len(done)} leads ({sum(1 for d in done if d['country']=='IN')} IN, "
          f"{sum(1 for d in done if d['country']=='US')} US), {sum(1 for d in done if d['has_contact'])} with contact")


if __name__ == "__main__":
    main()
