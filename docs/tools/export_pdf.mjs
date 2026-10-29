// PDF files of the maintained documents for the final submission (Increment 5, D6 and RQ-3).
//
//   node docs/tools/export_pdf.mjs        (after `npm ci` and `npx playwright install chromium` in frontend/)
//
// Each Markdown document is rendered to HTML with `marked`, its images resolved from the document's own folder, and
// printed to A4 by the Chromium of the browser tests. The SRS is built separately on the course template
// (docs/RSR/build).
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const DOCS = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = join(DOCS, "Final_Submission");
const require = createRequire(resolve(DOCS, "../frontend/package.json"));
const markedModule = await import(pathToFileURL(require.resolve("marked")).href);
const Marked = markedModule.Marked ?? markedModule.default.Marked;
const { chromium } = require("@playwright/test");

const SPMP = "Software Project Management Plan (SPMP)/InternSync_SPMP.md";
const FILES = [
  ["InternSync_Final_Report.pdf", "Final Report", ["Final_Report.md"]],
  ["InternSync_SPMP_v1.7.pdf", "Software Project Management Plan", [SPMP]],
  ["InternSync_Design_v1.7.pdf", "System Design Document", ["Design/InternSync_Design.md"]],
  ["InternSync_API_Spec_v1.5.pdf", "API Specification", ["Design/InternSync_API_Spec.md"]],
  ["InternSync_Test_Reports.pdf", "Test Reports", [1, 2, 3, 4, 5].map((n) => `Increments/Increment_${n}/04_Test_Report.md`)],
  ["InternSync_UAT_Plan.pdf", "User Acceptance Testing Plan", ["Increments/Increment_4/05_UAT_Plan.md"]],
  ["InternSync_User_Guide.pdf", "User Guide", ["User_Guide.md"]],
  ["InternSync_Key_Results.pdf", "Key Results", ["Key_Results.md"]],
  ["InternSync_Requirements_Status.pdf", "Requirements Status", ["Requirements_Status.md"]],
  ["InternSync_Change_Requests.pdf", "Change Requests", ["Change_Requests.md"]],
  ["InternSync_Demo_Script.pdf", "Demonstration Script", ["Demo_Script.md"]],
];

const STYLE = `
  @page { size: A4; margin: 18mm 15mm 18mm 15mm; }
  body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #111827; }
  h1 { font-size: 20pt; color: #1F3864; border-bottom: 2px solid #1F3864; padding-bottom: 4px; }
  h2 { font-size: 14pt; color: #1F3864; margin-top: 18px; break-after: avoid; }
  h3, h4 { font-size: 11.5pt; break-after: avoid; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8.5pt; }
  th, td { border: 1px solid #CBD2DC; padding: 3px 5px; vertical-align: top; text-align: start; }
  th { background: #E6EEFB; }
  tr { break-inside: avoid; }
  code { font-family: Consolas, monospace; font-size: 8.5pt; background: #F3F4F6; padding: 0 2px; }
  pre { background: #F3F4F6; padding: 6px 8px; white-space: pre-wrap; font-size: 8.5pt; }
  pre code { background: none; }
  img { max-width: 100%; max-height: 190mm; display: block; margin: 6px auto; border: 1px solid #E5E7EB; }
  blockquote { border-inline-start: 3px solid #CBD2DC; margin: 6px 0; padding: 2px 10px; color: #4B5563; }
  section + section { break-before: page; }
  a { color: #1F4E9A; text-decoration: none; }
`;

function render(path) {
  const folder = dirname(join(DOCS, path));
  const marked = new Marked({
    gfm: true,
    walkTokens(token) {  // images and local links as file addresses, so the printed page finds them
      if (token.type === "image" && !/^(https?:|data:)/.test(token.href)) {
        token.href = pathToFileURL(resolve(folder, decodeURIComponent(token.href))).href;
      }
    },
  });
  return `<section>${marked.parse(readFileSync(join(DOCS, path), "utf8"))}</section>`;
}

mkdirSync(OUT, { recursive: true });
const work = join(tmpdir(), `internsync-export-${process.pid}`);
mkdirSync(work, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage();
for (const [name, title, sources] of FILES) {
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>InternSync – ${title}</title>
    <style>${STYLE}</style></head><body>${sources.map(render).join("\n")}</body></html>`;
  const file = join(work, `${name}.html`);
  writeFileSync(file, html);
  await page.goto(pathToFileURL(file).href, { waitUntil: "load" });
  await page.pdf({
    path: join(OUT, name), format: "A4", printBackground: true, displayHeaderFooter: true,
    headerTemplate: `<div style="font-size:7pt;color:#6B7280;width:100%;padding:0 15mm;">InternSync – ${title}</div>`,
    footerTemplate: `<div style="font-size:7pt;color:#6B7280;width:100%;text-align:center;">
      <span class="pageNumber"></span> / <span class="totalPages"></span></div>`,
    margin: { top: "18mm", bottom: "18mm", left: "15mm", right: "15mm" },
  });
  console.log(`wrote docs/Final_Submission/${name}`);
}
await browser.close();
rmSync(work, { recursive: true, force: true });
