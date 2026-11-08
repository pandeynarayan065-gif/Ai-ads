"""Build data/board.json: every pitchable brand from the cache, with contacts, signals and ready messages, for the
team lead board (artifact) and the PDF. Usage: python3 build_board.py"""
import json, re, urllib.parse
import leads

rows = []
for b in leads.brands():
    if b["score"] < 0:
        continue
    p = leads.profile_for(b["page_url"]) if b["page_url"] else None
    cat = (p or {}).get("category") or ""
    if re.search(r"creator|public figure|media|news|blogger|trainer|tour|agency|influencer|community", cat, re.I):
        continue
    cc = b["country"]
    phone = (p or {}).get("phone") or ""
    if cc == "IN" and phone.startswith("+") and not phone.startswith("+91"):
        continue
    if cc == "US" and phone.startswith("+") and not phone.startswith("+1"):
        continue
    wa, subj, email, dm = (leads.messages_us if cc == "US" else leads.messages)(b, p)
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("911800") or digits.startswith("1800") or cc != "IN":
        digits = ""
    em = (p or {}).get("email") or ""
    rows.append({
        "id": re.sub(r"[^a-z0-9-]", "-", b["domain"].lower())[:80],
        "country": cc, "brand": b["brand"], "domain": b["domain"], "score": b["score"],
        "category": cat or b["keywords"].split(",")[0].title(), "searched": b["keywords"],
        "ads_seen": b["active_ads"], "page_likes": b["page_likes"], "video_share": b["video_share"],
        "running_since": b["running_since"], "fb_page": b["page_url"],
        "website": (p or {}).get("website") or f"https://{b['domain']}",
        "email": em, "phone": phone, "has_contact": bool(em or phone),
        "wa_link": f"https://wa.me/{digits}?text={urllib.parse.quote(wa)}" if digits and wa else "",
        "msg_whatsapp": wa, "email_subject": subj, "msg_email": email, "msg_dm": dm,
        "sample_ad": b["sample_ad"][:220],
        "status": "new", "next_followup": "", "notes": "",
    })
json.dump(rows, open(leads.DATA / "board.json", "w"), indent=1, ensure_ascii=False)
print(len(rows), "leads |", sum(r["has_contact"] for r in rows), "with contact |",
      {c: sum(1 for r in rows if r["country"] == c) for c in ("IN", "US")})
