"""Generate the SRS Word file from InternSync_SRS.md on the CSC 305 SRS template (IEEE 830 adapted).
Usage: python gen_docx.py <template.docx> <srs.md> <out.docx>"""
import copy
import re
import sys
import pathlib

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.image.image import Image as DocxImage
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

TEMPLATE, MD, OUT = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
MD_DIR = MD.parent
TEXT_W = 6.0  # inches between the template margins
MAX_IMG_H = 6.9

doc = docx.Document(TEMPLATE)
body = doc.element.body
lines = MD.read_text(encoding="utf-8").splitlines()

# ------------------------------------------------------------------ metadata from the Markdown header
meta = {}
for ln in lines[:20]:
    m = re.match(r"^\| (Project title|Team name|Advisor|Version|Date) \| (.+) \|$", ln)
    if m:
        meta[m.group(1)] = m.group(2)
team_rows = []
i = lines.index("### Team Information")
for ln in lines[i + 1:]:
    if ln.startswith("###"):
        break
    if ln.startswith("| ") and "---" not in ln and "**Team Member**" not in ln:
        team_rows.append([c.strip() for c in ln.strip().strip("|").split("|")])

# ------------------------------------------------------------------ helpers
INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*])|<br>)")


def unescape(t):
    return t.replace("\\|", "|").replace("\\<", "<").replace("\\>", ">").replace("\\*", "*")


def add_hyperlink(par, url, text, size=None):
    rid = par.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                             is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), "1F4E9A"); rpr.append(c)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rpr.append(u)
    if size:
        sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2))); rpr.append(sz)
    r.append(rpr)
    t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r)
    par._p.append(h)


def add_inline(par, text, size=None, bold=None, italic=None):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok == "<br>":
            par.add_run().add_break()
            continue
        b, it, code, link = bold, italic, False, None
        if tok.startswith("**") and tok.endswith("**"):
            tok, b = tok[2:-2], True
        elif tok.startswith("`") and tok.endswith("`"):
            tok, code = tok[1:-1], True
        elif tok.startswith("[") and "](" in tok:
            label, link = re.match(r"\[([^\]]+)\]\(([^)]+)\)", tok).groups()
            tok = label.strip("`")
            code = label.startswith("`")
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            tok, it = tok[1:-1], True
        tok = unescape(tok)
        if link and link.startswith("http"):
            add_hyperlink(par, link, tok, size)
            continue
        if "**" in tok or tok.startswith("*"):
            pass
        run = par.add_run(tok)
        run.bold = b
        run.italic = it
        if size:
            run.font.size = Pt(size)
        if code:
            run.font.name = "Consolas"
            run.font.size = Pt((size or 11) - 1)


def keep_next(par):
    par.paragraph_format.keep_with_next = True


def set_cell_shading(cell, hex_color):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_color)
    tcpr.append(shd)


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true")
    trpr.append(h)


def no_split(row):
    trpr = row._tr.get_or_add_trPr()
    c = OxmlElement("w:cantSplit"); c.set(qn("w:val"), "true")
    trpr.append(c)


def widths_for(header, rows):
    h = [re.sub(r"\*", "", c).strip() for c in header]
    n = len(h)
    if h[:4] == ["ID", "Requirement", "Priority", "Acceptance criterion"]:
        return [0.95, 2.6, 0.6, 1.85]
    if n == 2 and (h[0] in ("Use case", "Term", "Item", "Attribute", "Priority")):
        return {"Use case": [1.35, 4.65], "Term": [1.5, 4.5], "Item": [1.6, 4.4], "Attribute": [1.2, 4.8],
                "Priority": [1.3, 4.7]}[h[0]]
    if h[0] == "Action" and n == 7:
        return [2.1] + [0.65] * 6
    # generic: share by content length
    lens = []
    for j in range(n):
        col = [len(re.sub(r"\*|`", "", r[j])) if j < len(r) else 0 for r in [header] + rows]
        lens.append(max(4, min(60, sum(col) / len(col) + 0.3 * max(col))))
    tot = sum(lens)
    w = [max(0.55, TEXT_W * x / tot) for x in lens]
    s = sum(w)
    return [x * TEXT_W / s for x in w]


def add_table(anchor, header, rows, small=False):
    ncol = len(header)
    t = doc.add_table(rows=1 + len(rows), cols=ncol)
    t.style = doc.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = widths_for(header, rows)
    size = 8 if (small or ncol >= 6) else 9
    for r_i, row in enumerate([header] + rows):
        tr = t.rows[r_i]
        if r_i == 0:
            repeat_header(tr)
        no_split(tr)
        for c_i in range(ncol):
            cell = tr.cells[c_i]
            cell.width = Inches(widths[c_i])
            txt = row[c_i] if c_i < len(row) else ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            align = None
            if txt.strip().startswith(":") or re.fullmatch(r"\s*(—|Yes|Must|Should|Could|–|\d+)\s*", txt or ""):
                align = WD_ALIGN_PARAGRAPH.CENTER
            add_inline(p, txt.strip(), size=size, bold=True if r_i == 0 else None)
            if r_i == 0:
                set_cell_shading(cell, "DBE5F1")
            if align is not None and r_i > 0 and ncol > 2:
                p.alignment = align
    # keep short tables on one page; otherwise keep the header with the first row
    n_rows = len(t.rows)
    keep_upto = n_rows - 1 if n_rows <= 12 else min(2, n_rows - 1)
    for r_i in range(keep_upto):
        for cell in t.rows[r_i].cells:
            for cp in cell.paragraphs:
                cp.paragraph_format.keep_with_next = True
    # column widths in the grid too (Word honours tblGrid)
    grid = t._tbl.tblGrid
    for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[j] * 1440)))
    anchor.addprevious(t._tbl)
    return t


def para(anchor, text="", style=None, align=None, size=None, italic=None, bold=None):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if text:
        add_inline(p, text, size=size, italic=italic, bold=bold)
    if align is not None:
        p.alignment = align
    anchor.addprevious(p._p)
    return p


def page_break(anchor):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    anchor.addprevious(p._p)


def picture(anchor, path, max_w=TEXT_W):
    img = DocxImage.from_file(str(path))
    w_in = img.px_width / (img.horz_dpi or 96)
    h_in = img.px_height / (img.vert_dpi or 96)
    ratio = h_in / w_in
    w = min(max_w, TEXT_W)
    if img.px_width < 1300 and img.px_height > img.px_width * 1.5:   # phone screenshots
        w = min(w, 2.9)
    if w * ratio > MAX_IMG_H:
        w = MAX_IMG_H / ratio
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(w))
    anchor.addprevious(p._p)


def toc_field(anchor):
    p = doc.add_paragraph()
    r = p.add_run()
    fc1 = OxmlElement("w:fldChar"); fc1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = 'TOC \\o "1-3" \\h \\z \\u'
    fc2 = OxmlElement("w:fldChar"); fc2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t"); t.text = "Right-click and choose Update Field to build the table of contents."
    fc3 = OxmlElement("w:fldChar"); fc3.set(qn("w:fldCharType"), "end")
    for el in (fc1, it, fc2, t, fc3):
        r._r.append(el)
    anchor.addprevious(p._p)


# ------------------------------------------------------------------ cover page (template paragraphs 0 – 6)
P = doc.paragraphs


def set_line(p, label, value):
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    p.runs[0].text = ""
    lab = p.runs[0]
    lab.text = label
    lab.bold = True
    p.add_run(value)


set_line(P[2], "Project Title: ", meta["Project title"])
set_line(P[3], "Team Name & Members: ", meta["Team name"])
set_line(P[4], "Advisor: ", meta["Advisor"])
set_line(P[5], "Version: ", meta["Version"])
set_line(P[6], "Date: ", meta["Date"])
# team table right after the "Team Name & Members" line
anchor_team = P[4]._p
tbl = add_table(anchor_team, ["**Team Member**", "**Student ID**", "**Project Role**"], team_rows)
for row in tbl.rows:
    for c, w in zip(row.cells, [2.2, 1.2, 2.6]):
        c.width = Inches(w)
gap = para(anchor_team, "")

# ------------------------------------------------------------------ remove the template's guidance body
children = list(body.iterchildren())
eval_idx = next(i for i, el in enumerate(children)
                if el.tag == qn("w:p") and Paragraph(el, doc).text.strip() == "Evaluation")
toc_idx = next(i for i, el in enumerate(children)
               if el.tag == qn("w:p") and Paragraph(el, doc).text.strip() == "Table of Contents")
for el in children[toc_idx:eval_idx]:
    body.remove(el)
EVAL = children[eval_idx]  # new content goes before this

# ------------------------------------------------------------------ front matter: revision history and contents
page_break(EVAL)
para(EVAL, "Revision History", style="TOC Heading")
rev = []
i = lines.index("### Revision History")
for ln in lines[i + 1:]:
    if ln.startswith("##"):
        break
    if ln.startswith("| ") and "---" not in ln and "**Version**" not in ln:
        rev.append([c.strip() for c in ln.strip().strip("|").split("|")])
add_table(EVAL, ["**Version**", "**Date**", "**Description**", "**Author**"], rev)
para(EVAL, "")
para(EVAL, "Table of Contents", style="TOC Heading")
toc_field(EVAL)
page_break(EVAL)

# ------------------------------------------------------------------ body from the Markdown (from "## 1. Introduction")
start = lines.index("## 1. Introduction")
k = start
first_h1 = True
last_par = None
while k < len(lines):
    ln = lines[k]
    if not ln.strip():
        k += 1
        continue
    m = re.match(r"^(#{2,4}) (.+)$", ln)
    if m:
        level = len(m.group(1)) - 1
        if level == 1 and not first_h1:
            page_break(EVAL)
        first_h1 = False
        h = para(EVAL, m.group(2), style=f"Heading {level}")
        last_par = h
        k += 1
        continue
    m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", ln)
    if m:
        picture(EVAL, (MD_DIR / m.group(2)).resolve())
        k += 1
        continue
    m = re.match(r"^\*\*((Table|Figure) [\dA]+\.\d+ – .+)\*\*$", ln)
    if m:
        cap = para(EVAL, m.group(1), style="Caption",
                   align=WD_ALIGN_PARAGRAPH.CENTER if m.group(2) == "Figure" else None)
        if m.group(2) == "Table":
            keep_next(cap)
            if last_par is not None and len(last_par.text) < 400:
                keep_next(last_par)
        last_par = cap
        k += 1
        continue
    if ln.startswith("|"):
        rows = []
        while k < len(lines) and lines[k].startswith("|"):
            if not re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lines[k]):
                cells = re.split(r"(?<!\\)\|", lines[k].strip())[1:-1]
                rows.append([c.strip() for c in cells])
            k += 1
        if last_par is not None and len(last_par.text) < 400:
            keep_next(last_par)
        add_table(EVAL, rows[0], rows[1:])
        para(EVAL, "").paragraph_format.space_after = Pt(2)
        last_par = None
        continue
    if ln.startswith("> "):
        k += 1
        continue
    m = re.match(r"^- (.+)$", ln)
    if m:
        para(EVAL, m.group(1), style="List Bullet")
        k += 1
        continue
    m = re.match(r"^(\d+)\.\s+(.+)$", ln)
    if m:
        p = para(EVAL, f"{m.group(1)}.\t{m.group(2)}")
        pf = p.paragraph_format
        pf.left_indent = Inches(0.35)
        pf.first_line_indent = Inches(-0.3)
        pf.tab_stops.add_tab_stop(Inches(0.35))
        k += 1
        continue
    m = re.match(r"^\*(Source: .+)\*$", ln)
    if m:
        last_par = para(EVAL, m.group(1), italic=True, size=10)
        k += 1
        continue
    # plain paragraph (joins hard-wrapped lines)
    buf = [ln]
    k += 1
    while k < len(lines) and lines[k].strip() and not re.match(r"^(#|\||!\[|- |\d+\.\s|> |\*\*(Table|Figure) )", lines[k]):
        buf.append(lines[k])
        k += 1
    last_par = para(EVAL, " ".join(s.strip() for s in buf))

# evaluation page of the template on its own page
page_break(EVAL)

# ------------------------------------------------------------------ footer: page number
fp = doc.sections[0].footer.paragraphs
pn = fp[1] if len(fp) > 1 else doc.sections[0].footer.add_paragraph()
pn.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = pn.add_run("Page ")
r.font.size = Pt(9)
run = pn.add_run()
for typ, txt in (("begin", None), (None, "PAGE"), ("separate", None), (None, None), ("end", None)):
    if typ:
        fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), typ); run._r.append(fc)
    elif txt:
        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = txt; run._r.append(it)
    else:
        t = OxmlElement("w:t"); t.text = "1"; run._r.append(t)
run.font.size = Pt(9)

# template footer: shorten the run of spaces so the line fits on one row
for r in doc.sections[0].footer.paragraphs[0].runs:
    if r.text.strip() == "" and len(r.text) > 5:
        r.text = "   "

# core properties
cp = doc.core_properties
cp.title = "InternSync – Software Requirements Specification"
cp.subject = "CSC 305 SRS (IEEE 830 adapted)"
cp.author = "Group 3"
cp.revision = 13
doc.save(OUT)
print("saved", OUT)
