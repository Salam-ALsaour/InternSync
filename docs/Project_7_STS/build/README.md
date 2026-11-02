# STS – Word and PDF Build

`../InternSync_STS_v1.0.docx` and `../InternSync_STS_v1.0.pdf` are generated from [`../InternSync_STS.md`](../InternSync_STS.md) on the CSC 305 STS template ([`../STS_Template_IEEE829_Students.docx`](../STS_Template_IEEE829_Students.docx), IEEE 829 adapted for student projects). Edit the Markdown, then rebuild; do not edit the Word file by hand.

The table of Appendix 11.2 is generated from the acceptance tests and test reports of the increments. After a change to them, refresh it first (from the repository root):

```bash
python docs/Project_7_STS/build/acceptance_table.py
```

Then, from this folder, with the tools of the SRS build in [`../../tools`](../../tools/) (see [the SRS build](../../Project_4_SRS/build/README.md) for what they need):

```bash
python ../../tools/gen_docx.py ../STS_Template_IEEE829_Students.docx ../InternSync_STS.md out.docx
python3 ../../tools/lo_finish.py out.docx ../InternSync_STS_v1.0.docx ../InternSync_STS_v1.0.pdf
```

On Windows with Word, use `..\..\tools\word_finish.ps1` for the second step, with absolute paths. Then delete `out.docx`.
