"""Generate the SDD Word file from InternSync_SDD.md on the CSC 305 SDD template (IEEE 1016 adapted).

Usage: python gen_sdd_docx.py <template.docx> <sdd.md> <out.docx>

The template keeps its cover page, logo header, footer with page numbers, table of contents, and its eight
numbered section headings. The guidance text under each heading is replaced by the matching "## n." section of
the Markdown. Markdown understood: headings ### (Heading 2) and #### (Heading 3), paragraphs, "- " bullets,
"1. " numbered items, pipe tables (with "<br>" for a line break in a cell), images, and bold
"Table x.y – …" / "Figure x.y – …" captions. Block quotes (">") are left out."""
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
from docx.text.paragraph import Paragraph

sys.stdout.reconfigure(encoding="utf-8")
TEMPLATE, MD, OUT = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
MD_DIR = MD.parent
TEXT_W = 6.85          # inches between the template margins (8.5 in page, 0.8 in margins)
MAX_IMG_H = 8.45
NAVY = RGBColor(0x17, 0x36, 0x5D)
BODY_PT = 11
SECTIONS = ["Introduction", "System Overview", "Design Considerations", "Architectural Design", "Detailed Design",
            "Data Design", "External Interfaces", "Appendices"]

doc = docx.Document(TEMPLATE)
body = doc.element.body
lines = MD.read_text(encoding="utf-8").splitlines()

# ------------------------------------------------------------------ metadata from the Markdown header
meta = {}
for ln in lines[:25]:
    m = re.match(r"^\| (Project title|Team name|Advisor|Version|Date) \| (.+) \|$", ln)
    if m:
        meta[m.group(1)] = m.group(2)


def table_after(heading):
    rows = []
    i = lines.index(heading)
    for ln in lines[i + 1:]:
        if ln.startswith("#"):
            break
        if ln.startswith("| ") and "---" not in ln and not re.match(r"^\| \*\*", ln):
            rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return rows


team_rows = table_after("### Team Information")
rev_rows = table_after("### Revision History")

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


def add_inline(par, text, size=BODY_PT, bold=None, italic=None, color=None):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok == "<br>":
            par.add_run().add_break()
            continue
        b, it, code, link = bold, italic, False, None
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            tok, b = tok[2:-2], True
        elif tok.startswith("`") and tok.endswith("`"):
            tok, code = tok[1:-1], True
        elif tok.startswith("[") and "](" in tok:
            label, link = re.match(r"\[([^\]]+)\]\(([^)]+)\)", tok).groups()
            code = label.startswith("`")
            tok = label.strip("`")
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            tok, it = tok[1:-1], True
        tok = unescape(tok)
        if link and link.startswith("http"):
            add_hyperlink(par, link, tok, size)
            continue
        run = par.add_run(tok)
        run.bold = b
        run.italic = it
        run.font.size = Pt(size)
        if color is not None:
            run.font.color.rgb = color
        if code:
            run.font.name = "Consolas"
            run.font.size = Pt(size - 1.5)


def set_cell_shading(cell, hex_color):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_color)
    tcpr.append(shd)


def row_prop(row, tag):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement(tag); el.set(qn("w:val"), "true")
    trpr.append(el)


def cell_margins(table, top=30, bottom=30, side=70):
    tblpr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for edge, v in (("top", top), ("left", side), ("bottom", bottom), ("right", side)):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); mar.append(e)
    tblpr.append(mar)


def clean(c):
    return re.sub(r"\*|`", "", c).strip()


def widths_for(header, rows):
    h = [clean(c) for c in header]
    n = len(h)
    fixed = {
        ("Module Name", "Responsibilities", "Inputs / Outputs", "Notes / Diagrams"): [1.35, 2.0, 2.3, 1.2],
        ("No.", "Decision", "Options considered", "Rationale and trade-off"): [0.45, 1.75, 1.45, 3.2],
        ("Column", "Type", "Constraints", "Notes"): [1.75, 1.05, 1.55, 2.5],
        ("Term", "Definition"): [1.6, 5.25],
        ("Item", "Value"): [1.6, 5.25],
    }
    if tuple(h) in fixed:
        return fixed[tuple(h)]
    if n == 2 and h[0] in ("Role", "Record", "Status"):
        return [1.0, 5.85]
    lens = []
    for j in range(n):
        col = [len(clean(r[j])) if j < len(r) else 0 for r in [header] + rows]
        lens.append(max(4, min(70, sum(col) / len(col) + 0.25 * max(col))))
    tot = sum(lens)
    w = [max(0.5, TEXT_W * x / tot) for x in lens]
    s = sum(w)
    return [x * TEXT_W / s for x in w]


def add_table(anchor, header, rows):
    ncol = len(header)
    t = doc.add_table(rows=1 + len(rows), cols=ncol)
    t.style = doc.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    widths = widths_for(header, rows)
    size = 8 if ncol >= 5 else 9
    for r_i, row in enumerate([header] + rows):
        tr = t.rows[r_i]
        if r_i == 0:
            row_prop(tr, "w:tblHeader")
        row_prop(tr, "w:cantSplit")
        for c_i in range(ncol):
            cell = tr.cells[c_i]
            cell.width = Inches(widths[c_i])
            txt = row[c_i] if c_i < len(row) else ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.space_before = Pt(0)
            add_inline(p, txt.strip(), size=size, bold=True if r_i == 0 else None)
            if r_i == 0:
                set_cell_shading(cell, "DBE5F1")
    n_rows = len(t.rows)
    keep_upto = n_rows - 1 if n_rows <= 10 else min(2, n_rows - 1)
    for r_i in range(keep_upto):
        for cell in t.rows[r_i].cells:
            for cp in cell.paragraphs:
                cp.paragraph_format.keep_with_next = True
    grid = t._tbl.tblGrid
    for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
        gc.set(qn("w:w"), str(int(widths[j] * 1440)))
    cell_margins(t)
    anchor.addprevious(t._tbl)
    return t


def para(anchor, text="", size=BODY_PT, bold=None, italic=None, align=None, after=6, before=0, keep=False,
         color=None, style=None):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if text:
        add_inline(p, text, size=size, bold=bold, italic=italic, color=color)
    pf = p.paragraph_format
    pf.space_after = Pt(after)
    pf.space_before = Pt(before)
    pf.line_spacing = 1.12
    if align is not None:
        p.alignment = align
    if keep:
        pf.keep_with_next = True
    anchor.addprevious(p._p)
    return p


def heading(anchor, text, level):
    p = doc.add_paragraph(style=f"Heading {level}")
    run = p.add_run(text)
    run.bold = True
    run.italic = False
    run.font.color.rgb = NAVY
    run.font.size = Pt(13 if level == 2 else 11.5)
    rpr = run._r.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts"); rpr.insert(0, fonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(a), "Times New Roman")
    pf = p.paragraph_format
    pf.space_before = Pt(12 if level == 2 else 9)
    pf.space_after = Pt(4)
    pf.keep_with_next = True
    anchor.addprevious(p._p)
    return p


def list_item(anchor, marker, text, level=0):
    p = para(anchor, "", after=3)
    pf = p.paragraph_format
    indent = 0.3 + 0.25 * level
    pf.left_indent = Inches(indent)
    pf.first_line_indent = Inches(-0.22)
    pf.tab_stops.add_tab_stop(Inches(indent))
    r = p.add_run(marker + "\t")
    r.font.size = Pt(BODY_PT)
    add_inline(p, text)
    return p


def page_break(anchor):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    p.paragraph_format.space_after = Pt(0)
    anchor.addprevious(p._p)


def picture(anchor, path):
    img = DocxImage.from_file(str(path))
    ratio = img.px_height / img.px_width
    w = TEXT_W
    if img.px_width < 1500 and img.px_height < 1000:      # screenshots: a little narrower
        w = 6.2
    if w * ratio > MAX_IMG_H:
        w = MAX_IMG_H / ratio
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Inches(w))
    anchor.addprevious(p._p)


def text_of(el):
    return Paragraph(el, doc).text.strip() if el.tag == qn("w:p") else ""


# ------------------------------------------------------------------ cover page
children = list(body.iterchildren())
title_p = next(el for el in children if text_of(el).startswith("[Enter a clear"))
tp = Paragraph(title_p, doc)
for r in tp.runs[1:]:
    r._r.getparent().remove(r._r)
tp.runs[0].text = meta["Project title"]
tp.runs[0].bold = True

team_tbl = next(el for el in children if el.tag == qn("w:tbl") and "Team Members" in el.xpath("string(.)"))
from docx.table import Table  # noqa: E402
tt = Table(team_tbl, doc)
for row, member in zip(tt.rows[1:], team_rows):
    cell = row.cells[0]
    p = cell.paragraphs[0]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    run = p.add_run(f"{member[0]} – {member[1]}")
    run.font.size = Pt(11)

# advisor, course, version, and date under the team table, in place of the first blank lines
after_team = team_tbl.getnext()
cover_lines = [("Advisor: ", meta["Advisor"]),
               ("Course: ", "CSC 305 – Software Engineering · Semester 1 – 2026/2027 · Section 5MA1 · Group 3"),
               ("Version: ", f"{meta['Version']}  ·  Date: {meta['Date']}"),
               ("Standard: ", "IEEE Std 1016-1998, Recommended Practice for Software Design Descriptions")]
blank = after_team
used = 0
while blank is not None and used < len(cover_lines):
    blank = blank.getnext()
    if blank is not None and blank.tag == qn("w:p") and not text_of(blank) and not blank.findall(".//" + qn("w:br")):
        p = Paragraph(blank, doc)
        lab, val = cover_lines[used]
        r1 = p.add_run(lab); r1.bold = True; r1.font.size = Pt(12)
        r2 = p.add_run(val); r2.font.size = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        used += 1
# drop four further blank lines so that the cover keeps to one page
el = blank.getnext()
dropped = 0
while el is not None and dropped < 4:
    nxt = el.getnext()
    if el.tag == qn("w:p") and not text_of(el) and not el.findall(".//" + qn("w:br")):
        body.remove(el)
        dropped += 1
    el = nxt

# ------------------------------------------------------------------ revision history before the table of contents
children = list(body.iterchildren())
toc = next(el for el in children if el.tag == qn("w:sdt"))
para(toc, "Revision History", size=14, bold=True, color=NAVY, after=6, keep=True)
add_table(toc, ["**Version**", "**Date**", "**Description**", "**Author**"], rev_rows)
para(toc, "", after=10)

# blank paragraphs between the table of contents and section 1: replace with one page break
el = toc.getnext()
while el is not None and el.tag == qn("w:p") and not text_of(el):
    nxt = el.getnext()
    body.remove(el)
    el = nxt
H1 = {}
for el in body.iterchildren():
    t = text_of(el)
    if t in SECTIONS and el.find(".//" + qn("w:numPr")) is not None:
        H1[t] = el
assert list(H1) == SECTIONS, list(H1)
page_break(H1["Introduction"])

# the section headings: all as Heading 1 so that they appear in the table of contents
for el in H1.values():
    pstyle = el.find(qn("w:pPr")).find(qn("w:pStyle"))
    pstyle.set(qn("w:val"), "Heading1")
    bidi = el.find(qn("w:pPr")).find(qn("w:bidi"))
    if bidi is not None:
        el.find(qn("w:pPr")).remove(bidi)
    Paragraph(el, doc).paragraph_format.space_after = Pt(6)

# remove the guidance under each heading
sect_pr = body.find(qn("w:sectPr"))
for i, name in enumerate(SECTIONS):
    start = H1[name]
    stop = H1[SECTIONS[i + 1]] if i + 1 < len(SECTIONS) else sect_pr
    el = start.getnext()
    while el is not None and el is not stop:
        nxt = el.getnext()
        body.remove(el)
        el = nxt

# ------------------------------------------------------------------ Markdown sections into the template
sec_starts = [i for i, ln in enumerate(lines) if re.match(r"^## \d+\. ", ln)]
assert len(sec_starts) == len(SECTIONS), sec_starts
CAPTION = re.compile(r"^\*\*((Table|Figure) [A-Z\d]+\.\d+ – .+)\*\*$")
STOP = re.compile(r"^(#|\||!\[|- |\d+\.\s|> |\*\*(Table|Figure) [A-Z\d]+\.\d+ – )")

for s_i, name in enumerate(SECTIONS):
    title = lines[sec_starts[s_i]][3:].split(". ", 1)[1]
    assert title == name, (title, name)
    anchor = H1[SECTIONS[s_i + 1]] if s_i + 1 < len(SECTIONS) else sect_pr
    k = sec_starts[s_i] + 1
    end = sec_starts[s_i + 1] if s_i + 1 < len(SECTIONS) else len(lines)
    last = None
    first_h = True
    while k < end:
        ln = lines[k]
        if not ln.strip():
            k += 1
            continue
        m = re.match(r"^(#{3,4}) (.+)$", ln)
        if m:
            level = len(m.group(1)) - 1
            if s_i == 7 and level == 2 and not first_h:
                page_break(anchor)              # each appendix on its own page
            first_h = False
            last = heading(anchor, m.group(2), level)
            k += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", ln)
        if m:
            picture(anchor, (MD_DIR / m.group(2)).resolve())
            k += 1
            continue
        m = CAPTION.match(ln)
        if m:
            is_fig = m.group(2) == "Figure"
            last = para(anchor, m.group(1), size=10, bold=True, italic=False, after=8 if is_fig else 3,
                        before=0 if is_fig else 4, align=WD_ALIGN_PARAGRAPH.CENTER if is_fig else None,
                        keep=not is_fig, color=NAVY)
            k += 1
            continue
        if ln.startswith("|"):
            rows = []
            while k < end and lines[k].startswith("|"):
                if not re.match(r"^\|(\s*:?-+:?\s*\|)+\s*$", lines[k]):
                    cells = re.split(r"(?<!\\)\|", lines[k].strip())[1:-1]
                    rows.append([c.strip() for c in cells])
                k += 1
            if last is not None:
                last.paragraph_format.keep_with_next = True
            add_table(anchor, rows[0], rows[1:])
            para(anchor, "", size=4, after=4)
            last = None
            continue
        if ln.startswith("> "):
            k += 1
            continue
        m = re.match(r"^(\s*)- (.+)$", ln)
        if m:
            last = list_item(anchor, "•", m.group(2), level=1 if m.group(1) else 0)
            k += 1
            continue
        m = re.match(r"^(\s*)(\d+)\.\s+(.+)$", ln)
        if m:
            last = list_item(anchor, f"{m.group(2)}.", m.group(3), level=1 if m.group(1) else 0)
            k += 1
            continue
        buf = [ln]
        k += 1
        while k < end and lines[k].strip() and not STOP.match(lines[k]):
            buf.append(lines[k])
            k += 1
        text = " ".join(s.strip() for s in buf)
        last = para(anchor, text, keep=text.endswith(":") or bool(re.fullmatch(r"\*\*[^*]+\*\*", text)))
    if s_i + 1 < len(SECTIONS):
        page_break(anchor)

# ------------------------------------------------------------------ properties
cp = doc.core_properties
cp.title = "InternSync – Software Design Description"
cp.subject = "CSC 305 SDD (IEEE 1016 adapted)"
cp.author = "Group 3"
doc.save(OUT)
print("saved", OUT)
