// Render Claude Design .dc.html artboards to PNG outside the canvas (static preview with default props).
// usage: node render_wf.js <wireframes dir> <out dir> <name> [<name> ...]
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

const [, , SRC, OUT, ...NAMES] = process.argv;
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

function parse(file) {
  const html = fs.readFileSync(file, 'utf8');
  const helmet = (html.match(/<helmet>([\s\S]*?)<\/helmet>/) || [, ''])[1];
  let body = (html.match(/<x-dc>([\s\S]*?)<\/x-dc>/) || [, ''])[1];
  body = body.replace(/<helmet>[\s\S]*?<\/helmet>/, '');
  const scriptTag = html.match(/<script type="text\/x-dc"[^>]*data-props='([^']*)'[^>]*>([\s\S]*?)<\/script>/);
  const propsDecl = scriptTag ? JSON.parse(scriptTag[1]) : {};
  const code = scriptTag ? scriptTag[2] : 'class Component extends DCLogic { renderVals() { return {}; } }';
  const props = {};
  for (const [k, v] of Object.entries(propsDecl)) if (k !== '$preview' && v && 'default' in v) props[k] = v.default;
  class DCLogic { constructor(p) { this.props = p; } }
  // eslint-disable-next-line no-new-func
  const Component = new Function('DCLogic', code + '\nreturn Component;')(DCLogic);
  const vals = new Component(props).renderVals();
  const preview = propsDecl.$preview || { width: 1280, height: 900 };
  const lang = (html.match(/<html[^>]*lang="([^"]+)"/) || [, 'ar'])[1];
  const dir = (html.match(/<html[^>]*dir="([^"]+)"/) || [, 'rtl'])[1];
  return { helmet, body, vals, preview, lang, dir };
}

function renderInPage(vals) {
  const BOOL = new Set(['checked', 'disabled', 'selected', 'readonly', 'hidden', 'required']);
  const lookup = (expr, scope) => {
    expr = expr.trim();
    if (expr === 'true') return true;
    if (expr === 'false') return false;
    if (/^-?\d+(\.\d+)?$/.test(expr)) return Number(expr);
    let cur;
    const parts = expr.split('.');
    for (let i = scope.length - 1; i >= 0; i--) if (parts[0] in scope[i]) { cur = scope[i]; break; }
    if (cur === undefined) return undefined;
    for (const p of parts) { if (cur == null) return undefined; cur = cur[p]; }
    return cur;
  };
  const single = /^\s*\{\{([^}]*)\}\}\s*$/;
  const subst = (s, scope) => s.replace(/\{\{([^}]*)\}\}/g, (_, e) => { const v = lookup(e, scope); return v == null ? '' : String(v); });
  const walk = (node, scope) => {
    for (const child of Array.from(node.childNodes)) {
      if (child.nodeType === 3) { if (child.nodeValue.includes('{{')) child.nodeValue = subst(child.nodeValue, scope); continue; }
      if (child.nodeType !== 1) continue;
      const tag = child.tagName.toLowerCase();
      if (tag === 'sc-if') {
        const m = (child.getAttribute('value') || '').match(single);
        const ok = m ? !!lookup(m[1], scope) : false;
        if (ok) { walk(child, scope); child.replaceWith(...Array.from(child.childNodes)); } else child.remove();
        continue;
      }
      if (tag === 'sc-for') {
        const m = (child.getAttribute('list') || '').match(single);
        const list = (m ? lookup(m[1], scope) : []) || [];
        const as = child.getAttribute('as') || 'item';
        const frag = document.createDocumentFragment();
        list.forEach((item, index) => {
          const holder = document.createElement('div');
          holder.innerHTML = child.innerHTML;
          walk(holder, scope.concat([{ [as]: item, index }]));
          frag.append(...Array.from(holder.childNodes));
        });
        child.replaceWith(frag);
        continue;
      }
      for (const attr of Array.from(child.attributes)) {
        if (!attr.value.includes('{{')) continue;
        const m = attr.value.match(single);
        if (m) {
          const v = lookup(m[1], scope);
          if (typeof v === 'boolean') {
            if (!v) child.removeAttribute(attr.name);
            else child.setAttribute(attr.name, BOOL.has(attr.name) ? '' : 'true');
            if (attr.name === 'checked') child.checked = v;
            continue;
          }
        }
        child.setAttribute(attr.name, subst(attr.value, scope));
      }
      walk(child, scope);
    }
  };
  walk(document.body, [vals]);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, args: ['--no-sandbox'] });
  for (const name of NAMES) {
    const { helmet, body, vals, preview, lang, dir } = parse(path.join(SRC, name + '.dc.html'));
    const page = await browser.newPage();
    await page.setViewport({ width: preview.width, height: preview.height, deviceScaleFactor: preview.width < 600 ? 2 : 1.25 });
    const doc = `<!doctype html><html lang="${lang}" dir="${dir}"><head><meta charset="utf-8">${helmet}</head><body>${body}</body></html>`;
    await page.setContent(doc, { waitUntil: 'networkidle0', timeout: 60000 });
    await page.evaluate(renderInPage, vals);
    await page.evaluate(() => document.fonts.ready);
    await new Promise((r) => setTimeout(r, 300));
    const file = path.join(OUT, name + '.png');
    await page.screenshot({ path: file, fullPage: true });
    console.log('ok', name);
    await page.close();
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
