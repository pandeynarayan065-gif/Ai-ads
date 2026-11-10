"""Build data/board.json: every pitchable brand from the cache, with contacts, signals and ready messages, for the
team lead board (Vercel site + claude.ai board) and the PDF. Usage: python3 build_board.py

Contacts come from the brand's Facebook page profile when we paid for one (leads.py enrich), otherwise from the
brand's own website (webcontacts.py, free). Lead ids are the domain, so claims and statuses survive rebuilds."""
import json, re, urllib.parse
import leads

web = json.loads((leads.DATA / "web_contacts.json").read_text()) if (leads.DATA / "web_contacts.json").exists() else {}


def norm_phone(raw, cc):
    d = re.sub(r"\D", "", raw or "")
    if not d:
        return ""
    if cc == "IN":
        d = d.lstrip("0")
        if len(d) == 10 and d[0] in "6789":
            d = "91" + d
        return "+" + d if d.startswith("91") and len(d) == 12 else (raw or "")
    if cc == "US":
        if len(d) == 10:
            d = "1" + d
        return "+" + d if d.startswith("1") and len(d) == 11 else (raw or "")
    return raw


rows = []
for b in leads.brands():
    if b["score"] < 0:
        continue
    p = leads.profile_for(b["page_url"]) if b["page_url"] else None
    w = web.get(b["domain"], {})
    cat = (p or {}).get("category") or ""
    if re.search(r"creator|public figure|media|news|blogger|trainer|tour|agency|influencer|community", cat, re.I):
        continue
    cc = b["country"]
    email = (p or {}).get("email") or w.get("email") or ""
    phone = norm_phone((p or {}).get("phone") or w.get("phone") or "", cc)
    wa_num = norm_phone(w.get("whatsapp") or "", cc) or (phone if cc == "IN" else "")
    if cc == "IN" and phone.startswith("+") and not phone.startswith("+91"):
        continue
    if cc == "US" and phone.startswith("+") and not phone.startswith("+1"):
        continue
    wa, subj, email_body, dm = (leads.messages_us if cc == "US" else leads.messages)(b, p)
    digits = re.sub(r"\D", "", wa_num)
    if digits.startswith("911800") or cc != "IN" or not re.fullmatch(r"91[6-9]\d{9}", digits):
        digits = ""          # WhatsApp only for Indian mobile numbers (landlines and toll-free can't take it)
    ig = w.get("instagram") or ""
    rows.append({
        "id": re.sub(r"[^a-z0-9-]", "-", b["domain"].lower())[:80],
        "country": cc, "brand": b["brand"], "domain": b["domain"], "score": b["score"],
        "category": cat or b["keywords"].split(",")[0].title(), "searched": b["keywords"],
        "ads_seen": b["active_ads"], "page_likes": b["page_likes"], "video_share": b["video_share"],
        "running_since": b["running_since"], "fb_page": b["page_url"],
        "website": (p or {}).get("website") or f"https://{b['domain']}",
        "email": email, "phone": phone, "instagram": ig,
        "has_contact": bool(email or phone or digits),
        "contact_source": "facebook page" if (p and ((p.get("email")) or p.get("phone"))) else ("website" if (email or phone) else ""),
        "wa_link": f"https://wa.me/{digits}?text={urllib.parse.quote(wa)}" if digits and wa else "",
        "msg_whatsapp": wa, "email_subject": subj, "msg_email": email_body, "msg_dm": dm,
        "sample_ad": b["sample_ad"][:220],
        "status": "new", "next_followup": "", "notes": "",
    })
json.dump(rows, open(leads.DATA / "board.json", "w"), indent=1, ensure_ascii=False)
print(len(rows), "leads |", sum(r["has_contact"] for r in rows), "with email/phone/WhatsApp |",
      sum(1 for r in rows if r["instagram"]), "with Instagram |", sum(1 for r in rows if r["wa_link"]), "WhatsApp-ready |",
      {c: sum(1 for r in rows if r["country"] == c) for c in ("IN", "US")})
