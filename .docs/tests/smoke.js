// Browser smoke test for the built site.
//
//   python3 .docs/tools/stage_site.py --out _site
//   node .docs/tests/smoke.js _site [chromium|webkit]
//
// Serves the staged site on a free port, opens it in headless Chromium (or
// WebKit, the engine of every iPhone browser) at a
// desktop and a phone size, and checks what a reader would notice: the menu,
// a long page with its images, search, the page footer, the 404 page, formulas,
// diagrams, phone table cards, the phone image viewer, the theme button and
// sideways scrolling, and reading a visited page offline. Needs the `playwright` npm package (with the browser).
// Every check name starts with the engine, so a failure says where it broke.
// Exits 1 and names each failed check.
const http = require('http');
const fs = require('fs');
const path = require('path');
const playwright = require('playwright');

const root = path.resolve(process.argv[2] || '_site');
const engine = process.argv[3] || 'chromium';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.md': 'text/markdown; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp' };

let serverDown = false; // the offline check also stops the server, so nothing can come from the network
const server = http.createServer((req, res) => {
  if (serverDown) return req.socket.destroy();
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
  // the Content-Security-Policy blocks silently; record every refusal
  await page.addInitScript(() => {
    window.__csp = [];
    document.addEventListener('securitypolicyviolation', (e) => window.__csp.push(e.violatedDirective + ' ' + (e.blockedURI || 'inline') + ' at ' + (e.sourceFile || '').split('/').pop() + ':' + e.lineNumber + ' on ' + location.hash));
  });
  page.libs = [];
  page.on('request', (r) => { const m = r.url().match(/\/npm\/(mermaid|katex)@/); if (m) page.libs.push(m[1]); });
  return page;
}

async function run(browser, base, label, size, phone) {
  const page = await open(browser, size, phone);
  const go = async (hash, wait = 3000) => { await page.goto(base + '/#/' + hash); await page.waitForTimeout(wait); };
  const c = (name, ok, detail) => check(`[${engine} ${label}] ${name}`, ok, detail);

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
  if (phone) {
    const bar = await page.evaluate(async () => {
      window.scrollTo(0, 3000); await new Promise((r) => setTimeout(r, 300));
      const t = document.getElementById('theme-toggle').getBoundingClientRect();
      const corner = document.querySelector('.github-corner');
      return { top: Math.round(t.top), right: Math.round(window.innerWidth - t.right),
        corner: !!corner && corner.getBoundingClientRect().width > 0, github: !!document.querySelector('#menu-github a[href*="github.com"]') };
    });
    c('theme button sits in the top bar on the right and stays there', bar.top >= 0 && bar.top < 12 && bar.right < 20, JSON.stringify(bar));
    c('GitHub link moves from the corner into the menu', !bar.corner && bar.github, JSON.stringify(bar));
  }
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
  const nxt = await page.evaluate(async () => {
    const a = document.querySelector('.pagination-item--next a');
    if (!a) return null;
    for (let i = 0; i < 3; i++) {  // late images move the end of the page: scroll until Next is steady
      a.scrollIntoView({ block: 'end' });
      await new Promise((r) => setTimeout(r, 500));
    }
    window.scrollTo(0, document.documentElement.scrollHeight);
    await new Promise((r) => setTimeout(r, 400));
    const gap = document.getElementById('back-to-top').getBoundingClientRect().top - document.querySelector('.pagination-item--next').getBoundingClientRect().bottom;
    a.click();
    await new Promise((r) => setTimeout(r, 2000));
    return { y: Math.round(window.scrollY), gap: Math.round(gap) };
  });
  c('Next opens the next page at its top, clear of back-to-top', nxt && nxt.y < 20 && nxt.gap >= 0, JSON.stringify(nxt));

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
    const sizes = await page.evaluate(() => ['button.sidebar-toggle', '#theme-toggle'].map((sel) => {
      const r = document.querySelector(sel).getBoundingClientRect();
      return [sel, Math.round(r.width), Math.round(r.height)];
    }));
    c('menu and theme buttons are at least 44px to tap', sizes.every(([, w, h]) => w >= 44 && h >= 44), JSON.stringify(sizes));
    const edge = await page.evaluate(() => {
      const el = document.elementFromPoint(20, window.innerHeight / 3);
      return !!el && !el.closest('.sidebar-toggle');
    });
    c('text near the left edge is not covered by the menu button', edge);
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
    // a page link in the menu opens the page and closes the menu
    try {
      await page.evaluate(() => { const g = [...document.querySelectorAll('.sidebar-nav li.group')].find((l) => /Tips/.test(l.firstElementChild.textContent)); if (g) g.click(); });
      await page.waitForTimeout(300);
      await page.tap('.sidebar-nav a[href*="tips/kaggle"]', { timeout: 3000 });
      await page.waitForTimeout(1200);
      const after = await page.evaluate(() => ({ hash: location.hash, open: document.querySelector('aside.sidebar').classList.contains('show') }));
      c('a page link in the phone menu opens the page and closes the menu', /kaggle/.test(after.hash) && !after.open, JSON.stringify(after));
      await go('');
      await page.tap('.sidebar-toggle-button', { timeout: 2000 }).catch(() => {});
      await page.waitForTimeout(800);
    } catch (e) { c('a page link in the phone menu opens the page and closes the menu', false, e.message.split('\n')[0]); }
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
  const csp = await page.evaluate(() => {
    // docsify-pagination probes for `global` with eval inside try/catch and falls back; harmless
    const before = window.__csp.filter((v) => !/^script-src eval\b.*docsify-pagination/.test(v));
    const s = document.createElement('script');
    s.textContent = 'window.__injected = true';
    document.body.appendChild(s);
    return { before, injected: !!window.__injected };
  });
  c('previous / next page links work under the policy', (await page.evaluate(() => document.querySelectorAll('.pagination-item a').length)) >= 1);
  c('security policy blocks nothing the site needs', csp.before.length === 0, csp.before.slice(0, 5).join(' | '));
  c('security policy blocks an injected inline script', !csp.injected);
  if (!phone) {
    const landed = new Set();
    for (let i = 0; i < 4; i++) {
      await page.evaluate(() => document.getElementById('surprise-me').click());
      await page.waitForTimeout(1200);
      const at = await page.evaluate(() => ({ hash: location.hash, h1: !!document.querySelector('.markdown-section h1'), lost: /This page is not here/.test(document.body.textContent) }));
      if (at.h1 && !at.lost && !/README/.test(at.hash)) landed.add(at.hash);
    }
      await go('fields/benchmarks/hpl');
    await page.context().grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => {});
    const link = await page.evaluate(async () => {
      const b = document.querySelector('.markdown-section h2 .section-link-copy');
      if (!b) return {};
      b.click();
      await new Promise((r) => setTimeout(r, 300));
      return { url: b.getAttribute('data-url'), note: b.getAttribute('data-note') };
    });
    c('copy-a-link button copies the section address', /#\/fields\/benchmarks\/hpl\?id=/.test(link.url || '') && link.note === 'Copied', JSON.stringify(link));
    await go('fields/system-administration/q-and-a');
    const code = await page.evaluate(async () => {
      const pre = document.querySelector('.markdown-section pre[data-lang="bash"]');
      const b = pre && pre.querySelector('.code-copy');
      if (!b) return { buttons: 0 };
      b.click();
      await new Promise((r) => setTimeout(r, 300));
      let text = '';
      try { text = await navigator.clipboard.readText(); } catch (e) { /* not readable */ }
      return { buttons: document.querySelectorAll('.code-copy').length, old: document.querySelectorAll('.docsify-copy-code-button').length,
        note: b.getAttribute('data-note'), same: text === pre.querySelector('code').textContent.replace(/\n$/, '') };
    });
    c('code block copy button copies the code', code.buttons >= 1 && !code.old && code.note === 'Copied' && code.same, JSON.stringify(code));
    if (link.url) {
      await page.goto(link.url);
      await page.waitForTimeout(2500);
      const id = decodeURIComponent(link.url.split('?id=')[1]);
      const top = await page.evaluate((i) => Math.round(document.getElementById(i).getBoundingClientRect().top), id);
      c('a copied section link opens with that section on screen', top >= 0 && top < 800, 'heading top ' + top);
    }
  c('"Surprise me" opens different real pages', landed.size >= 3, [...landed].join(' '));
  }
  const nested = await page.evaluate(() => {
    const label = (t) => [...document.querySelectorAll('.sidebar-nav li.group')].find((l) => l.firstElementChild.textContent.trim() === t);
    ['Fields', 'Benchmarks'].forEach((t) => { const l = label(t); if (l && l.classList.contains('collapsed')) l.click(); });
    const b = label('Benchmarks');
    return !!b && !b.classList.contains('collapsed') && b.querySelectorAll('a').length > 1;
  });
  c('a folder inside a folder in the menu opens when tapped', nested);
  const twice = await page.evaluate(() => [...document.querySelectorAll('.sidebar-nav li.group > a')].filter((a) => [...a.parentNode.querySelectorAll(':scope > ul > li > a')].some((k) => k.getAttribute('href') === a.getAttribute('href'))).length);
  c('a folder heading and its index page are one menu entry, not two', twice === 0, twice + ' folders list their index twice');
  // reading history: a page read is dimmed in the menu, and "Continue" returns to it
  await go('tips/kaggle-tips', 1500);
  await go('', 1500);
  const hist = await page.evaluate(() => {
    const cont = document.getElementById('continue-reading');
    const read = [...document.querySelectorAll('.sidebar-nav a.read')].some((a) => /kaggle-tips/.test(a.getAttribute('href')));
    return { href: cont && cont.getAttribute('href'), read };
  });
  c('pages already read are marked in the menu and "Continue" links to the last one', hist.read && hist.href === '#/tips/kaggle-tips', JSON.stringify(hist));
  c('no script errors', page.errors.length === 0, page.errors.join(' | '));
  await page.context().close();
}

// Read offline: the service worker (sw.js, written by stage_site.py) takes
// over, keeps the pages that were read, and shows one again with no network.
async function offline(browser, base) {
  const c = (name, ok, detail) => check(`[${engine} desktop] ${name}`, ok, detail);
  if (!fs.existsSync(path.join(root, 'sw.js'))) return c('staged site has a service worker (sw.js)', false, 'no sw.js in ' + root);
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, colorScheme: 'light' });
  const page = await ctx.newPage();
  page.setDefaultTimeout(10000);
  const h1 = () => page.evaluate(() => ({
    h1: ((document.querySelector('.markdown-section h1') || {}).textContent || '').trim(),
    lost: /This page is not here|You are offline/.test(document.body.textContent),
  }));
  try {
    await page.goto(base + '/#/');
    const active = await page.evaluate(() => Promise.race([
      navigator.serviceWorker.ready.then((r) => !!r.active),
      new Promise((r) => setTimeout(() => r(false), 15000)),
    ]));
    await page.reload();
    await page.waitForTimeout(2000);
    const controlled = await page.evaluate(() => !!navigator.serviceWorker.controller);
    c('a service worker is registered and controls the page after a reload', active && controlled, JSON.stringify({ active, controlled }));
    await page.goto(base + '/#/fields/benchmarks/hpl');
    await page.waitForTimeout(3000);
    const online = await h1();
    serverDown = true;
    await ctx.setOffline(true);
    await page.reload();
    await page.waitForFunction(() => document.querySelector('.markdown-section h1'), null, { timeout: 10000 }).catch(() => {});
    await page.waitForTimeout(1000);
    const off = await h1();
    c('a page read before opens again offline', !!online.h1 && off.h1 === online.h1 && !off.lost, JSON.stringify({ online, off }));
  } catch (e) {
    c('read offline run finished', false, e.message.split('\n')[0]);
  } finally {
    serverDown = false;
    await ctx.setOffline(false).catch(() => {});
    await ctx.close();
  }
}

async function reducedMotion(browser, base) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 800 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  await page.goto(base + '/#/');
  await page.waitForTimeout(2500);
  const t = await page.evaluate(() => [getComputedStyle(document.querySelector('aside.sidebar')).transitionDuration,
    getComputedStyle(document.documentElement).scrollBehavior]);
  check(`[${engine} phone] reduced motion turns off the menu slide and smooth scrolling`,
    t[0].split(',').every((d) => parseFloat(d) < 0.01) && t[1] !== 'smooth', JSON.stringify(t));
  await ctx.close();
}

(async () => {
  if (!fs.existsSync(path.join(root, 'index.html'))) { console.error('no index.html in ' + root); process.exit(2); }
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port;
  if (!['chromium', 'webkit'].includes(engine)) { console.error('engine must be chromium or webkit'); process.exit(2); }
  const browser = await playwright[engine].launch();
  try {
    for (const [label, size, phone] of [['desktop', { width: 1280, height: 800 }, false], ['phone', { width: 390, height: 800 }, true]]) {
      try { await run(browser, base, label, size, phone); }
      catch (e) { check(`[${engine} ${label}] run finished`, false, e.message.split('\n')[0]); }
    }
    // Playwright's WebKit cannot reload a service-worker page with the network
    // emulated off ("internal error"); Safari itself supports service workers.
    if (engine === 'chromium') {
      await offline(browser, base).catch((e) => check(`[${engine} desktop] read offline run finished`, false, e.message.split('\n')[0]));
    } else {
      console.log(`SKIP [${engine} desktop] read offline (not supported by Playwright's WebKit)`);
    }
    await reducedMotion(browser, base).catch((e) => check(`[${engine} phone] reduced motion run finished`, false, e.message.split('\n')[0]));
  } finally {
    await browser.close();
    server.close();
  }
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${engine}: ${results.length - failed.length} of ${results.length} checks passed`);
  process.exit(failed.length ? 1 : 0);
})();
