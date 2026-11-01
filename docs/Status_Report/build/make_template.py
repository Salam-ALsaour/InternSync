"""Make the stand-in Project Status Report template from the course SDD template: the same IAU header, footer, and
cover lines, with the title changed and the SDD rubric removed. Used until the official Project Status Report
template is available; gen_docx.py fills either.

    python make_template.py SDD_Template_IEEE1016.docx Status_Report_Template.docx"""
import sys

import docx
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

src, out = sys.argv[1], sys.argv[2]
doc = docx.Document(src)
P = doc.paragraphs


def retitle(p, text):
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""


retitle(P[0], "Project Status Report")
retitle(P[1], "Mid Status Report – Project 5")
body = doc.element.body
children = list(body.iterchildren())
start = next(i for i, el in enumerate(children)
             if el.tag == qn("w:p") and Paragraph(el, doc).text.strip() == "To be completed by the instructor or supervisor.")
for el in children[start + 1:]:
    if el.tag != qn("w:sectPr"):  # keep the section properties (page size, header, footer)
        body.remove(el)
doc.save(out)
print("saved", out)
