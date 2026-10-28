# InternSync – Project Documents

CSC 305 – Software Engineering · Semester 1 – 2026/2027 · Group 3

## Documents

| **Document** | **Maintained file (edit this)** | **Submitted snapshots** | **Version** |
|:---|:---|:---|:--:|
| Project Idea Form | – (frozen) | [MINISTRY OF EDUCATION-1.pdf](Project%20Idea%20%20Team%20&%20Problem%20Definition/MINISTRY%20OF%20EDUCATION-1.pdf) | Sep 5, 2026 |
| Project Proposal | – (frozen) | [InternSync_Project_Proposal-1.pdf](Project%20Proposal%20%20Process%20&%20Feasibility/InternSync_Project_Proposal-1.pdf) | Oct 2, 2026 |
| Software Project Management Plan | [InternSync_SPMP.md](Software%20Project%20Management%20Plan%20%28SPMP%29/InternSync_SPMP.md) | InternSync_SPMP-1.pdf (v1.0) | 1.6 |
| Software Requirements Specification | [InternSync_SRS.md](RSR/InternSync_SRS.md) | [InternSync_SRS_v1.3.pdf](RSR/InternSync_SRS_v1.3.pdf) (submitted Oct 23, 2026) and [.docx](RSR/InternSync_SRS_v1.3.docx), generated on the course template; the v1.0 draft is in [RSR/old](RSR/old/) | 1.6 |
| System Design Document | [InternSync_Design.md](Design/InternSync_Design.md) | – | 1.6 |
| Wireframes (clickable prototype) | [Claude Design canvas](https://claude.ai/artifact/GUCAYYDPvkkBiwntVfJWJA); sources in [Design/wireframes](Design/wireframes/) | – | 1.1 |
| API Specification | [InternSync_API_Spec.md](Design/InternSync_API_Spec.md) | – | 1.5 |
| Diagram pack | [InternSync_Diagrams/README.md](InternSync_Diagrams/README.md) and its sources | InternSync_Diagrams.pdf (v1.2), InternSync_Diagrams_v1.0.pdf | 1.2 |
| Increment documents | Increment 1: [requirements](Increments/Increment_1/01_Requirements.md), [design](Increments/Increment_1/02_Design.md), [test report](Increments/Increment_1/04_Test_Report.md). Increment 2: [requirements](Increments/Increment_2/01_Requirements.md), [design](Increments/Increment_2/02_Design.md), [test report](Increments/Increment_2/04_Test_Report.md). Increment 3: [requirements](Increments/Increment_3/01_Requirements.md), [design](Increments/Increment_3/02_Design.md), [test report](Increments/Increment_3/04_Test_Report.md). Increment 4: [requirements](Increments/Increment_4/01_Requirements.md), [design](Increments/Increment_4/02_Design.md), [test report](Increments/Increment_4/04_Test_Report.md), [UAT plan](Increments/Increment_4/05_UAT_Plan.md) | – | – |
| Key results | [Key_Results.md](Key_Results.md): every measured result of the project in one place, for the final presentation | – | – |
| Deployment | [Deployment.md](Deployment.md): the reference deployment and how to switch it on | – | 1.2 |
| Change requests | [Change_Requests.md](Change_Requests.md) | – | – |

## Rules

- **Markdown is the source of truth.** Edit the `.md` files. The SRS Word and PDF files are generated from the Markdown ([RSR/build](RSR/build/README.md)); the other PDF and DOCX files are snapshots of earlier versions. None of them is edited by hand.
- **The Idea Form and the Proposal are frozen.** Later decisions go into the SPMP, SRS, design document, and [Change_Requests.md](Change_Requests.md).
- **Every requirement change is a change request:** add a CR entry, update the affected documents, and add a row to their revision history.
- **Diagrams** are edited in `InternSync_Diagrams/source/` and regenerated; see the [diagram pack README](InternSync_Diagrams/README.md).

## Exporting for Submission

Install pandoc once:

```bash
winget install --id JohnMacFarlane.Pandoc -e
```

The SRS is built on the course template with its own script; see [RSR/build/README.md](RSR/build/README.md).

For the other documents, from this `docs` folder, export to Word with pandoc (open the result in Word and save as PDF if a PDF is needed):

```bash
pandoc "Design/InternSync_Design.md" --resource-path="Design" -o "InternSync_Design_v1.3.docx"
```

`--resource-path` must point to the document's own folder so that the diagram images are found.
