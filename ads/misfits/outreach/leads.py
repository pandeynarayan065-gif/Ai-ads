"""Misfits lead engine: find Indian D2C brands that are running Meta ads right now, enrich them with their public
business contact details, score them, and write personalised outreach (WhatsApp / email / IG DM) to a tracker.

Source: ScrapeCreators (Meta Ad Library search + Facebook page profile). The API key is injected by the network proxy
for api.scrapecreators.com; locally, set SCRAPECREATORS_API_KEY. 1 credit per call; every response is cached in
data/cache/, so re-runs are free.

  python3 leads.py search  --pages 3                      # ad-library search over the keyword list (30 ads/page)
  python3 leads.py enrich  --max-credits 50               # page profiles for the best-scoring brands not yet enriched
  python3 leads.py export                                 # data/leads.csv + data/outreach.csv (messages + links)
  python3 leads.py status                                 # funnel counts from the tracker

Nothing is sent automatically: WhatsApp and email both ban unsolicited bulk sending. The export gives one-tap
wa.me / mailto links so a person sends each message, and the tracker holds the follow-up dates."""
import argparse, csv, datetime as dt, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"; CACHE = DATA / "cache"
API = "https://api.scrapecreators.com"
KEY = os.environ.get("SCRAPECREATORS_API_KEY", "proxy-injected")   # the proxy replaces this header

# categories that match our proof (Spraymax = grooming) and buy creative often
KEYWORDS = ["hair spray", "hair wax", "beard oil", "face wash", "sunscreen", "serum", "perfume", "body spray",
            "deodorant", "lip balm", "protein powder", "cold coffee", "energy drink", "healthy snacks", "granola",
            "sneakers", "streetwear", "oversized t-shirt", "kurta", "silver jewellery", "watches", "bags",
            "home decor", "candles", "pet food", "baby care", "phone case", "earbuds", "skincare men", "ayurvedic"]
# marketplaces, apps and giants: not a brand we can pitch, or one with an in-house team
SKIP_DOMAINS = {"amazon.in", "amazon.com", "flipkart.com", "myntra.com", "nykaa.com", "blinkit.com", "zeptonow.com",
                "swiggy.com", "play.google.com", "apps.apple.com", "meesho.com", "ajio.com", "jiomart.com",
                "walmart.com", "walmart.ca", "target.com", "etsy.com", "ebay.com", "bestbuy.com", "costco.com", "sephora.com", "ulta.com", "tiktok.com", "shop.app", "bigbasket.com", "tatacliq.com", "firstcry.com", "purplle.com",
                "instagram.com", "facebook.com", "fb.com", "google.com", "forms.gle", "shopify.com", "wa.me", "whatsapp.com", "youtube.com", "linktr.ee", "bit.ly", "instacart.com", "urlgeni.us", "amzlink.to", "amzn.to", "geni.us", "beacons.ai", "stan.store", "maps.app.goo.gl", "goo.gl", "g.page", "maps.google.com", "forms.office.com", "calendly.com", "wa.link"}
MAX_LIKES = 1_000_000      # bigger pages almost always have an agency already
MIN_ADS = 2                # one ad is a test; two or more means a budget
BIG = re.compile(r"nestl|starbucks|unilever|hindustan|tata |reliance|itc |amazon|samsung|apple|loreal|l'oreal|nivea|dabur|marico|emami|godrej|himalaya|colgate|p&g|procter|walmart|target|nike|nykaa|myntra|ajio|tata|adidas|coca|pepsi|kraft|johnson|gillette|dove|axe|old spice|oldspice|meta |google", re.I)


def call(path, **params):
    q = urllib.parse.urlencode(params)
    f = CACHE / (hashlib.sha1(f"{path}?{q}".encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text()), False
    req = urllib.request.Request(f"{API}{path}?{q}", headers={"x-api-key": KEY})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read())
            break
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    CACHE.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps(d))
    return d, True


def domain(url):
    h = urllib.parse.urlparse(url or "").netloc.lower()
    return h[4:] if h.startswith("www.") else h


def load_ads():
    ads = []
    for f in CACHE.glob("*.json"):
        d = json.loads(f.read_text())
        for a in d.get("searchResults") or []:
            a["_kw"] = d.get("_kw", ""); a["_country"] = d.get("_country", "IN")
            ads.append(a)
    return ads


def cmd_search(a):
    spent = 0
    kws = a.keywords.split(",") if a.keywords else KEYWORDS
    for kw in kws:
        cursor = None
        for page in range(a.pages):
            params = {"query": kw, "country": a.country, "status": "ACTIVE"}
            if cursor:
                params["cursor"] = cursor
            d, fresh = call("/v1/facebook/adLibrary/search/ads", **params)
            spent += fresh
            # remember which keyword found these ads
            f = CACHE / (hashlib.sha1(f"/v1/facebook/adLibrary/search/ads?{urllib.parse.urlencode(params)}".encode()).hexdigest() + ".json")
            d["_kw"] = kw; d["_country"] = a.country; f.write_text(json.dumps(d))
            n = len(d.get("searchResults") or [])
            print(f"{kw!r} p{page + 1}: {n} ads{' (cached)' if not fresh else ''}  credits left {d.get('credits_remaining')}")
            cursor = d.get("cursor")
            if not cursor or not n:
                break
            if spent >= a.max_credits:
                sys.exit(f"stopped at --max-credits {a.max_credits}")


def brand_from_domain(dom):
    parts = [x for x in dom.split(".") if x not in ("www", "shop", "store", "order", "buy", "get", "try", "in", "com", "co", "us", "io", "net")]
    name = parts[0] if parts else dom
    return re.sub(r"[-_]+", " ", name).title()


def brands():
    """Group ads by the brand behind them: the landing-page domain (creators' branded posts point to the brand)."""
    b = defaultdict(lambda: {"ads": 0, "pages": defaultdict(int), "likes": 0, "formats": defaultdict(int),
                             "ctas": defaultdict(int), "kw": set(), "sample": "", "first": None, "page_urls": {},
                             "country": defaultdict(int)})
    for ad in load_ads():
        s = ad.get("snapshot") or {}
        dom = domain(s.get("link_url"))
        if not dom or dom in SKIP_DOMAINS or any(dom.endswith("." + x) for x in SKIP_DOMAINS):
            continue
        r = b[dom]
        r["ads"] += 1
        name = s.get("page_name") or ad.get("page_name") or ""
        r["pages"][name] += 1
        r["page_urls"][name] = s.get("page_profile_uri") or ""
        r["likes"] = max(r["likes"], s.get("page_like_count") or 0)
        r["formats"][s.get("display_format") or "?"] += 1
        r["ctas"][s.get("cta_text") or "?"] += 1
        r["kw"].add(ad.get("_kw", "")); r["country"][ad.get("_country", "IN")] += 1
        body = ((s.get("body") or {}).get("text") or "").strip()
        if body and len(body) > len(r["sample"]):
            r["sample"] = body[:300]
        st = ad.get("start_date")
        if st and (r["first"] is None or st < r["first"]):
            r["first"] = st
    out = []
    for dom, r in b.items():
        page = max(r["pages"], key=r["pages"].get)   # the page that runs most of the ads is usually the brand's own
        fmt = dict(r["formats"])
        video = fmt.get("VIDEO", 0) / max(1, r["ads"])
        score = min(r["ads"], 20) * 3 + (15 if r["likes"] < 300_000 else 5) + (10 if video < 0.5 else 0) \
            + (5 if dom.endswith(".in") or dom.endswith(".com") else 0)
        if r["likes"] > MAX_LIKES or BIG.search(page) or BIG.search(dom) or "--" in dom \
                or re.match(r"^(go|programs|apps?|link|l|click|track|lp)\.", dom):
            score -= 100
        elif r["ads"] < MIN_ADS:
            score -= 10        # seen once in our sample: still a live advertiser, just less proof of budget
        if re.fullmatch(r"[a-z0-9._]+", page or ""):
            page = brand_from_domain(dom)   # the ad ran on a creator's handle: name the brand from its domain
        out.append({"country": max(r["country"], key=r["country"].get), "domain": dom, "brand": page, "page_url": r["page_urls"].get(page, ""), "active_ads": r["ads"],
                    "page_likes": r["likes"], "video_share": round(video, 2), "formats": fmt,
                    "keywords": ",".join(sorted(r["kw"])), "sample_ad": r["sample"], "score": score,
                    "running_since": dt.date.fromtimestamp(r["first"]).isoformat() if r["first"] else ""})
    return sorted(out, key=lambda x: -x["score"])


def profile_for(url):
    f = CACHE / (hashlib.sha1(f"/v1/facebook/profile?{urllib.parse.urlencode({'url': url})}".encode()).hexdigest() + ".json")
    return json.loads(f.read_text()) if f.exists() else None


def cmd_enrich(a):
    spent = 0
    for b in brands():
        if b["score"] < 0 or not b["page_url"] or "facebook.com/" not in b["page_url"]:
            continue
        if a.country and b["country"] != a.country:
            continue
        if profile_for(b["page_url"]) is not None:
            continue
        if spent >= a.max_credits:
            break
        d, fresh = call("/v1/facebook/profile", url=b["page_url"])
        spent += fresh
        print(f"{b['brand']:<30} {d.get('email') or '-':<32} {d.get('phone') or '-':<18} {d.get('category') or ''}")
    print(f"spent {spent} credits")


def first_name_greeting(brand):
    return f"Hi {brand} team"


US_ADDRESS = "[VERIFY: Misfits business postal address, required by CAN-SPAM]"


def messages_us(b, p):
    video = b["video_share"]
    angle = ("saw your Meta ads, and the ones we found are mostly static images" if video < 0.5
             else "saw your video ads on Meta")
    subj = f"Video ad concept for {b['brand']}"
    email = (f"Hi {b['brand']} team,\n\nI run Misfits (misfitsagency.in), a creative studio that makes AI product films "
             f"and UGC-style video ads for DTC brands. I {angle}.\n\nOne offer: an Ad Sprint, 3 video ads + 2 statics "
             f"in 5 days for $299, fixed. Two reels we made for Spraymax have 121K views on their Instagram (public counts).\n\n"
             f"I'd like to make one concept ad of your product first, free, so you can judge the quality. Worth a look?\n\n"
             f"Book 15 min: calendly.com/misfitsagency-in/30min\n\nMisfits\nmisfitsagency.in\n{US_ADDRESS}\n"
             f"Not interested? Reply \"no thanks\" and I won't email again.")
    dm = (f"Hey! Big fan of what {b['brand']} is doing. We're Misfits, we make AI product films + UGC-style ads for DTC "
          f"brands (our Spraymax reels: 121K views). Mind if I send a free concept ad for you here?")
    return "", subj, email, dm


def messages(b, p):
    video = b["video_share"]
    # we only see the ads our keyword search matched, never the brand's full count: don't quote a number
    angle = ("saw your ads on Meta, and the ones we found are mostly static images" if video < 0.5
             else "saw your video ads on Meta")
    hook = ("We make product films that look shot, without a shoot, so you can test video hooks fast."
            if video < 0.5 else "We make product films that look shot, without a shoot, so you can test more hooks, faster.")
    wa = (f"{first_name_greeting(b['brand'])}! I'm the founder of Misfits (misfitsagency.in). I {angle}. {hook} "
          f"Our two reels for Spraymax have 121K views on their page. Can I send a free ad concept for {b['brand']}? "
          f"Who should I send it to?")
    email_subj = f"An ad concept for {b['brand']}"
    email = (f"{first_name_greeting(b['brand'])},\n\nI run Misfits (misfitsagency.in), an AI ad studio for D2C brands. "
             f"I {angle}. {hook}\n\nProof: two reels we made for Spraymax have 121K views on their "
             f"Instagram (public counts).\n\nOffer: an Ad Sprint, 3 video ads + 2 statics in 5 days, fixed price. "
             f"Happy to make one concept ad for {b['brand']} first, free, so you can judge.\n\n"
             f"15 minutes this week? calendly.com/misfitsagency-in/30min\n\n— Misfits\nmisfitsagency.in")
    dm = (f"Hey! Love what {b['brand']} is doing. We're Misfits, we make AI product films for D2C brands "
          f"(Spraymax reels: 121K views). Made a quick concept idea for you, can I send it here?")
    return wa, email_subj, email, dm


def cmd_export(a):
    DATA.mkdir(exist_ok=True)
    rows, out = [], []
    tracker = {}
    tf = DATA / f"tracker{('-' + a.country.lower()) if a.country else ''}.csv"
    if tf.exists():
        tracker = {r["domain"]: r for r in csv.DictReader(tf.open())}
    for b in brands():
        p = profile_for(b["page_url"]) if b["page_url"] else None
        row = {k: b[k] for k in ("country", "score", "brand", "domain", "active_ads", "page_likes", "video_share", "running_since",
                                 "keywords", "page_url")}
        row.update({"email": (p or {}).get("email") or "", "phone": (p or {}).get("phone") or "",
                    "website": (p or {}).get("website") or "", "category": (p or {}).get("category") or "",
                    "fb_followers": (p or {}).get("followerCount") or ""})
        rows.append(row)
        if b["score"] < 0 or not (row["email"] or row["phone"]):
            continue
        cc = b["country"]
        if re.search(r"creator|public figure|media|news|blogger|trainer|tour|agency|influencer", row["category"], re.I):
            continue           # a creator's or publisher's page, not the brand: find the brand by hand
        if a.country and cc != a.country:
            continue
        if cc == "IN" and row["phone"].startswith("+") and not row["phone"].startswith("+91"):
            continue           # not an Indian business
        if cc == "US" and row["phone"].startswith("+") and not row["phone"].startswith("+1"):
            continue           # not a US business
        if cc == "US" and not row["email"]:
            continue           # US outreach is email + DM
        wa, subj, email, dm = (messages_us if cc == "US" else messages)(b, p)
        digits = re.sub(r"\D", "", row["phone"])
        if digits.startswith("911800") or digits.startswith("1800"):
            digits = ""       # toll-free: not on WhatsApp
        t = tracker.get(b["domain"], {})
        out.append({"country": cc, "brand": b["brand"], "domain": b["domain"], "score": b["score"], "email": row["email"],
                    "phone": row["phone"],
                    "whatsapp_link": f"https://wa.me/{digits}?text={urllib.parse.quote(wa)}" if digits and wa else "",
                    "mailto_link": f"mailto:{row['email']}?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(email)}" if row["email"] else "",
                    "whatsapp_msg": wa, "email_subject": subj, "email_body": email, "ig_dm": dm,
                    "status": t.get("status", "new"), "last_contact": t.get("last_contact", ""),
                    "next_followup": t.get("next_followup", ""), "notes": t.get("notes", "")})
    sfx = f"-{a.country.lower()}" if a.country else ""
    with (DATA / f"leads{sfx}.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with (DATA / f"outreach{sfx}.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["brand"]); w.writeheader(); w.writerows(out)
    with tf.open("w", newline="") as f:     # tracker keeps your status edits across exports
        keys = ["domain", "brand", "status", "last_contact", "next_followup", "notes"]
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in keys})
    good = [r for r in rows if int(r["score"]) >= 0]
    print(f"brands: {len(rows)} | pitchable: {len(good)} | with contact: {len(out)} -> data/leads{sfx}.csv, data/outreach{sfx}.csv, {tf.name}")


def cmd_status(a):
    tf = DATA / "tracker.csv"
    if not tf.exists():
        sys.exit("no tracker yet: run export")
    c = defaultdict(int)
    for r in csv.DictReader(tf.open()):
        c[r["status"]] += 1
    print(dict(c))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("search"); s.add_argument("--pages", type=int, default=2); s.add_argument("--keywords")
    s.add_argument("--country", default="IN", help="2-letter country code, e.g. IN, US")
    s.add_argument("--max-credits", type=int, default=60); s.set_defaults(f=cmd_search)
    e = sp.add_parser("enrich"); e.add_argument("--max-credits", type=int, default=30)
    e.add_argument("--country", default="", help="only brands from this country"); e.set_defaults(f=cmd_enrich)
    x = sp.add_parser("export"); x.add_argument("--country", default="", help="only this country (IN, US); default all")
    x.set_defaults(f=cmd_export)
    sp.add_parser("status").set_defaults(f=cmd_status)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
