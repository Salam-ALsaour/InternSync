# SDD – Word and PDF Build

`../InternSync_SDD_v1.0.docx` and `../InternSync_SDD_v1.0.pdf` are generated from [`../InternSync_SDD.md`](../InternSync_SDD.md) on the CSC 305 SDD template ([`../SDD_Template_IEEE1016.docx`](../SDD_Template_IEEE1016.docx), IEEE 1016 adapted for student projects). Edit the Markdown, then rebuild; do not edit the Word file by hand.

The tools are the ones of the SRS build, in [`../../tools`](../../tools/) (see [the SRS build](../../Project_4_SRS/build/README.md) for what they need). From this folder:

```bash
python ../../tools/gen_docx.py ../SDD_Template_IEEE1016.docx ../InternSync_SDD.md out.docx
python3 ../../tools/lo_finish.py out.docx ../InternSync_SDD_v1.0.docx ../InternSync_SDD_v1.0.pdf
```

On Windows with Word, use `..\..\tools\word_finish.ps1` for the second step, with absolute paths. Then delete `out.docx`.

The figures come from the [diagram pack](../../InternSync_Diagrams/README.md) and from [`../figures`](../figures/): `class_report_review.png` and `runtime_architecture.png` are PNG exports of the Archify diagrams in `.archify/class-report-review-…` and `.archify/architecture-internsync-overview-…` at the repository root.
