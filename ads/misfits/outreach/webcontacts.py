"""Free contact enrichment: read each brand's own website (home, contact page, Shopify contact-information policy)
for a public business email, phone, WhatsApp number and Instagram handle. No API credits.

  python3 webcontacts.py [--limit N] [--workers 12]

Writes data/web_contacts.json {domain: {email, phone, whatsapp, instagram, checked}}; domains already checked are
skipped, so re-runs only visit new brands. A handful of pages per site, one request at a time per site."""
import argparse, json, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import leads

OUT = leads.DATA / "web_contacts.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
PATHS = ["/", "/pages/contact", "/pages/contact-us", "/contact", "/contact-us", "/policies/contact-information",
         "/pages/about-us", "/policies/refund-policy"]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,10}")
BAD_EMAIL = re.compile(r"\.(png|jpe?g|gif|webp|svg|css|js)$|sentry|wixpress|example\.|domain\.com|email\.com|yourstore|"
                       r"yourdomain|@shopify\.com|@sentry|u003e|@2x|@3x|noreply|no-reply|privacy@|legal@|dpo@|abuse@|"
                       r"godaddy|cloudflare|@mail\.com$|test@", re.I)
GOOD_LOCAL = ("hello", "hi", "contact", "info", "team", "support", "care", "help", "customercare", "customer", "sales",
              "marketing", "partnerships", "collab", "business", "brand", "founder", "shop", "orders", "connect")
IG = re.compile(r"instagram\.com/([A-Za-z0-9._]{2,30})/?", re.I)
IG_SKIP = {"p", "reel", "reels", "explore", "accounts", "stories", "tv", "share", "shopify", "instagram", "_u", "direct"}
TEL = re.compile(r'href=["\']tel:([+0-9 ()\-.]{7,22})', re.I)
WA = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send/?\?phone=)\+?(\d{8,15})", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            if "html" not in (r.headers.get("Content-Type") or "html"):
                return ""
            return r.read(600_000).decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001  (dead sites, 403s, timeouts: just no data)
        return ""


def root_of(dom):
    parts = dom.split(".")
    return ".".join(parts[-3:]) if parts[-2] in ("co", "com", "org", "net") and len(parts) > 2 else ".".join(parts[-2:])


def pick_email(found, dom):
    root = root_of(dom).split(".")[0]
    cands = [e.strip(".").lower() for e in found if not BAD_EMAIL.search(e)]
    if not cands:
        return ""
    def rank(e):
        local, _, host = e.partition("@")
        return (0 if root in host else 1, 0 if any(local.startswith(g) for g in GOOD_LOCAL) else 1, len(e))
    return sorted(set(cands), key=rank)[0]


def visit(dom):
    base_hosts = [dom] + ([root_of(dom)] if root_of(dom) != dom else [])
    emails, phones, was, igs, checked = [], [], [], [], 0
    for host in base_hosts:
        for path in PATHS:
            html = fetch(f"https://{host}{path}")
            checked += 1
            if not html:
                if path == "/":
                    break           # site down or blocking: don't hammer the other paths
                continue
            emails += re.findall(r'mailto:([^"\'?<> ]+)', html, re.I) + EMAIL.findall(html)
            phones += TEL.findall(html)
            was += WA.findall(html)
            igs += [h for h in IG.findall(html) if h.lower() not in IG_SKIP]
            if emails and (phones or was) and igs:
                break
            time.sleep(0.4)
        if emails:
            break
    em = pick_email([urllib.parse.unquote(e) for e in emails], dom)
    ig = max(set(igs), key=igs.count) if igs else ""
    ph = re.sub(r"[^\d+]", "", phones[0]) if phones else ""
    return dom, {"email": em, "phone": ph, "whatsapp": was[0] if was else "", "instagram": ig, "checked": checked}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [b["domain"] for b in leads.brands() if b["score"] >= 0 and b["domain"] not in done]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(todo)} sites to read ({len(done)} already done)", flush=True)
    n = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for dom, info in ex.map(visit, todo):
            done[dom] = info; n += 1
            if n % 20 == 0:
                OUT.write_text(json.dumps(done, indent=1)); print(f"{n}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(done, indent=1))
    got = [d for d in done.values() if d["email"] or d["phone"] or d["whatsapp"]]
    print(f"done: {len(done)} sites, {len(got)} with email/phone/WhatsApp, "
          f"{sum(1 for d in done.values() if d['instagram'])} with Instagram")


if __name__ == "__main__":
    main()
