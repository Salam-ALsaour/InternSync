# Mid Status Report – Word and PDF Build

`../InternSync_Mid_Status_Report_v1.0.docx` and `../InternSync_Mid_Status_Report_v1.0.pdf` are generated from [`../InternSync_Mid_Status_Report.md`](../InternSync_Mid_Status_Report.md). Edit the Markdown, then rebuild; do not edit the Word file by hand.

The assignment asks for the official Project Status Report template, which was not available when the report was written. `Status_Report_Template.docx` is a stand-in made by `make_template.py` from the course SDD template, so the report has the course header, footer, and cover. When the official template arrives, put it here and build from it instead: `gen_docx.py` fills any course template that has the same cover lines and the "Table of Contents" and "Evaluation" headings.

From this folder, with the tools of the SRS build in [`../../tools`](../../tools/) (see [the SRS build](../../RSR/build/README.md) for what they need):

```bash
python make_template.py ../../SDD/build/SDD_Template_IEEE1016.docx Status_Report_Template.docx   # only to remake the stand-in
python ../../tools/gen_docx.py Status_Report_Template.docx ../InternSync_Mid_Status_Report.md out.docx
python3 ../../tools/lo_finish.py out.docx ../InternSync_Mid_Status_Report_v1.0.docx ../InternSync_Mid_Status_Report_v1.0.pdf
```

On Windows with Word, use `..\..\tools\word_finish.ps1` for the last step, with absolute paths. Then delete `out.docx`.
