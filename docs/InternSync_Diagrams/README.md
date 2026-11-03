# InternSync – Diagram Pack (v1.2)

Requirements and design diagrams, consistent with [SRS v1.3](../Project_4_SRS/InternSync_SRS.md), [SPMP v1.2](../Project_3_SPMP/InternSync_SPMP.md), and the [design document](../Design/InternSync_Design.md).

- `png/` and `svg/` hold the figures; `source/` holds their editable sources.
- `InternSync_Diagrams.pdf` is the printable pack, built by `source/build_pack.py`.
- `InternSync_Diagrams_v1.0.pdf` is the first version, kept because it contains the earlier ERD and deployment options.

**Colour key:** blue = system behaviour or people; orange = AI-supported (advisory) behaviour; green = approved / final state or the chosen option; grey dashed = external service.

| **No.** | **Diagram** | **Source** | **Used in** |
|:--:|:---|:---|:---|
| 1 | [Use case diagram](png/01_use_case.png) | `01_use_case.py` | SRS 3.2 |
| 2 | [Context diagram](png/02_context.png) | `02_context.dot` | SRS 2.1 |
| 3a | [Activity – registration, setup, and placement](png/03a_activity_setup_placement.png) | `03_activity_lifecycle.py` | SRS 2.2 |
| 3b | [Activity – training and grading](png/03b_activity_training_grading.png) | `03_activity_lifecycle.py` | SRS 2.2 |
| 4a | [Report slot states](png/04a_report_states.png) | `04a_report_states.dot` | SRS 3.1.10, design 5.1 |
| 4b | [Grade states](png/04b_grade_states.png) | `04b_grade_states.dot` | SRS 3.1.10, design 5.1 |
| 4c | [Vacancy states](png/04c_vacancy_states.png) | `04c_vacancy_states.dot` | SRS 6.2, design 5.1 |
| 4d | [Application and placement states](png/04d_application_states.png) | `04d_application_states.dot` | SRS 6.2, design 5.1 |
| 5 | [System architecture](png/05_architecture.png) | `05_architecture.py` | Design 2.1 |
| 6a | [ERD – organizations, accounts, cycles, student profiles](png/06a_erd_organizations_profiles.png) | `06_erd.py` | Design 4.2 |
| 6b | [ERD – vacancies, matching, applications, placements](png/06b_erd_vacancies_placement.png) | `06_erd.py` | Design 4.2 |
| 6c | [ERD – reports, similarity, attendance, evaluations, grades, certificates](png/06c_erd_training_grading.png) | `06_erd.py` | Design 4.2 |
| 6d | [ERD – verification and platform services](png/06d_erd_platform.png) | `06_erd.py` | Design 4.2 |
| 7a | [Sequence – CV upload and matching](png/07a_seq_cv_matching.png) | `07a_seq_cv_matching.mmd` | Design 6 |
| 7b | [Sequence – weekly report and review](png/07b_seq_weekly_report.png) | `07b_seq_weekly_report.mmd` | Design 5.1 |
| 7c | [Sequence – grade submission and approval](png/07c_seq_grade_approval.png) | `07c_seq_grade_approval.mmd` | Design 5.1 |
| 7d | [Sequence – scheduled reminders and escalation](png/07d_seq_scheduler.png) | `07d_seq_scheduler.mmd` | Design 5.3 |
| 8 | [AI pipelines](png/08_ai_pipelines.png) | `08_ai_pipelines.py` | Design 6 |
| 9 | [Deployment (zero cost, CR-01)](png/09_deployment.png) | `09_deployment.py` | Design 3.2 |
| 10 | [Schedule (Gantt)](png/10_gantt_schedule.png) | `10_charts.py` | SPMP 4 |
| 11 | [Requirements by area and priority](png/11_requirements_priority.png) | `10_charts.py` | SRS 6.3.2 |

## Regenerating

Run these from `source/`:

| **Figures** | **Command** | **Needs** |
|:---|:---|:---|
| Block diagrams (1, 3, 5, 8, 9), charts (10, 11) | `python <file>.py` | `matplotlib` |
| ERD (6a–6d) | `python 06_erd.py` | Graphviz `dot` on the PATH (without it, only the `.dot` files are written) |
| State machines, context (2, 4a–4d) | `dot -Tpng -Gdpi=250 <file>.dot -o ../png/<file>.png` | Graphviz |
| Sequences (7a–7d) | `mmdc -i <file>.mmd -o ../png/<file>.png -c mermaid.json -s 3 -b white` | Mermaid CLI |
| Printable pack | `python build_pack.py` | `pymupdf` |

The ERD must match the data dictionary in Section 4.3 of the design document, which is authoritative.
