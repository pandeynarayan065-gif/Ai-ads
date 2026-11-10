"""Download every product image from avrana.co (Shopify products.json) into product-images/<product>/NN.jpg at
1600 px wide, plus an overview contact sheet. Re-run any time; images are gitignored (they're the brand's assets).
Usage: python3 fetch_images.py"""
import io, json, re, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

HERE = Path(__file__).parent; OUT = HERE / "product-images"
UA = {"User-Agent": "Mozilla/5.0"}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
products = json.loads(get("https://avrana.co/products.json?limit=250"))["products"]
jobs = []
for p in products:
    d = OUT / p["handle"]; d.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(p["images"], 1):
        jobs.append((p["title"], img["src"] + ("&" if "?" in img["src"] else "?") + "width=1600", d / f"{i:02d}.jpg"))
def dl(j):
    title, url, path = j
    if not path.exists():
        Image.open(io.BytesIO(get(url))).convert("RGB").save(path, quality=90)
    return j
list(ThreadPoolExecutor(10).map(dl, jobs))
# overview: one row per product, first 8 images
rows = [(p["title"], sorted((OUT / p["handle"]).glob("*.jpg"))[:8]) for p in products]
T, W = 150, 8
sheet = Image.new("RGB", (220 + W * (T + 6), len(rows) * (T + 6) + 6), (245, 245, 242)); dr = ImageDraw.Draw(sheet)
for r, (title, files) in enumerate(rows):
    y = 6 + r * (T + 6); dr.text((8, y + T // 2 - 6), title[:30], fill=(20, 20, 20))
    for c, f in enumerate(files):
        im = Image.open(f); im.thumbnail((T, T)); sheet.paste(im, (220 + c * (T + 6), y))
sheet.save(HERE / "product-images-overview.jpg", quality=85)
print(f"{len(products)} products, {len(jobs)} images -> {OUT}")
