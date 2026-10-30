"""Bundle the Archify diagrams into one HTML file with a tab per diagram.

Archify writes one standalone page per diagram. This script embeds each page (gzip + base64) in a single file and
shows it in a full-height frame when its tab is chosen, so every diagram keeps its own viewer controls.

    python .archify/build_tabs.py            # from the repository root
"""
import base64
import gzip
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "internsync-diagrams.html"

# (tab id, tab label, one-line description, diagram page relative to .archify/)
TABS = [
    ("architecture", "Architecture", "Runtime components, the report-submit path and trust boundaries",
     "architecture-internsync-overview-20261030-221930/internsync-overview.html"),
    ("workflow", "Workflow", "Weekly report submit and review loop: approval, retry, blocked and evidence paths",
     "workflow-report-review-20261030-222738/report-review.html"),
    ("sequence", "Sequence", "POST /report-slots/{id}/submit from the web app to the response and the background check",
     "sequence-report-submit-20261030-223009/report-submit.html"),
    ("dataflow", "Dataflow", "Notification outbox: producers, the notifications table, the deliver job and channels",
     "dataflow-notification-outbox-20261030-223151/notification-outbox.html"),
    ("lifecycle", "Lifecycle", "Report slot states, waiting states and endings",
     "lifecycle-report-slot-20261030-223423/report-slot.html"),
    ("erd", "ERD", "Report-side schema: 13 tables with every column and foreign key",
     "erd-report-schema-20261030-223705/report-schema.html"),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>InternSync Diagrams</title>
<style>
:root {
  --bg: #f6f7f9; --surface: #ffffff; --ink: #14171f; --muted: #5b6475; --line: #dde1e8;
  --accent: #0f766e; --accent-soft: #e6f4f2; --focus: #2563eb;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0e1116; --surface: #161b22; --ink: #e6e9ef; --muted: #9aa4b5; --line: #2a313c;
    --accent: #5eead4; --accent-soft: #12302d; --focus: #60a5fa;
  }
}
:root[data-theme="dark"] {
  --bg: #0e1116; --surface: #161b22; --ink: #e6e9ef; --muted: #9aa4b5; --line: #2a313c;
  --accent: #5eead4; --accent-soft: #12302d; --focus: #60a5fa;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; }
body { background: var(--bg); color: var(--ink); display: flex; flex-direction: column;
  font: 14px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
header { background: var(--surface); border-bottom: 1px solid var(--line); padding: 10px 16px 0; }
.top { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
h1 { font-size: 16px; margin: 0; }
#caption { color: var(--muted); font-size: 13px; margin: 0; }
[role="tablist"] { display: flex; gap: 4px; overflow-x: auto; margin-top: 8px; scrollbar-width: thin; }
[role="tab"] { appearance: none; border: 0; background: none; color: var(--muted); cursor: pointer;
  font: inherit; font-weight: 600; padding: 8px 12px; border-bottom: 2px solid transparent; white-space: nowrap; }
[role="tab"]:hover { color: var(--ink); }
[role="tab"][aria-selected="true"] { color: var(--accent); border-bottom-color: var(--accent); }
[role="tab"]:focus-visible { outline: 2px solid var(--focus); outline-offset: -2px; border-radius: 4px; }
main { flex: 1; min-height: 0; position: relative; }
iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; background: var(--bg); }
iframe[hidden] { display: none; }
#status { position: absolute; inset: 0; display: grid; place-items: center; color: var(--muted); padding: 16px;
  text-align: center; }
</style>
</head>
<body>
<header>
  <div class="top">
    <h1>InternSync Diagrams</h1>
    <p id="caption"></p>
  </div>
  <div role="tablist" aria-label="Diagrams">
__TABS__
  </div>
</header>
<main id="panel" role="tabpanel">
  <div id="status">Loading…</div>
</main>
__DATA__
<script>
(() => {
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const panel = document.getElementById("panel");
  const status = document.getElementById("status");
  const caption = document.getElementById("caption");
  const frames = {};

  async function page(id) {
    const b64 = document.getElementById("data-" + id).textContent.trim();
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    return await new Response(stream).text();
  }

  async function show(id, focus) {
    const tab = tabs.find((t) => t.dataset.id === id) || tabs[0];
    id = tab.dataset.id;
    for (const t of tabs) {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
    }
    if (focus) tab.focus();
    caption.textContent = tab.dataset.caption;
    panel.setAttribute("aria-labelledby", tab.id);
    document.title = tab.textContent + " · InternSync Diagrams";
    try { history.replaceState(null, "", "#" + id); } catch (e) { /* file: or sandboxed */ }
    for (const [key, frame] of Object.entries(frames)) frame.hidden = key !== id;
    if (frames[id]) { status.hidden = true; return; }
    status.hidden = false;
    status.textContent = "Loading…";
    try {
      if (typeof DecompressionStream === "undefined") throw new Error("This browser cannot unpack the diagrams.");
      const frame = document.createElement("iframe");
      frame.title = tab.textContent + " diagram";
      frame.srcdoc = await page(id);
      frames[id] = frame;
      const current = tabs.find((t) => t.getAttribute("aria-selected") === "true").dataset.id;
      frame.hidden = current !== id;  // another tab may have been chosen while this one loaded
      panel.appendChild(frame);
      if (current === id) status.hidden = true;
    } catch (err) {
      status.textContent = "Could not open this diagram: " + err.message;
    }
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => show(tab.dataset.id));
    tab.addEventListener("keydown", (e) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (e.key === "Home" || e.key === "End") {
        e.preventDefault();
        show(tabs[e.key === "Home" ? 0 : tabs.length - 1].dataset.id, true);
      } else if (step) {
        e.preventDefault();
        show(tabs[(i + step + tabs.length) % tabs.length].dataset.id, true);
      }
    });
  });
  show(location.hash.slice(1));
})();
</script>
</body>
</html>
"""


def main() -> None:
    buttons, blobs = [], []
    for i, (key, label, caption, rel) in enumerate(TABS):
        data = (ROOT / rel).read_bytes()
        packed = base64.b64encode(gzip.compress(data, mtime=0)).decode("ascii")
        buttons.append(f'    <button role="tab" id="tab-{key}" data-id="{key}" aria-controls="panel" '
                       f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" '
                       f'data-caption="{html.escape(caption)}">{html.escape(label)}</button>')
        blobs.append(f'<script type="application/octet-stream" id="data-{key}">{packed}</script>')
    OUT.write_text(PAGE.replace("__TABS__", "\n".join(buttons)).replace("__DATA__", "\n".join(blobs)),
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT.parent)} ({OUT.stat().st_size // 1024} KB, {len(TABS)} tabs)")


if __name__ == "__main__":
    main()
