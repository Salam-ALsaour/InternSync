# Mid Status Report – Word and PDF Build

`../InternSync_Mid_Status_Report_v1.1.docx` and `../InternSync_Mid_Status_Report_v1.1.pdf` are generated from [`../InternSync_Mid_Status_Report.md`](../InternSync_Mid_Status_Report.md) on the official course template, `Project_Status_Report_Template.docx` (Project Status Report, CSC 305 Project 5). Edit the Markdown, then rebuild; do not edit the Word file by hand.

`fill_status_report.py` keeps the template as it is and fills it:

- Each `##` heading of the Markdown goes under the template's label of the same name ("Project Title:", "Reporting Period:", "Team Information:", "Summary of Progress:", "Tasks Completed:", "Tasks In Progress:", "Upcoming Tasks:", "Notes / Comments:"). The template's example text is replaced.
- The template's tables are filled in place. A table may have more columns than the template's (Student ID, Due, Action), but every template column stays, in order; the script stops if one is missing.
- The template's second "Upcoming Tasks:" label heads its Issue | Impact | Owner | Status table, so the script renames it "Issues and Risks:".
- Headings the template does not have (Team Members and Responsibilities, Revision History) become new labels in the template's style. Extra tables follow the section's template table and are copies of the template's table, so they look the same.
- The Signature and Date cells of the team table are left empty for the members to sign.

From this folder, with the Python packages of the SRS build (see [the SRS build](../../RSR/build/README.md)):

```bash
python fill_status_report.py Project_Status_Report_Template.docx ../InternSync_Mid_Status_Report.md ../InternSync_Mid_Status_Report_v1.1.docx
python3 ../../tools/lo_finish.py ../InternSync_Mid_Status_Report_v1.1.docx - ../InternSync_Mid_Status_Report_v1.1.pdf
```

The Word file is final as generated (the report has no table of contents to build); the second command only makes the PDF with LibreOffice. With Word, open the Word file and save it as PDF instead.

Version 1.0 was built on a stand-in template before the official one was available; it is kept in [`../old`](../old/).
