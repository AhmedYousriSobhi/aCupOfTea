// Browser smoke test for the built site.
//
//   python3 .docs/tools/stage_site.py --out _site
//   node .docs/tests/smoke.js _site
//
// Serves the staged site on a free port, opens it in headless Chromium at a
// desktop and a phone size, and checks what a reader would notice: the menu,
// a long page with its images, search, the page footer, the 404 page, formulas,
// diagrams, phone table cards, the phone image viewer, the theme button and
// sideways scrolling. Needs the `playwright` npm package (with Chromium).
// Exits 1 and names each failed check.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const root = path.resolve(process.argv[2] || '_site');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.md': 'text/markdown; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp' };

const server = http.createServer((req, res) => {
  const file = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!file.startsWith(root)) { res.writeHead(403); return res.end(); }
  fs.stat(file, (err, st) => {
    const target = !err && st.isDirectory() ? path.join(file, 'index.html') : file;
    fs.readFile(target, (e, data) => {
      if (e) { res.writeHead(404); return res.end('not found'); }
      res.writeHead(200, { 'Content-Type': TYPES[path.extname(target)] || 'application/octet-stream' });
      res.end(data);
    });
  });
});

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail });
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (ok || !detail ? '' : '  -> ' + detail));
}

async function open(browser, size, phone) {
  const ctx = await browser.newContext({ viewport: size, isMobile: phone, hasTouch: phone, colorScheme: 'light' });
  const page = await ctx.newPage();
  page.errors = [];
  page.setDefaultTimeout(8000);
  page.on('pageerror', (e) => page.errors.push(e.message.slice(0, 120)));
  page.libs = [];
  page.on('request', (r) => { const m = r.url().match(/\/npm\/(mermaid|katex)@/); if (m) page.libs.push(m[1]); });
  return page;
}

async function run(browser, base, label, size, phone) {
  const page = await open(browser, size, phone);
  const go = async (hash, wait = 3000) => { await page.goto(base + '/#/' + hash); await page.waitForTimeout(wait); };
  const c = (name, ok, detail) => check(`[${label}] ${name}`, ok, detail);

  await go('');
  const home = await page.evaluate(() => ({
    h1: (document.querySelector('.markdown-section h1') || {}).textContent,
    nav: document.querySelectorAll('.sidebar-nav li').length,
    recent: /Recently added/.test(document.body.textContent),
    cards: document.querySelectorAll('table.stack').length,
    time: !!document.querySelector('.reading-time'),
  }));
  c('home page renders with the menu', home.h1 === 'aCupOfTea' && home.nav > 50, JSON.stringify(home));
  c('home page lists recently added pages', home.recent);
  c('home page has no reading time', !home.time);
  if (phone) c('tables become cards on a phone', home.cards >= 1, 'stack tables: ' + home.cards);

  await go('fields/deep-learning/concepts/convolution', 4000);
  const conv = await page.evaluate(() => ({
    imgs: document.querySelectorAll('.markdown-section img').length,
    first: (() => { const i = document.querySelector('.markdown-section img'); return !!i && i.complete && i.naturalWidth > 0; })(),
    footer: (document.querySelector('.page-footer') || {}).textContent || '',
  }));
  c('long page has its images', conv.imgs >= 80, 'images: ' + conv.imgs);
  c('first image loads', conv.first);
  c('page footer has an edit link and a date', /Edit this page/.test(conv.footer) && /Last updated \d{4}-\d{2}-\d{2}/.test(conv.footer), conv.footer);
  const sideways = await page.evaluate(async () => {
    window.scrollTo(200, 0); await new Promise((r) => setTimeout(r, 150)); return window.scrollX;
  });
  c('no sideways scrolling', sideways === 0, 'scrollX ' + sideways);
  const prog = await page.evaluate(async () => {
    const before = !document.getElementById('back-to-top').hidden;
    window.scrollTo(0, document.documentElement.scrollHeight / 2);
    await new Promise((r) => setTimeout(r, 300));
    const bar = document.getElementById('read-progress');
    const t = bar.style.transform;
    const shown = !document.getElementById('back-to-top').hidden;
    const icon = Math.round(document.querySelector('#back-to-top svg').getBoundingClientRect().width);
    const nav = Math.round(document.querySelector('nav.app-nav').getBoundingClientRect().top);
    document.getElementById('back-to-top').click();
    await new Promise((r) => setTimeout(r, 1500));
    return { before, bar: !bar.hidden && /scaleX\(0\.[1-9]/.test(t), shown, icon, nav, back: Math.round(window.scrollY) };
  });
  c('progress bar and back-to-top work on a long page', !prog.before && prog.bar && prog.shown && prog.icon > 10 && prog.back < 20, JSON.stringify(prog));
  c('top menu stays on screen while scrolling', prog.nav === 0, 'menu top ' + prog.nav);
  c('pages without diagrams or formulas skip Mermaid and KaTeX', page.libs.length === 0, page.libs.join(', '));

  if (phone) {
    await page.evaluate(() => { const i = document.querySelector('.markdown-section img[src*="convolution-0"]'); if (i) i.scrollIntoView({ block: 'center' }); });
    await page.waitForTimeout(500);
    try {
      await page.tap('.markdown-section img[src*="convolution-0"]', { timeout: 4000 });
      await page.waitForTimeout(500);
      c('tapping an image opens the viewer', await page.evaluate(() => document.documentElement.style.overflow === 'hidden'));
    } catch (e) { c('tapping an image opens the viewer', false, e.message.split('\n')[0]); }
  }

  await go('fields/deep-learning/concepts/sequence-models');
  const strip = await page.evaluate(() => {
    const el = document.querySelector('.related-strip');
    const h1 = document.querySelector('.markdown-section h1');
    return { links: el ? el.querySelectorAll('a').length : 0, underTitle: !!el && !!h1 && h1.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING && el.getBoundingClientRect().top - h1.getBoundingClientRect().bottom < 120 };
  });
  const time = await page.evaluate(() => (document.querySelector('.markdown-section h1 ~ .reading-time') || {}).textContent || '');
  c('reading time is shown under the title', /^\d+ min read$/.test(time.trim()), time);
  c('related pages are linked right under the title', strip.links >= 1 && strip.underTitle, JSON.stringify(strip));

  await go('fields/benchmarks/hpl');
  c('formulas render', (await page.locator('.math-block .katex').count()) >= 8);
  await go('fields/system-administration/network', 4000);
  c('diagrams render', (await page.locator('.mermaid svg').count()) >= 3);
  await go('fields/benchmarks/stream');
  c('alerts render', (await page.locator('.alert.callout').count()) >= 1);

  for (const [kind, route] of [['script', 'programming/software-goals/robustness/script_RectangleClass.py'],
    ['notebook', 'programming/software-goals/robustness/nb_Robustness.ipynb']]) {
    await go(route);
    const code = await page.evaluate(() => ({
      head: !!document.querySelector('.code-file a[href*="github.com"]'),
      blocks: document.querySelectorAll('.markdown-section pre[data-lang="python"]').length,
      missing: /This page is not here/.test(document.body.textContent),
      colours: document.querySelectorAll('.markdown-section pre[data-lang="python"] .token.keyword').length,
    }));
    c(`a ${kind} link opens a readable page`, code.head && code.blocks >= 1 && !code.missing, JSON.stringify(code));
    if (kind === 'script') c('Python code is highlighted', code.colours >= 3, 'keywords: ' + code.colours);
  }

  await go('this-page-does-not-exist');
  c('missing page shows the friendly 404', /This page is not here/.test(await page.locator('.markdown-section').innerText()));

  await go('');
  if (phone) {
    const x = () => page.evaluate(() => Math.round(document.querySelector('aside.sidebar').getBoundingClientRect().x));
    const before = await x();
    // the menu button is `.sidebar-toggle-button` on Docsify 5; older builds also had an overlay `.sidebar-pin`
    for (const sel of ['.sidebar-toggle-button', '.sidebar-pin']) {
      if ((await x()) >= 0) break;
      await page.tap(sel, { timeout: 2000 }).catch(() => {});
      await page.waitForTimeout(800);
    }
    const after = await x();
    c('phone menu opens', before < 0 && after >= 0, `x ${before} -> ${after}`);
    // the menu stays open: on a phone the search box lives inside it
  }
  try {
    await page.locator('.srch input').fill('convolution');
    await page.waitForTimeout(3000);
    c('search finds pages', (await page.locator('.srch-panel a').count()) >= 3);
    await page.fill('.srch input', 'bias variance');
    await page.waitForTimeout(2500);
    await page.evaluate(() => document.querySelector('.srch-panel a.srch-item').click());
    await page.waitForTimeout(2000);
    const where = await page.evaluate(() => {
      const here = document.querySelector('.sidebar-nav a.here') || document.querySelector('.sidebar-nav li.active > a');
      return { found: !!here, hidden: !!here && !!here.closest('li.group.collapsed, li.group.collapsed *') && !!here.closest('ul') && [...document.querySelectorAll('.sidebar-nav li.group.collapsed')].some((g) => g.contains(here)) };
    });
    c('after a search result the menu marks and shows the current page', where.found && !where.hidden && (await page.locator('.sidebar-nav a.here').count()) === 1, JSON.stringify(where));
  } catch (e) { c('search finds pages', false, 'search box not usable: ' + e.message.split('\n')[0]); }

  const menu = await page.evaluate(() => !!document.getElementById('theme-toggle'));
  if (menu) {
    const look = () => page.evaluate(() => getComputedStyle(document.body).backgroundColor + '|' + getComputedStyle(document.querySelector('.sidebar')).backgroundColor);
    const seen = { light: await look() };
    for (const id of ['black', 'sepia', 'dark', 'midnight']) {
      await page.evaluate(() => document.getElementById('theme-toggle').click());
      await page.evaluate((t) => document.querySelector(`#theme-menu [data-choice="${t}"]`).click(), id);
      await page.waitForTimeout(300);
      seen[id] = await look();
    }
    const colours = new Set(Object.values(seen));
    c('theme list switches to five different looks', colours.size === 5, JSON.stringify(seen));
    c('black theme is really black', seen.black.startsWith('rgb(0, 0, 0)'), seen.black);
    await page.reload();
    await page.waitForTimeout(2500);
    c('theme choice survives a reload', (await look()) === seen.midnight);
    await page.evaluate(() => document.getElementById('theme-toggle').click());
    await page.evaluate(() => document.querySelector('#theme-menu [data-size="xl"]').click());
    await go('fields/deep-learning/concepts/sequence-models');
    const big = await page.evaluate(async () => {
      const px = parseFloat(getComputedStyle(document.querySelector('.markdown-section p')).fontSize);
      window.scrollTo(200, 0); await new Promise((r) => setTimeout(r, 150));
      return { px, wide: document.documentElement.scrollWidth - window.innerWidth, x: window.scrollX };
    });
    c('largest text size applies, fits the screen and is remembered', big.px >= 19 && big.wide <= 0 && big.x === 0, JSON.stringify(big));
  } else {
    // pages built before the theme list: the older single button
    const old = await page.evaluate(() => !!document.getElementById('docsify-darklight-theme'));
    if (old) {
      const a = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      await page.evaluate(() => document.getElementById('docsify-darklight-theme').click());
      await page.waitForTimeout(500);
      c('theme button switches the colours', a !== (await page.evaluate(() => getComputedStyle(document.body).backgroundColor)));
    }
  }
  c('no script errors', page.errors.length === 0, page.errors.join(' | '));
  await page.context().close();
}

(async () => {
  if (!fs.existsSync(path.join(root, 'index.html'))) { console.error('no index.html in ' + root); process.exit(2); }
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch();
  try {
    for (const [label, size, phone] of [['desktop', { width: 1280, height: 800 }, false], ['phone', { width: 390, height: 800 }, true]]) {
      try { await run(browser, base, label, size, phone); }
      catch (e) { check(`[${label}] run finished`, false, e.message.split('\n')[0]); }
    }
  } finally {
    await browser.close();
    server.close();
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length} of ${results.length} checks passed`);
  process.exit(failed.length ? 1 : 0);
})();
