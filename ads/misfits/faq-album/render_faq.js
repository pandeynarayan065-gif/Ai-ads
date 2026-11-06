// Render faq.html slides to slide-1.png ... slide-5.png (1080x1350). Usage: node render_faq.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  await p.goto('file://' + path.join(__dirname, 'faq.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(500);
  for (let i = 1; i <= 5; i++) await p.locator('#s' + i).screenshot({ path: path.join(__dirname, `slide-${i}.png`) });
  await b.close();
})();
