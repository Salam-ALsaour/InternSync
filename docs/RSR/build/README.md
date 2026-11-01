# SRS – Word and PDF Build

`../InternSync_SRS_v1.3.docx` and `../InternSync_SRS_v1.3.pdf` are generated from [`../InternSync_SRS.md`](../InternSync_SRS.md) on the CSC 305 SRS template (`SRS_Template_IEEE830.docx`, IEEE 830 adapted for student projects). Edit the Markdown, then rebuild; do not edit the Word file by hand.

The build tools are shared with the SDD and STS and live in [`../../tools`](../../tools/):

- `gen_docx.py` fills the template: cover page (project title, team, advisor, version, date), revision history, table of contents, sections from the Markdown, and the template's evaluation page at the end.
- `word_finish.ps1` opens the result in Microsoft Word, builds the table of contents, and exports the PDF.
- `lo_finish.py` does the same with LibreOffice, for computers without Word.

**Needs:** Python with `python-docx` (`pip install python-docx`), and either Microsoft Word on Windows or LibreOffice with its Python bridge (`python3-uno`).

From this folder, in PowerShell:

```powershell
python ..\..\tools\gen_docx.py SRS_Template_IEEE830.docx ..\InternSync_SRS.md "$PWD\out.docx"
```

```powershell
..\..\tools\word_finish.ps1 -InDocx "$PWD\out.docx" -OutDocx "$PWD\..\InternSync_SRS_v1.3.docx" -OutPdf "$PWD\..\InternSync_SRS_v1.3.pdf"
```

Or, with LibreOffice instead of Word:

```bash
python3 ../../tools/lo_finish.py out.docx ../InternSync_SRS_v1.3.docx ../InternSync_SRS_v1.3.pdf
```

Then delete `out.docx`. Word needs absolute paths, hence `$PWD`.

The generator understands the Markdown used in the SRS: headings `##` – `####` (Heading 1 – 3), paragraphs, `-` bullets, numbered lists, pipe tables (`<br>` for a line break inside a cell), images, and bold `Table x.y – …` / `Figure x.y – …` captions. A block quote (`>`) is kept out of the Word file.
