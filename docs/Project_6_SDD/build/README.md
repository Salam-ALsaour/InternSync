# SDD – Word and PDF Build

`../InternSync_SDD_v1.1.docx` and `../InternSync_SDD_v1.1.pdf` are generated from [`../InternSync_SDD.md`](../InternSync_SDD.md) on the official 2026 course SDD template ([`../SDD_Template_Students_2026.docx`](../SDD_Template_Students_2026.docx)); the 2026 rubric is [`../SDD_Evaluation_Rubric_2026.docx`](../SDD_Evaluation_Rubric_2026.docx). Edit the Markdown, then rebuild; do not edit the Word file by hand. Version 1.0, made on the earlier template, is kept in [`../old`](../old/).

`gen_sdd_docx.py` fills the template:

- the cover page: the project title, the team in the template's table (name and student ID; the signature and date columns stay empty for the members to sign), then the advisor, course, version, date, and standard;
- a revision history before the template's own table of contents;
- the eight numbered sections of the template, each filled from the matching `## n.` section of the Markdown; the template's guidance text is removed.

It understands the Markdown used in the SDD: headings `###` and `####` (Heading 2 and 3 under the template's numbered Heading 1), paragraphs, `-` bullets, numbered items, pipe tables, images, and bold `Table x.y – …` / `Figure x.y – …` captions (the appendices use letters, as in `Table A.1`). A block quote (`>`) is kept out of the Word file. Arabic words inside an English sentence should stay short and be separated by Latin words, because Word reorders runs of right-to-left characters.

**Needs:** Python with `python-docx` (the backend's `.venv` has it), and Microsoft Word on Windows, or LibreOffice elsewhere.

From this folder, in PowerShell on Windows:

```powershell
..\..\..\backend\.venv\Scripts\python gen_sdd_docx.py ..\SDD_Template_Students_2026.docx ..\InternSync_SDD.md "$PWD\out.docx"
```

```powershell
..\..\tools\word_finish.ps1 -InDocx "$PWD\out.docx" -OutDocx "$PWD\..\InternSync_SDD_v1.1.docx" -OutPdf "$PWD\..\InternSync_SDD_v1.1.pdf"
```

Without Word, the second step is `python3 ../../tools/lo_finish.py out.docx ../InternSync_SDD_v1.1.docx ../InternSync_SDD_v1.1.pdf`. Then delete `out.docx` and copy the PDF to [`../../Final_Submission`](../../Final_Submission/). Word needs absolute paths, hence `$PWD`.

The figures come from the [diagram pack](../../InternSync_Diagrams/README.md) and from [`../figures`](../figures/): `class_report_review.png` and `runtime_architecture.png` are PNG exports of the Archify diagrams in `.archify/class-report-review-…` and `.archify/architecture-internsync-overview-…` at the repository root.
