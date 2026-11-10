"""Build site/dist/index.html from the site/index.html template + data/board.json (keeps each lead's first-seen date for the New tag).
Usage: python3 build_board.py && python3 update_site.py && ./deploy_vercel.sh"""
import datetime as dt, json, re
from pathlib import Path
here = Path(__file__).parent
tpl = (here / "site/index.html").read_text()          # committed template, no lead data
built = here / "site/dist/index.html"                  # gitignored build with the data
m = re.search(r"^const DATA=(.*);$", built.read_text() if built.exists() else "const DATA=[];", re.M)
prev = json.loads(m.group(1).replace("<\\/", "</"))
old = {d["id"]: d.get("added", "2026-11-08") for d in prev}
today = dt.date.today().isoformat()
rows = json.load(open(here / "data/board.json"))
shop = here / "data/shopify_leads.json"          # small stores from the public Shopify list (shopify_leads.py)
if shop.exists():
    seen = {r["id"] for r in rows}
    rows += [r for r in json.load(open(shop)) if r["id"] not in seen]
ids = {r["id"] for r in rows}
rows += [d for d in prev if d["id"] not in ids]   # never drop a lead the team may already be working
for r in rows:
    r["added"] = old.get(r["id"], today)
latest = max(r["added"] for r in rows)
blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
page = tpl.replace("const DATA=__DATA__;", "const DATA=" + blob + ";").replace("__LATEST__", json.dumps(latest))
page = page.replace("__UPDATED__", dt.date.today().strftime("%-d %b"))
built.parent.mkdir(exist_ok=True); built.write_text(page)
print(f"{len(rows)} leads in site, {sum(1 for r in rows if r['added'] == latest)} new ({latest}), {len(page)//1024} KB")
