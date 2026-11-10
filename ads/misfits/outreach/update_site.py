"""Put the latest data/board.json into site/index.html (keeps each lead's first-seen date for the New tag).
Usage: python3 build_board.py && python3 update_site.py && ./deploy_vercel.sh"""
import datetime as dt, json, re
from pathlib import Path
here = Path(__file__).parent
page = (here / "site/index.html").read_text()
page = re.sub(r"^const LATEST=.*\n", "", page, flags=re.M)   # drop the old marker; re-added below
m = re.search(r"^const DATA=(.*);$", page, re.M)
prev = json.loads(m.group(1).replace("<\\/", "</"))
old = {d["id"]: d.get("added", "2026-11-08") for d in prev}
today = dt.date.today().isoformat()
rows = json.load(open(here / "data/board.json"))
ids = {r["id"] for r in rows}
rows += [d for d in prev if d["id"] not in ids]   # never drop a lead the team may already be working
for r in rows:
    r["added"] = old.get(r["id"], today)
latest = max(r["added"] for r in rows)
blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
page = page[:m.start()] + f"const DATA={blob};\nconst LATEST={json.dumps(latest)};" + page[m.end():]
page = re.sub(r"updated (__UPDATED__|\d{1,2} \w{3})", "updated " + dt.date.today().strftime("%-d %b"), page)
(here / "site/index.html").write_text(page)
print(f"{len(rows)} leads in site, {sum(1 for r in rows if r['added'] == latest)} new ({latest}), {len(page)//1024} KB")
