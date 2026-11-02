"""Fill the official CSC 305 Project Status Report template from the Markdown report.

    python fill_status_report.py <template.docx> <report.md> <out.docx>

Each `## Heading` of the Markdown goes under the template's label "Heading:". The template's own paragraphs and
tables are kept: its example text is replaced, its tables are filled in place (a table may get more columns, but every
column of the template must stay, in the same order), and its empty spacing paragraphs stay. A heading the template
does not have becomes a new label in the template's style, at the same place as in the Markdown. Extra tables and
captions go after the section's template table, built from the template's own table so they look the same.

Markdown understood: paragraphs, `- ` bullets, `**bold**`, `code` (shown as plain text), links (shown as their text),
pipe tables with `:---` (left) or `:--:` (centred) columns, a caption line `**Table N – ...**` before a table, and
`<!-- widths: 40 20 ... -->` before a table for its column widths in percent. Text before the first `##` is not
printed."""
import copy
import re
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BLUE = "00B0F0"
TABLE_WIDTH = 9645  # twips, the width of the template's task tables
# The template's second "Upcoming Tasks:" label heads the Issue | Impact | Owner | Status table: a copy error.
RENAME_SECOND = ("Upcoming Tasks", "Issues and Risks")
EMOJI_FONT = "Segoe UI Emoji"  # as in the template's "✅ Done" cells

W_P, W_TBL, W_R = qn("w:p"), qn("w:tbl"), qn("w:r")


# ---------------------------------------------------------------- Markdown
def parse(md):
    """[(heading, [block, ...])] where a block is ("p", text), ("li", text), ("cap", text), or
    ("table", header, rows, aligns, widths)."""
    sections, blocks, para, table, widths = [], None, [], None, None

    def flush_para():
        if para:
            blocks.append(("p", " ".join(para)))
            para.clear()

    def flush_table():
        nonlocal table, widths
        if table:
            cells = [split_row(r) for r in table]
            aligns = ["center" if re.fullmatch(r":-+:", c) else "left" for c in cells[1]]
            blocks.append(("table", cells[0], cells[2:], aligns, widths))
        table, widths = None, None

    for line in md.splitlines():
        s = line.strip()
        if s.startswith("## "):
            if blocks is not None:
                flush_para(), flush_table()
            blocks = []
            sections.append((s[3:].strip(), blocks))
            continue
        if blocks is None or s.startswith(">"):
            continue
        if s.startswith("|"):
            flush_para()
            table = (table or []) + [s]
            continue
        flush_table()
        m = re.fullmatch(r"<!--\s*widths:\s*([\d\s.]+)-->", s)
        if m:
            widths = [float(x) for x in m.group(1).split()]
        elif not s:
            flush_para()
        elif s.startswith("- "):
            flush_para()
            blocks.append(("li", s[2:]))
        elif re.fullmatch(r"\*\*Table [^*]+\*\*", s):
            flush_para()
            blocks.append(("cap", s.strip("*")))
        else:
            para.append(s)
    if blocks is not None:
        flush_para(), flush_table()
    return sections


def split_row(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def inline(text):
    """[(text, bold)] for a Markdown line: links become their text, code its text, `\\|` a bar."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text).replace("\\|", "|").replace("`", "")
    return [(part, i % 2 == 1) for i, part in enumerate(text.split("**")) if part]


def plain(text):
    return "".join(t for t, _ in inline(text))


# ---------------------------------------------------------------- Word helpers
def text_of(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def is_label(el):
    if el.tag != W_P or not text_of(el).strip().endswith(":"):
        return False
    for r in el.iter(W_R):
        rpr = r.find(qn("w:rPr"))
        col = rpr.find(qn("w:color")) if rpr is not None else None
        if col is not None and col.get(qn("w:val")) == BLUE and rpr.find(qn("w:b")) is not None:
            return True
    return False


def label_name(el):
    return text_of(el).strip()[:-1].strip()


def set_label(el, name):
    runs = [r for r in el.findall(W_R) if r.find(qn("w:t")) is not None]
    runs[0].find(qn("w:t")).text = name + ":"
    for r in runs[1:]:
        el.remove(r)


def keep_next(p):
    ppr = p.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr")
        p.insert(0, ppr)
    if ppr.find(qn("w:keepNext")) is None:
        k = OxmlElement("w:keepNext")
        # keepNext comes after pStyle in the schema order; inserting first after pStyle is enough for Word
        style = ppr.find(qn("w:pStyle"))
        ppr.insert(1 if style is not None else 0, k)


def clear_runs(p):
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)


def make_run(text, bold=False, base_rpr=None, font=None):
    r = OxmlElement("w:r")
    rpr = copy.deepcopy(base_rpr) if base_rpr is not None else OxmlElement("w:rPr")
    for tag in ("w:b", "w:bCs"):
        old = rpr.find(qn(tag))
        if old is not None:
            rpr.remove(old)
    if font:
        f = rpr.find(qn("w:rFonts"))
        if f is None:
            f = OxmlElement("w:rFonts")
            rpr.insert(0, f)
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            f.set(qn(a), font)
    if bold:
        b = OxmlElement("w:b")
        pos = 1 if rpr.find(qn("w:rFonts")) is not None else 0
        rpr.insert(pos, b)
    if len(rpr):
        r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    return r


def fill_runs(p, text, base_rpr=None, bold_all=False):
    """Write `text` (Markdown inline) into paragraph `p`; a leading emoji such as ✅ gets the template's emoji font."""
    clear_runs(p)
    for part, bold in inline(text):
        m = re.match(r"([☀-➿\U0001F300-\U0001FAFF]️?)(.*)", part, re.S)
        if m:
            p.append(make_run(m.group(1), False, base_rpr, EMOJI_FONT))
            part = m.group(2)
        if part:
            p.append(make_run(part, bold or bold_all, base_rpr))


def set_jc(p, align):
    ppr = p.find(qn("w:pPr"))
    jc = ppr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        rpr = ppr.find(qn("w:rPr"))
        if rpr is not None:
            rpr.addprevious(jc)
        else:
            ppr.append(jc)
    jc.set(qn("w:val"), align)


def first_run_rpr(p):
    r = p.find(W_R)
    return r.find(qn("w:rPr")) if r is not None else None


# ---------------------------------------------------------------- tables
def row_flag(tr, tag):
    trpr = tr.find(qn("w:trPr"))
    if trpr is None:
        trpr = OxmlElement("w:trPr")
        tr.insert(0, trpr)
    if trpr.find(qn(tag)) is None:
        e = OxmlElement(tag)
        trpr.insert(0, e)


def build_table(proto, header, rows, aligns, widths, total):
    """A copy of the template table `proto` with this header and these rows: header cells from its first row, data
    cells from its second row, so shading, borders, and alignment stay the template's."""
    tbl = copy.deepcopy(proto)
    trs = tbl.findall(qn("w:tr"))
    head_tr, data_tr = trs[0], trs[1]
    for tr in trs:
        tbl.remove(tr)
    n = len(header)
    widths = widths or [1] * n
    if len(widths) != n:
        raise SystemExit(f"widths {widths} do not match the {n} columns of: {' | '.join(header)}")
    tw = [round(total * w / sum(widths)) for w in widths]
    tblw = tbl.find(qn("w:tblPr")).find(qn("w:tblW"))
    tblw.set(qn("w:w"), str(total))
    tblw.set(qn("w:type"), "dxa")
    grid = tbl.find(qn("w:tblGrid"))
    for g in list(grid):
        grid.remove(g)
    for w in tw:
        g = OxmlElement("w:gridCol")
        g.set(qn("w:w"), str(w))
        grid.append(g)

    def row(proto_tr, values, header_row):
        tr = copy.deepcopy(proto_tr)
        cells = tr.findall(qn("w:tc"))
        cell_proto = cells[0]
        for c in cells:
            tr.remove(c)
        for i, value in enumerate(values):
            tc = copy.deepcopy(cell_proto)
            tc.find(qn("w:tcPr")).find(qn("w:tcW")).set(qn("w:w"), str(tw[i]))
            for p in tc.findall(W_P)[1:]:
                tc.remove(p)
            p = tc.find(W_P)
            fill_runs(p, plain(value) if header_row else value)
            set_jc(p, "center" if header_row else aligns[i])
            tr.append(tc)
        row_flag(tr, "w:cantSplit")
        if header_row:
            row_flag(tr, "w:tblHeader")
        return tr

    tbl.append(row(head_tr, header, True))
    for r in rows:
        tbl.append(row(data_tr, r + [""] * (n - len(r)), False))
    return tbl


def check_columns(tpl_tbl, header):
    """Every column of the template table must stay, in order."""
    tpl_cols = [text_of(tc).strip().lower() for tc in tpl_tbl.find(qn("w:tr")).findall(qn("w:tc"))]
    md_cols = [plain(h).lower() for h in header]
    it = iter(md_cols)
    if not all(any(c == m for m in it) for c in tpl_cols):
        raise SystemExit(f"table {' | '.join(md_cols)} drops a template column of {' | '.join(tpl_cols)}")


# ---------------------------------------------------------------- main
def main(tpl_path, md_path, out_path):
    sections = parse(open(md_path, encoding="utf-8").read())
    doc = Document(tpl_path)
    body = doc.element.body
    sect_pr = body.find(qn("w:sectPr"))

    labels = [el for el in body if is_label(el)]
    names = [label_name(el) for el in labels]
    if names.count(RENAME_SECOND[0]) == 2:
        second = labels[[i for i, n in enumerate(names) if n == RENAME_SECOND[0]][1]]
        set_label(second, RENAME_SECOND[1])
        names = [label_name(el) for el in labels]

    # prototypes, copied before anything changes
    p_label = copy.deepcopy(labels[0])
    para = [el for el in body if el.tag == W_P]
    p_text = copy.deepcopy(next(p for p in para if text_of(p).startswith("Brief overview")))
    p_bullet = copy.deepcopy(next(p for p in para if p.find(qn("w:pPr")) is not None
                                  and p.find(qn("w:pPr")).find(qn("w:numPr")) is not None))
    after_title = labels[0].getprevious()
    p_spacer = copy.deepcopy(next(p for p in para if not text_of(p).strip() and p.find(qn("w:pPr")) is not None
                                  and p.find(qn("w:pPr")).find(qn("w:spacing")) is None
                                  and list(body).index(p) > list(body).index(after_title)))
    tables = [el for el in body if el.tag == W_TBL]
    t_proto = copy.deepcopy(next(t for t in tables if "Assigned To" in text_of(t)))

    unused = list(zip(names, labels))
    md_names = [n for n, _ in sections]
    missing = [n for n, _ in unused if n not in md_names]
    if missing:
        raise SystemExit(f"the Markdown has no section for the template labels: {', '.join(missing)}")

    for name, blocks in sections:
        idx = next((i for i, (n, _) in enumerate(unused) if n == name), None)
        if idx is None:  # a heading the template does not have: a new label before the next template label
            label = copy.deepcopy(p_label)
            set_label(label, name)
            nxt = unused[0][1] if unused else sect_pr
            nxt.addprevious(label)
            spacer = copy.deepcopy(p_spacer)
            nxt.addprevious(spacer)
            end = spacer
        else:
            if idx != 0:
                raise SystemExit(f"section '{name}' is out of the template's order")
            label = unused.pop(0)[1]
            end = unused[0][1] if unused else sect_pr
        keep_next(label)
        fill_section(label, end, blocks, p_text, p_bullet, p_spacer, t_proto)

    cp = doc.core_properties
    cp.title = "InternSync – Mid Status Report (Project 5)"
    cp.subject = "CSC 305 Project Status Report"
    cp.author = "Group 3"
    cp.last_modified_by = "Group 3"
    doc.save(out_path)
    print("saved", out_path)


def fill_section(label, end, blocks, p_text, p_bullet, p_spacer, t_proto):
    span = []
    el = label.getnext()
    while el is not None and el is not end:
        span.append(el)
        el = el.getnext()
    tpl_tbl = next((e for e in span if e.tag == W_TBL), None)
    holders = [e for e in span if e.tag == W_P and text_of(e).strip()]
    # body text takes the look of the section's own example paragraph when it has one
    plain_holders = [h for h in holders if h.find(qn("w:pPr")) is None or h.find(qn("w:pPr")).find(qn("w:numPr")) is None]
    text_proto = copy.deepcopy(plain_holders[0] if plain_holders else p_text)

    # where the blocks before the first table go, and where the rest go
    first_table = next((i for i, b in enumerate(blocks) if b[0] == "table"), None)
    if tpl_tbl is not None and first_table is not None:
        before, main_tbl, after = blocks[:first_table], blocks[first_table], blocks[first_table + 1:]
    else:
        before, main_tbl, after = blocks, None, []

    if tpl_tbl is not None and main_tbl is None:
        raise SystemExit(f"section '{label_name(label)}' needs a table for the template's table")

    anchor = holders[0] if holders else (tpl_tbl if tpl_tbl is not None else end)
    for e in render(before, text_proto, p_bullet, p_spacer, t_proto, trailing_spacer=main_tbl is not None):
        anchor.addprevious(e)
    if main_tbl is not None:
        _, header, rows, aligns, widths = main_tbl
        check_columns(tpl_tbl, header)
        total = int(tpl_tbl.find(qn("w:tblPr")).find(qn("w:tblW")).get(qn("w:w")))
        new = build_table(tpl_tbl, header, rows, aligns, widths, total)
        tpl_tbl.addprevious(new)
        tpl_tbl.getparent().remove(tpl_tbl)
        point = new
        for e in render(after, text_proto, p_bullet, p_spacer, t_proto, leading_spacer=True):
            point.addnext(e)
            point = e
    for h in holders:
        h.getparent().remove(h)


def render(blocks, text_proto, p_bullet, p_spacer, t_proto, leading_spacer=False, trailing_spacer=False):
    """Word elements for the blocks, with one spacing paragraph between blocks of different kinds."""
    out, prev = [], None
    for b in blocks:
        kind = b[0]
        if (prev is not None and not (prev == kind == "li") and prev != "cap") or (prev is None and leading_spacer):
            out.append(copy.deepcopy(p_spacer))
        if kind == "p":
            p = copy.deepcopy(text_proto)
            fill_runs(p, b[1], first_run_rpr(text_proto))
            out.append(p)
        elif kind == "li":
            p = copy.deepcopy(p_bullet)
            fill_runs(p, b[1], first_run_rpr(p_bullet))
            out.append(p)
        elif kind == "cap":
            p = copy.deepcopy(text_proto)
            fill_runs(p, b[1], first_run_rpr(text_proto), bold_all=True)
            set_jc(p, "left")
            keep_next(p)
            out.append(p)
        else:
            _, header, rows, aligns, widths = b
            out.append(build_table(t_proto, header, rows, aligns, widths, TABLE_WIDTH))
        prev = kind
    if out and trailing_spacer:
        out.append(copy.deepcopy(p_spacer))
    # a paragraph right before a table stays with it
    for a, b in zip(out, out[1:]):
        if a.tag == W_P and b.tag == W_TBL:
            keep_next(a)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
