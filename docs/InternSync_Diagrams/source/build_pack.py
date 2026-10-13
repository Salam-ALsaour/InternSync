"""Build the diagram pack PDF (../InternSync_Diagrams.pdf) from the PNG figures. Needs PyMuPDF (`pip install pymupdf`)."""
import html

import pymupdf

VERSION = "v1.1"
NAVY, GREY = "#1F3864", "#595959"

# (number, title, what it shows, where to use it, [png files])
FIGURES = [
    ("1", "Use case diagram", "Actors, use cases UC-01 to UC-15, include / extend relations",
     "SRS 3.3 (Table 3.1)", ["01_use_case"]),
    ("2", "Context diagram", "System boundary, users and external services", "SRS 3.1 (Figure 3.1)", ["02_context"]),
    ("3a", "Activity diagram — setup and placement", "Swimlanes from opening a cycle to a confirmed placement",
     "SRS 3.2, design document", ["03a_activity_setup_placement"]),
    ("3b", "Activity diagram — training and grading", "Weekly loop, final evaluation, grade approval",
     "SRS 3.2, design document", ["03b_activity_training_grading"]),
    ("4a, 4b", "State machines — report and grade", "Report slot and grade life cycles",
     "SRS 4.9 (Figures 4.1, 4.2); design 5.1", ["04a_report_states", "04b_grade_states"]),
    ("4c, 4d", "State machines — vacancy and application", "Vacancy and application / placement life cycles",
     "SRS 4.4; design 5.1", ["04c_vacancy_states", "04d_application_states"]),
    ("5", "System architecture", "Layers, API modules, AI services, scheduler, data", "Design 2.1, presentation",
     ["05_architecture"]),
    ("6a", "ERD — accounts, configuration, profiles, vacancies, matching", "Tables, keys and cardinalities (crow's foot)",
     "Design 4.2", ["06a_erd_accounts_matching"]),
    ("6b", "ERD — reports, similarity, attendance, evaluations, grades", "Tables, keys and cardinalities (crow's foot)",
     "Design 4.2", ["06b_erd_training_grading"]),
    ("6c", "ERD — platform services", "Sessions, tokens, files, notifications, audit, imports, settings, jobs",
     "Design 4.2", ["06c_erd_platform"]),
    ("7a", "Sequence — CV upload and matching", "Skill extraction, confirmation, ranking with fallback", "Design 6",
     ["07a_seq_cv_matching"]),
    ("7b", "Sequence — weekly report and review", "Submission, Late flag, similarity check, accept / revision",
     "Design 5.1", ["07b_seq_weekly_report"]),
    ("7c", "Sequence — grade submission and approval", "Preconditions, approve / return, notifications", "Design 5.1",
     ["07c_seq_grade_approval"]),
    ("7d", "Sequence — scheduled reminders and escalation", "15-minute jobs, idempotent notifications", "Design 5.3",
     ["07d_seq_scheduler"]),
    ("8", "AI pipelines", "Fit-score formula, explanation, similarity method", "Design 6, presentation",
     ["08_ai_pipelines"]),
    ("9", "Deployment", "Zero-cost reference deployment (chosen, CR-01) and the self-hosted option", "Design 3.2",
     ["09_deployment"]),
    ("10", "Schedule (Gantt)", "Activities T1–T9, milestones M1–M7, dependencies", "SPMP 4, progress presentations",
     ["10_gantt_schedule"]),
    ("11", "Requirements by area and priority", "116 requirements by area: Must / Should / Could", "SRS 9.2",
     ["11_requirements_priority"]),
]

CSS = f"""
* {{ font-family: sans-serif; }}
h1 {{ color: {NAVY}; font-size: 22px; margin: 0 0 4px 0; }}
.sub {{ color: {GREY}; font-size: 10px; margin-bottom: 14px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8px; }}
th {{ color: {NAVY}; text-align: left; border-bottom: 1px solid {NAVY}; padding: 3px; }}
td {{ border-bottom: 0.5px solid #CCCCCC; padding: 3px; vertical-align: top; }}
.note {{ color: {GREY}; font-size: 7.5px; margin-top: 10px; }}
h2 {{ color: {NAVY}; font-size: 13px; margin: 0; }}
.cap {{ color: {GREY}; font-size: 8.5px; margin-top: 2px; }}
"""


def footer(page, n):
    r = page.rect
    page.insert_text((40, r.height - 25), f"InternSync — Diagram pack {VERSION} · CSC 305 Group 3", fontsize=7,
                     color=(0.35, 0.35, 0.35))
    page.insert_text((r.width - 75, r.height - 25), f"Page {n}", fontsize=7, color=(0.35, 0.35, 0.35))


def main():
    doc = pymupdf.open()
    a4 = pymupdf.paper_rect("a4")
    # cover with index
    page = doc.new_page(width=a4.width, height=a4.height)
    rows, pno = [], 2
    for num, title, what, where, _ in FIGURES:
        rows.append(f"<tr><td><b>{num}</b></td><td>{html.escape(title)} (p. {pno})</td><td>{html.escape(what)}</td>"
                    f"<td>{html.escape(where)}</td></tr>")
        pno += 1
    body = (f"<h1>InternSync — Diagram pack</h1><div class='sub'>Requirements and design diagrams · {VERSION} · "
            "consistent with SRS v1.1, the SPMP v1.1 and the design document v1.0</div>"
            "<table><tr><th>No.</th><th>Diagram</th><th>What it shows</th><th>Where to use it</th></tr>"
            + "".join(rows) + "</table>"
            "<div class='note'>Colour key: blue = system behaviour or people; orange = AI-supported (advisory) behaviour; "
            "green = an approved / final state or the chosen option; grey dashed = external service.<br/>"
            "v1.1 (Oct 13, 2026): the ERD is redrawn in three parts to match the data dictionary of the design document "
            "(45 tables); the deployment is decided (zero cost, CR-01); UC-15 is now in SRS Table 3.1. Diagram 8 values "
            "are configurable defaults tuned on the labelled test sets. Editable sources (Python, Graphviz, Mermaid) are in "
            "the source folder; SVG files are in the svg folder.</div>")
    page.insert_htmlbox(pymupdf.Rect(45, 45, a4.width - 45, a4.height - 50), body, css=CSS)
    footer(page, 1)
    # one page per figure (two stacked images for the state-machine pairs)
    for i, (num, title, what, where, pngs) in enumerate(FIGURES, start=2):
        page = doc.new_page(width=a4.width, height=a4.height)
        page.insert_htmlbox(pymupdf.Rect(40, 36, a4.width - 40, 90),
                            f"<h2>Figure {num} — {html.escape(title)}</h2><div class='cap'>{html.escape(what)}. "
                            f"Use in: {html.escape(where)}.</div>", css=CSS)
        top, bottom = 95, a4.height - 45
        slot = (bottom - top) / len(pngs)
        for k, name in enumerate(pngs):
            rect = pymupdf.Rect(40, top + k * slot + 6, a4.width - 40, top + (k + 1) * slot - 6)
            page.insert_image(rect, filename=f"../png/{name}.png", keep_proportion=True)
        footer(page, i)
    doc.save("../InternSync_Diagrams.pdf", garbage=3, deflate=True)
    print("ok", doc.page_count, "pages")


if __name__ == "__main__":
    main()
