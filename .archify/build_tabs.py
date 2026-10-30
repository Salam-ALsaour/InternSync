"""Bundle the Archify diagrams into one bilingual HTML file: a tab per diagram, Arabic first, with an English switch.

Archify writes one standalone page per diagram and language. This script stores every page in a single file and shows
it in a full-height frame when its tab is chosen, so each diagram keeps its own viewer controls. Pages are split at
their <script> and <style> blocks and identical pieces are stored once, since every page carries the same viewer.

    python .archify/build_tabs.py            # from the repository root
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "internsync-diagrams.html"

# key, folder, page stem (English is <stem>.html, Arabic <stem>.ar.html), tab labels and captions
TABS = [
    ("architecture", "architecture-internsync-overview-20261030-221930", "internsync-overview",
     {"ar": "المعمارية", "en": "Architecture"},
     {"ar": "مكونات التشغيل، ومسار إرسال التقرير، وحدود الثقة",
      "en": "Runtime components, the report-submit path and trust boundaries"}),
    ("workflow", "workflow-report-review-20261030-222738", "report-review",
     {"ar": "سير العمل", "en": "Workflow"},
     {"ar": "دورة إرسال التقرير الأسبوعي ومراجعته: الاعتماد والإعادة والرفض والأدلة",
      "en": "Weekly report submit and review loop: approval, retry, blocked and evidence paths"}),
    ("sequence", "sequence-report-submit-20261030-223009", "report-submit",
     {"ar": "تسلسل الطلب", "en": "Sequence"},
     {"ar": "طلب إرسال التقرير من تطبيق الويب حتى الرد، ثم الفحص بالخلفية",
      "en": "POST /report-slots/{id}/submit from the web app to the response and the background check"}),
    ("dataflow", "dataflow-notification-outbox-20261030-223151", "notification-outbox",
     {"ar": "تدفق الإشعارات", "en": "Dataflow"},
     {"ar": "الـ outbox: المنتِجون، وجدول notifications، ومهمة التوصيل، والقنوات",
      "en": "Notification outbox: producers, the notifications table, the deliver job and channels"}),
    ("lifecycle", "lifecycle-report-slot-20261030-223423", "report-slot",
     {"ar": "دورة حياة التقرير", "en": "Lifecycle"},
     {"ar": "حالات خانة التقرير، وحالات الانتظار، والنهايات",
      "en": "Report slot states, waiting states and endings"}),
    ("erd", "erd-report-schema-20261030-223705", "report-schema",
     {"ar": "قاعدة البيانات", "en": "ERD"},
     {"ar": "جانب التقارير: 13 جدولاً بكل الأعمدة والمفاتيح",
      "en": "Report-side schema: 13 tables with every column and foreign key"}),
]
LANGS = {"ar": ".ar.html", "en": ".html"}
SPLIT = re.compile(r"(?=<script)|(?<=</script>)|(?=<style)|(?<=</style>)")

PAGE = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مخططات InternSync · InternSync diagrams</title>
<style>
:root { --bg:#f6f7f9; --bar:#ffffff; --line:#d9dde3; --text:#1d2430; --muted:#5b6575; --accent:#0f766e; --chip:#eef1f4; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --bg:#0b0f17; --bar:#111827; --line:#253041; --text:#e6eaf0; --muted:#9aa5b5; --accent:#5eead4; --chip:#1b2433; }
}
:root[data-theme="dark"] { --bg:#0b0f17; --bar:#111827; --line:#253041; --text:#e6eaf0; --muted:#9aa5b5; --accent:#5eead4; --chip:#1b2433; }
* { box-sizing:border-box; }
html, body { margin:0; height:100%; background:var(--bg); color:var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", Tahoma, sans-serif; }
body { display:flex; flex-direction:column; }
header { background:var(--bar); border-bottom:1px solid var(--line); padding:8px 16px 0; }
.top { display:flex; align-items:center; gap:12px; }
h1 { font-size:16px; margin:0; white-space:nowrap; }
#caption { flex:1; min-width:0; margin:0; color:var(--muted); font-size:13px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
nav { display:flex; gap:4px; overflow-x:auto; scrollbar-width:thin; margin-top:4px; }
nav button { font:inherit; font-size:15px; color:var(--muted); background:none; border:0;
  border-bottom:3px solid transparent; padding:10px 14px; cursor:pointer; white-space:nowrap; }
nav button:hover { color:var(--text); }
nav button[aria-selected="true"] { color:var(--text); border-bottom-color:var(--accent); font-weight:600; }
#lang { font:inherit; font-size:14px; color:var(--text); background:var(--chip); border:1px solid var(--line);
  border-radius:999px; padding:6px 14px; cursor:pointer; white-space:nowrap; }
button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
main { position:relative; flex:1; min-height:0; }
iframe { position:absolute; inset:0; width:100%; height:100%; border:0; background:var(--bg); }
iframe.off { visibility:hidden; }
@media (max-width: 560px) { #caption { display:none; } }
</style>
</head>
<body>
<header>
  <div class="top">
    <h1 id="heading"></h1>
    <p id="caption"></p>
    <button id="lang" type="button"></button>
  </div>
  <nav role="tablist" id="tabs"></nav>
</header>
<main id="frames"></main>
<script type="application/json" id="chunks">__CHUNKS__</script>
<script type="application/json" id="docs">__DOCS__</script>
<script>
const CHUNKS = JSON.parse(document.getElementById('chunks').textContent);
const DOCS = JSON.parse(document.getElementById('docs').textContent);
const TABS = __TABS__;
const UI = {
  ar: { dir: 'rtl', title: 'مخططات InternSync', nav: 'المخططات', switchTo: 'English', switchLabel: 'Switch to English' },
  en: { dir: 'ltr', title: 'InternSync diagrams', nav: 'Diagrams', switchTo: 'العربية', switchLabel: 'التبديل إلى العربية' },
};
const frames = {};
let lang = 'ar', key = TABS[0].key;
try { const saved = localStorage.getItem('internsync-diagrams-lang'); if (saved in UI) lang = saved; } catch (e) {}
const m = location.hash.match(/^#(ar|en)\\/(\\w+)$/);
if (m && TABS.some((t) => t.key === m[2])) { lang = m[1]; key = m[2]; }

function frame(l, k) {
  const id = l + '-' + k;
  if (!frames[id]) {
    const f = document.createElement('iframe');
    f.title = TABS.find((t) => t.key === k).label[l];
    f.srcdoc = DOCS[l][k].map((i) => CHUNKS[i]).join('');
    document.getElementById('frames').appendChild(f);
    frames[id] = f;
  }
  return frames[id];
}

function render() {
  const ui = UI[lang];
  const tab = TABS.find((t) => t.key === key);
  document.documentElement.lang = lang;
  document.documentElement.dir = ui.dir;
  document.title = tab.label[lang] + ' · ' + ui.title;
  document.getElementById('heading').textContent = ui.title;
  document.getElementById('caption').textContent = tab.caption[lang];
  const nav = document.getElementById('tabs');
  nav.setAttribute('aria-label', ui.nav);
  nav.replaceChildren(...TABS.map((t) => {
    const b = document.createElement('button');
    b.setAttribute('role', 'tab');
    b.id = 'tab-' + t.key;
    b.textContent = t.label[lang];
    b.setAttribute('aria-selected', String(t.key === key));
    b.setAttribute('aria-controls', 'frames');
    b.tabIndex = t.key === key ? 0 : -1;
    b.addEventListener('click', () => { key = t.key; render(); nav.querySelector('[aria-selected="true"]').focus(); });
    b.addEventListener('keydown', (e) => {
      const fwd = ui.dir === 'rtl' ? 'ArrowLeft' : 'ArrowRight';
      const back = ui.dir === 'rtl' ? 'ArrowRight' : 'ArrowLeft';
      const step = e.key === fwd ? 1 : e.key === back ? -1 : 0;
      if (!step) return;
      e.preventDefault();
      const i = TABS.findIndex((x) => x.key === key);
      key = TABS[(i + step + TABS.length) % TABS.length].key;
      render();
      nav.querySelector('[aria-selected="true"]').focus();
    });
    return b;
  }));
  document.getElementById('frames').setAttribute('role', 'tabpanel');
  document.getElementById('frames').setAttribute('aria-labelledby', 'tab-' + key);
  const btn = document.getElementById('lang');
  btn.textContent = ui.switchTo;
  btn.lang = lang === 'ar' ? 'en' : 'ar';
  btn.setAttribute('aria-label', ui.switchLabel);
  nav.querySelector('[aria-selected="true"]').scrollIntoView({ block: 'nearest', inline: 'nearest' });
  const shown = frame(lang, key);
  for (const f of Object.values(frames)) f.classList.toggle('off', f !== shown);
  try { history.replaceState(null, '', '#' + lang + '/' + key); } catch (e) {}
  try { localStorage.setItem('internsync-diagrams-lang', lang); } catch (e) {}
}
document.getElementById('lang').addEventListener('click', () => { lang = lang === 'ar' ? 'en' : 'ar'; render(); });
render();
</script>
</body>
</html>
"""


def as_json(value) -> str:
    """JSON that is safe inside a <script> element: no '<' can close it early."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def main() -> None:
    chunks, index, docs = [], {}, {lang: {} for lang in LANGS}
    for key, folder, stem, _, _ in TABS:
        for lang, suffix in LANGS.items():
            page = (ROOT / folder / f"{stem}{suffix}").read_text(encoding="utf-8")
            ids = []
            for piece in SPLIT.split(page):
                if piece not in index:
                    index[piece] = len(chunks)
                    chunks.append(piece)
                ids.append(index[piece])
            assert "".join(chunks[i] for i in ids) == page, f"{folder} {lang} does not reassemble"
            docs[lang][key] = ids
    tabs = [{"key": key, "label": label, "caption": caption} for key, _, _, label, caption in TABS]
    out = (PAGE.replace("__CHUNKS__", as_json(chunks)).replace("__DOCS__", as_json(docs))
           .replace("__TABS__", as_json(tabs)))
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT.parent)} ({OUT.stat().st_size // 1024} KB, {len(TABS)} tabs × {len(LANGS)} "
          f"languages, {len(chunks)} chunks)")


if __name__ == "__main__":
    main()
