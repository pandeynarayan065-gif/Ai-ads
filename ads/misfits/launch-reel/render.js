// Render scene.html frame by frame (deterministic, no dropped frames) and pipe to ffmpeg.
// Usage: NODE_PATH=<dir with node_modules> node render.js <three.module.js> <out.mp4> [fps] [--stills t1,t2,...]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const [threePath, out, fpsArg, flag, list] = process.argv.slice(2);
const fps = +fpsArg || 30, DUR = 18.6, here = __dirname, repo = path.resolve(here, '../../..');
const files = {
  'three.module.js': threePath,
  'product.jpg': path.join(here, 'product.jpg'),
  'fonts/Archivo-VF.ttf': path.join(repo, 'brand/misfits/fonts/Archivo-VF.ttf'),
  'fonts/Inter-VF.ttf': path.join(repo, 'brand/misfits/fonts/Inter-VF.ttf'),
  'scene.html': path.join(here, 'scene.html'),
};
(async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => m.type() === 'error' && console.error('page:', m.text()));
  p.on('pageerror', e => console.error('pageerror:', e.message));
  await p.route('http://reel.local/**', r => {
    const f = files[new URL(r.request().url()).pathname.slice(1)];
    if (!f) return r.fulfill({ status: 404 });
    const ct = { '.js': 'text/javascript', '.html': 'text/html', '.jpg': 'image/jpeg', '.ttf': 'font/ttf' }[path.extname(f)];
    r.fulfill({ body: fs.readFileSync(f), contentType: ct });
  });
  await p.goto('http://reel.local/scene.html');
  await p.waitForFunction('window.ready === true', null, { timeout: 60000 });
  if (flag === '--stills') {
    for (const t of list.split(',')) {
      await p.evaluate(t => window.renderAt(t), +t);
      await p.screenshot({ path: `${out}-${t}.png` });
    }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const n = Math.round(DUR * fps);
    for (let i = 0; i < n; i++) {
      await p.evaluate(t => window.renderAt(t), i / fps);
      const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 60 === 0) console.log(`frame ${i}/${n}`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await b.close();
})();
