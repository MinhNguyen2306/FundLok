// Render the VPBank proposal artefacts to PDF with headless Chromium.
//
//   node render_pdfs.mjs            # everything
//   node render_pdfs.mjs diagrams   # the four diagrams only
//   node render_pdfs.mjs docs       # the four documents only
//
// Diagrams print from their own @page rules (A4 landscape, set in each generator).
// Documents print from the intermediate *-print.html that md2html.py produces; the
// header and footer are supplied here rather than in the CSS so page numbers work.
//
// Requires: npm i playwright   (and a Chromium; set CHROMIUM to override the path)

import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const DIA = path.join(ROOT, '04-diagrams');
const only = process.argv[2] ?? 'all';

const DIAGRAMS = [
  'section-1.4-moneyflow.html',
  'section-1.4-closedloop.html',
  'section-1.4-closedloop-VI.html',
  'section-1.5-dataflow.html',
  'section-3.1-swimlane.html',
];

// [ intermediate print html, output pdf, running header ]
const DOCS = [
  ['cons-en-print.html', '02-english-only/FundLok-VPBank-Response-Consolidated-EN.pdf',
   'FundLok × VPBank — response, English draft'],
  ['cons-vi-print.html', '01-send-to-team/FundLok-VPBank-Response-Consolidated-VI.pdf',
   'FundLok × VPBank — phản hồi, bản tiếng Việt'],
  ['issues-print.html', '02-english-only/Partnership-Issues-Register.pdf',
   'Internal · partnership issues register'],
  ['money-print.html', '02-english-only/Money-Flow-and-Fees-Summary.pdf',
   'Money flow & fees — summary'],
];

// Prefer Playwright's own Chromium; fall back to whatever browser is on the machine.
function findChrome() {
  if (process.env.CHROMIUM) return process.env.CHROMIUM;
  const candidates = [];
  const pw = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (pw && fs.existsSync(pw)) {
    for (const d of fs.readdirSync(pw).filter((n) => n.startsWith('chromium'))) {
      candidates.push(path.join(pw, d, 'chrome-linux', 'chrome'),
                      path.join(pw, d, 'chrome-mac', 'Chromium.app', 'Contents', 'MacOS', 'Chromium'));
    }
  }
  candidates.push(
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
  );
  return candidates.find((c) => fs.existsSync(c));
}

let browser;
try {
  browser = await chromium.launch();
} catch (e) {
  const exe = findChrome();
  if (!exe) throw new Error('No Chromium found. Run `npx playwright install chromium`, or set CHROMIUM=/path/to/chrome.');
  console.log('using', exe);
  browser = await chromium.launch({ executablePath: exe });
}
const grey = 'font:8pt system-ui;color:#98968f;width:100%;padding:0 18mm;';

if (only === 'all' || only === 'diagrams') {
  for (const f of DIAGRAMS) {
    const src = path.join(DIA, f);
    if (!fs.existsSync(src)) { console.log('missing, skipped:', f); continue; }
    const p = await browser.newPage({ viewport: { width: 1360, height: 1200 } });
    await p.goto('file://' + src, { waitUntil: 'load' });
    await p.emulateMedia({ media: 'print', colorScheme: 'light' });
    // preferCSSPageSize honours the @page size the generator declares
    await p.pdf({ path: src.replace(/\.html$/, '.pdf'), printBackground: true, preferCSSPageSize: true });
    await p.close();
    console.log('diagram →', f.replace(/\.html$/, '.pdf'));
  }
}

if (only === 'all' || only === 'docs') {
  for (const [inp, out, hdr] of DOCS) {
    const src = path.join(HERE, inp);
    if (!fs.existsSync(src)) { console.log('missing, skipped:', inp, '(run md2html.py first)'); continue; }
    const p = await browser.newPage();
    await p.goto('file://' + src, { waitUntil: 'load' });
    await p.emulateMedia({ media: 'print', colorScheme: 'light' });
    await p.pdf({
      path: path.join(ROOT, out), format: 'A4', printBackground: true, displayHeaderFooter: true,
      headerTemplate: `<div style="${grey}">${hdr}</div>`,
      footerTemplate: `<div style="${grey}text-align:right;">page <span class="pageNumber"></span> / <span class="totalPages"></span></div>`,
      margin: { top: '22mm', bottom: '16mm', left: '18mm', right: '18mm' },
    });
    await p.close();
    console.log('document →', out);
  }
}

await browser.close();
