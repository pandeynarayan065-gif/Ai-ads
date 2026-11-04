// Renders the HTML pages written by build_brand.py to PNG with the pre-installed Chromium.
//   node brand/misfits/render.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const jobs = JSON.parse(fs.readFileSync(path.join(__dirname, '_render_jobs.json'), 'utf8'));
  const browser = await chromium.launch();
  for (const j of jobs) {
    const page = await browser.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 1 });
    await page.goto('file://' + j.html);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: j.png, omitBackground: !!j.transparent, clip: { x: 0, y: 0, width: j.w, height: j.h } });
    await page.close();
    console.log('wrote', path.relative(process.cwd(), j.png));
  }
  await browser.close();
})();
