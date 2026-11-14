"""Bundle the Archify diagrams into one bilingual HTML file: a tab per diagram, English first, with an Arabic switch.

Archify writes one standalone page per diagram and language. This script stores every page in docs/diagrams.html
and shows it in a full-height frame when its tab is chosen, so each diagram keeps its own viewer controls. Pages are
split at their <script> and <style> blocks and identical pieces are stored once, since every page carries the same
viewer. A diagram without an Arabic page shows its English page in both languages.

The diagrams of the diagram pack that the SDD added (layered architecture, the two class diagrams, and the sign-in
sequence) are SVG files drawn with matplotlib. Each gets a small viewer page (zoom, fit, drag to move) built here,
with its controls in the reader's language; the drawing itself is in English. The SVG sits in its own <script>
block, so it is stored once for both languages.

    python .archify/build_tabs.py            # from the repository root
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "docs" / "diagrams.html"
SVG_DIR = ROOT.parent / "docs" / "InternSync_Diagrams" / "svg"

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
    # Archify class diagram made for the SDD (English page only)
    ("reportclasses", "class-report-review-20261101-225053", "report-review-classes",
     {"ar": "كلاسات مراجعة التقارير", "en": "Report review classes"},
     {"ar": "دوال خدمة التقارير والتشابه، والسجلات التي تغيّرها، وحالات خانة التقرير (المخطط بالإنجليزية)",
      "en": "Report and similarity service functions, the records they change, and the slot status"}),
    # diagram pack figures added for the SDD: "svg:" + file name in docs/InternSync_Diagrams/svg
    ("layers", "svg:", "12_layers",
     {"ar": "طبقات النظام", "en": "Layers"},
     {"ar": "طبقات العميل والخادم كما بُنيت، وكل طبقة تستدعي الطبقة التي تحتها فقط",
      "en": "Client and server layers as built; each layer calls only the layer below it"}),
    ("classes", "svg:", "13a_class_organizations_placement",
     {"ar": "الكلاسات: المنظمات والتوظيف", "en": "Classes: organizations"},
     {"ar": "مخطط كلاسات UML: الجامعات والشركات والحسابات والملف الشخصي والفرص والطلبات والتوظيف",
      "en": "UML class diagram: organizations, accounts, profiles, vacancies, applications, and placement"}),
    ("training", "svg:", "13b_class_training_grading",
     {"ar": "الكلاسات: التدريب والدرجات", "en": "Classes: training"},
     {"ar": "مخطط كلاسات UML: التقارير والتشابه والحضور والتقييمات والدرجات والشهادات",
      "en": "UML class diagram: reports, similarity, attendance, evaluations, grades, and certificates"}),
    ("signin", "svg:", "14_seq_login",
     {"ar": "تسلسل تسجيل الدخول", "en": "Sign-in sequence"},
     {"ar": "تسجيل الدخول والقفل والجلسة، ثم مرور أي طلب عبر بوابات الأمان",
      "en": "Sign-in, lockout, and the session, then any request through the pipeline gates"}),
]
LANGS = {"ar": ".ar.html", "en": ".html"}

# viewer page of one SVG figure; __...__ are filled per language, the <style> and <script> blocks are shared
SVG_PAGE = """<!doctype html>
<html lang="__LANG__" dir="__DIR__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
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
.tools { display:flex; flex-wrap:wrap; align-items:center; gap:6px; padding:8px 16px; background:var(--bar);
  border-bottom:1px solid var(--line); }
.tools button { font:inherit; font-size:14px; min-height:36px; min-width:40px; padding:6px 12px; color:var(--text);
  background:var(--chip); border:1px solid var(--line); border-radius:8px; cursor:pointer; }
.tools button:hover { border-color:var(--accent); }
.tools button:focus-visible, #stage:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.tools .note { color:var(--muted); font-size:13px; margin-inline-start:auto; }
#stage { flex:1; min-height:0; overflow:auto; cursor:grab; touch-action:manipulation; }
#stage.drag { cursor:grabbing; user-select:none; }
#paper { margin:16px auto; width:max-content; background:#ffffff; border:1px solid var(--line); border-radius:10px;
  padding:12px; direction:ltr; }
#paper svg { display:block; }
@media (max-width: 560px) { .tools .note { display:none; } .tools { padding:6px 10px; } .tools button { min-height:44px; min-width:44px; } }
</style>
</head>
<body>
<div class="tools" role="toolbar" aria-label="__TOOLBAR__">
  <button type="button" data-act="out" aria-label="__ZOOM_OUT__" title="__ZOOM_OUT__">−</button>
  <button type="button" data-act="in" aria-label="__ZOOM_IN__" title="__ZOOM_IN__">+</button>
  <button type="button" data-act="width">__FIT_WIDTH__</button>
  <button type="button" data-act="all">__FIT_ALL__</button>
  <span class="note">__NOTE__</span>
</div>
<div id="stage" tabindex="0" aria-label="__TITLE__"><div id="paper" role="img" aria-label="__TITLE__"></div></div>
<script type="image/svg+xml" id="figure">__SVG__</script>
<script>
const stage = document.getElementById('stage');
const paper = document.getElementById('paper');
paper.innerHTML = document.getElementById('figure').textContent;
const svg = paper.querySelector('svg');
const box = svg.viewBox.baseVal;
const ratio = box.height / box.width;
svg.removeAttribute('width');
svg.removeAttribute('height');
let mode = 'width', width = 0;
function room() { return { w: stage.clientWidth - 58, h: stage.clientHeight - 58 }; }
function size(w) {
  width = Math.max(240, Math.min(w, 6000));
  svg.style.width = width + 'px';
  svg.style.height = width * ratio + 'px';
}
function fit() { const r = room(); size(mode === 'all' ? Math.min(r.w, r.h / ratio) : r.w); }
function zoom(f, cx, cy) {
  const rect = stage.getBoundingClientRect();
  const x = cx === undefined ? stage.clientWidth / 2 : cx - rect.left;
  const y = cy === undefined ? stage.clientHeight / 2 : cy - rect.top;
  const px = (stage.scrollLeft + x) / stage.scrollWidth, py = (stage.scrollTop + y) / stage.scrollHeight;
  mode = 'free';
  size(width * f);
  stage.scrollLeft = px * stage.scrollWidth - x;
  stage.scrollTop = py * stage.scrollHeight - y;
}
document.querySelectorAll('[data-act]').forEach((b) => b.addEventListener('click', () => {
  const act = b.dataset.act;
  if (act === 'in') zoom(1.25); else if (act === 'out') zoom(0.8); else { mode = act; fit(); stage.scrollTo(0, 0); }
}));
stage.addEventListener('wheel', (e) => {
  if (!e.ctrlKey) return;
  e.preventDefault();
  zoom(e.deltaY < 0 ? 1.15 : 0.87, e.clientX, e.clientY);
}, { passive: false });
stage.addEventListener('keydown', (e) => {
  if (e.key === '+' || e.key === '=') zoom(1.25);
  else if (e.key === '-') zoom(0.8);
  else if (e.key === '0') { mode = 'width'; fit(); }
});
let drag = null;
stage.addEventListener('pointerdown', (e) => {
  if (e.pointerType !== 'mouse' || e.button !== 0) return;
  drag = { x: e.clientX, y: e.clientY, l: stage.scrollLeft, t: stage.scrollTop };
  stage.classList.add('drag');
  stage.setPointerCapture(e.pointerId);
});
stage.addEventListener('pointermove', (e) => {
  if (!drag) return;
  stage.scrollLeft = drag.l - (e.clientX - drag.x);
  stage.scrollTop = drag.t - (e.clientY - drag.y);
});
function stop() { drag = null; stage.classList.remove('drag'); }
stage.addEventListener('pointerup', stop);
stage.addEventListener('pointercancel', stop);
new ResizeObserver(() => { if (mode !== 'free') fit(); }).observe(stage);
fit();
</script>
</body>
</html>
"""
SVG_UI = {
    "ar": {"dir": "rtl", "toolbar": "أدوات العرض", "out": "تصغير", "in": "تكبير", "width": "ملء العرض",
           "all": "المخطط كاملاً",
           "note": "المخطط بالإنجليزية · اسحب للتحريك · Ctrl مع عجلة الفأرة للتكبير"},
    "en": {"dir": "ltr", "toolbar": "View controls", "out": "Zoom out", "in": "Zoom in", "width": "Fit width",
           "all": "Whole diagram", "note": "Drag to move · Ctrl + wheel to zoom"},
}


def svg_page(stem: str, lang: str, title: str) -> str:
    """Viewer page of one diagram pack SVG in one language."""
    drawing = (SVG_DIR / f"{stem}.svg").read_text(encoding="utf-8")
    drawing = drawing[drawing.index("<svg"):]              # drop the XML declaration and doctype
    assert "</script" not in drawing.lower()
    ui = SVG_UI[lang]
    fill = {"__LANG__": lang, "__DIR__": ui["dir"], "__TITLE__": html.escape(title), "__TOOLBAR__": ui["toolbar"],
            "__ZOOM_OUT__": ui["out"], "__ZOOM_IN__": ui["in"], "__FIT_WIDTH__": ui["width"],
            "__FIT_ALL__": ui["all"], "__NOTE__": ui["note"]}
    page = SVG_PAGE
    for k, v in fill.items():
        page = page.replace(k, v)
    return page.replace("__SVG__", drawing)


def source_page(folder: str, stem: str, lang: str, label: dict) -> str:
    """The page shown for one tab and language."""
    if folder == "svg:":
        return svg_page(stem, lang, label[lang])
    page = ROOT / folder / f"{stem}{LANGS[lang]}"
    if not page.exists():                                  # no Arabic page: show the English one
        page = ROOT / folder / f"{stem}{LANGS['en']}"
    return page.read_text(encoding="utf-8")
SPLIT = re.compile(r"(?=<script)|(?<=</script>)|(?=<style)|(?<=</style>)")

PAGE = """<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>InternSync diagrams · مخططات InternSync</title>
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
const CHOICE = 'internsync-diagrams-lang-choice';  // set only when the reader presses the language button
let lang = 'en', key = TABS[0].key;
try { const saved = localStorage.getItem(CHOICE); if (saved in UI) lang = saved; } catch (e) {}
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
}
document.getElementById('lang').addEventListener('click', () => {
  lang = lang === 'ar' ? 'en' : 'ar';
  try { localStorage.setItem(CHOICE, lang); } catch (e) {}
  render();
});
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
    for key, folder, stem, label, _ in TABS:
        for lang in LANGS:
            page = source_page(folder, stem, lang, label)
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
