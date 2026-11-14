"""UML class diagrams of the domain model as built (SDD Section 5.2).
13a: organizations, accounts, profiles, vacancies, and placement. 13b: training records and grading.
Attributes are the main columns of app/models; operations are the service functions that change the object
(each one is a checked state transition with an audit entry)."""
import logging
import sys
sys.path.insert(0, ".")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
from blocks import Canvas, AI_EDGE  # noqa: E402
from uml import cls, rel  # noqa: E402

COLW = 1.46
GAP = 0.44
X = [0.10 + i * (COLW + GAP) for i in range(4)]
W = 7.42


def box(c, k):
    return c.boxes[k]


def top(c, k, f=0.5):
    x, y, w, h = c.boxes[k]
    return (x + w * f, y)


def bot(c, k, f=0.5):
    x, y, w, h = c.boxes[k]
    return (x + w * f, y + h)


def hlink(c, a, b, y, m0, m1, label=None, kind="assoc", fs=5.6):
    """Horizontal relation in the gap between column a (left) and column b (right) at height y."""
    x0, x1 = X[a] + COLW, X[b]
    rel(c, [(x0, y), (x1, y)], kind, m0, m1)
    if label:
        c.ax.text((x0 + x1) / 2, y - 0.05, label, fontsize=fs, style="italic", color="#333333", ha="center",
                  va="bottom", linespacing=1.05)


# =================================================================== 13a
c = Canvas(W, 6.15)
R1, R2, R3 = 0.12, 1.80, 4.20
cls(c, "UNI", X[0], R1, COLW, "University",
    ["name_en, name_ar: text", "email_domains: text[]", "gpa_scale: numeric", "is_active: bool"])
cls(c, "COL", X[1], R1, COLW, "College",
    ["name_en, name_ar: text", "retention_months: int", "is_active: bool"],
    ["+ transfer_coordinator(to)"])
cls(c, "CYC", X[2], R1, COLW, "TrainingCycle",
    ["name: text", "type: co_op | summer", "start_date, end_date: date", "weeks: int; working_days: int[]",
     "report_weekday, report_time", "status: open | closed"],
    ["+ build_weeks()", "+ close()", "+ reopen(reason)"])
cls(c, "VR", X[3], R1, COLW, "VerificationRequest",
    ["kind: student | coordinator |", "    company", "submitted_data: json", "status: pending | approved |",
     "    rejected", "reason: text"],
    ["+ approve(cycle)", "+ reject(reason)"])
cls(c, "CMP", X[0], R2, COLW, "Company",
    ["name: text", "commercial_reg_no: text", "city, website: text", "status: pending | verified |",
     "    rejected | suspended"],
    ["+ suspend(reason)", "+ reactivate()", "+ transfer_admin(to)"])
cls(c, "USR", X[1], R2, COLW, "User",
    ["email: text", "password_hash: text (Argon2id)", "role: student |", "    company_supervisor |",
     "    academic_supervisor |", "    coordinator | platform_admin", "language: ar | en", "is_company_admin: bool",
     "verification_status: text", "consent_at: timestamptz", "is_active: bool", "failed_logins; locked_until"],
    ["+ register(kind, documents)", "+ login(email, password)", "+ give_consent()", "+ deactivate()"])
R2b = R2 + 0.45
cls(c, "PRF", X[2], R2b, COLW, "StudentProfile",
    ["student_number: text", "gpa: numeric; level: int", "interests: text[]", "embedding: halfvec(384)",
     "embedding_model: text"],
    ["+ upload_cv(file)", "+ confirm_skills(skills)"], kind="ai")
cls(c, "SKL", X[3], R2b, COLW, "Skill",
    ["name_en, name_ar: text", "synonyms: text[]", "match_terms: text[]", "is_active: bool"])
cls(c, "VAC", X[0], R3, COLW, "Vacancy",
    ["title, city, description: text", "training_type: co_op | summer", "training_start, training_end",
     "seats: int; min_gpa: numeric", "application_deadline", "status: draft | published |", "    closed",
     "embedding: halfvec(384)"],
    ["+ publish()", "+ close()"], kind="ai")
cls(c, "APP", X[1], R3, COLW, "Application",
    ["status: submitted | accepted |", "    declined | withdrawn |", "    placed | placement_cancelled",
     "fit_score: numeric (snapshot)", "match_mode, model_version"],
    ["+ apply(vacancy)", "+ withdraw()", "+ accept() / decline()"])
cls(c, "PLC", X[2], R3, COLW, "Placement",
    ["status: active | completed |", "    cancelled", "cancel_reason: text"],
    ["+ confirm(cs, as)", "+ cancel(reason)", "+ change_supervisor(as)"])

hlink(c, 0, 1, R1 + 0.33, "1", "1..*", None, kind="comp")
hlink(c, 1, 2, R1 + 0.33, "1", "*", "runs")
rel(c, [bot(c, "COL"), top(c, "USR")], "assoc", "0..1", "*")
c.ax.text(X[1] + COLW / 2 - 0.05, (bot(c, "COL")[1] + R2) / 2, "belongs to", fontsize=5.6, style="italic",
          color="#333333", ha="right", va="center")
hlink(c, 0, 1, R2 + 0.50, "0..1", "*", "employs")
# user -> verification requests (above the profile row)
yv = R2 + 0.17
vx = X[3] + COLW * 0.5
rel(c, [(X[1] + COLW, yv), (vx, yv), bot(c, "VR")], "assoc", "1", "*")
c.ax.text(X[2] + 0.55, yv - 0.05, "submits", fontsize=5.6, style="italic", color="#333333", ha="center", va="bottom")
yp = R2b + 0.40
hlink(c, 1, 2, yp, "1", "0..1", "has")
hlink(c, 2, 3, yp, "*", "*", "confirmed\nskills")
rel(c, [bot(c, "CMP"), top(c, "VAC")], "comp", "1", "*")
c.ax.text(X[0] + COLW / 2 + 0.06, (bot(c, "CMP")[1] + R3) / 2 + 0.05, "publishes", fontsize=5.6, style="italic",
          color="#333333", ha="left", va="center")
ya = R3 + 0.42
hlink(c, 0, 1, ya, "1", "*", "receives")
xu = X[1] + COLW * 0.3
rel(c, [(xu, bot(c, "USR")[1]), (xu, R3)], "assoc", "1", "*")
c.ax.text(xu + 0.1, (bot(c, "USR")[1] + R3) / 2, "applies\n(student)", fontsize=5.6, style="italic", color="#333333",
          ha="left", va="center")
hlink(c, 1, 2, ya, "1", "0..1", "becomes")
# placement -> supervisors (CS and AS)
ys = bot(c, "USR")[1] - 0.24
sx = X[2] + 0.30
rel(c, [(sx, R3), (sx, ys), (X[1] + COLW, ys)], "assoc", "*", "2")
c.ax.text(sx + 0.06, (ys + R3) / 2 + 0.05, "supervised by\n(CS and AS)", fontsize=5.6, style="italic",
          color="#333333", ha="left", va="center")
# placement -> cycle (channel between columns C and D)
chx = X[3] - 0.12
yc1 = R1 + 1.00
yr = R3 + box(c, "PLC")[3] * 0.22
rel(c, [(X[2] + COLW, yr), (chx, yr), (chx, yc1), (X[2] + COLW, yc1)], "assoc", "*", "1")
c.ax.text(chx - 0.04, 3.75, "in cycle", fontsize=5.6, style="italic", color="#333333", ha="right", va="center")
# vacancy -> skills (around the bottom and the right edge)
yb = max(bot(c, k)[1] for k in ("VAC", "APP", "PLC")) + 0.14
rx = W - 0.08
sk = box(c, "SKL")
ysk = sk[1] + sk[3] * 0.6
rel(c, [bot(c, "VAC", 0.5), (X[0] + COLW * 0.5, yb), (rx, yb), (rx, ysk), (sk[0] + sk[2], ysk)], "assoc", "*", "*")
c.ax.text(4.3, yb - 0.04, "required and preferred skills", fontsize=5.6, style="italic", color="#333333",
          ha="center", va="bottom")
c.ax.text(X[3], R3 + 0.02, "Notation\n◆  composition (the part cannot exist alone)\n—  association, with multiplicities\n"
          "Orange: holds an AI embedding (halfvec)\n+ op(): service function that changes the\n"
          "   object; each is checked and audited", fontsize=5.6, color="#404040", va="top", linespacing=1.3)
c.save("../png/13a_class_organizations_placement")

# =================================================================== 13b
c = Canvas(W, 6.12)
R1, R2, R3 = 0.12, 1.75, 4.05
cls(c, "CYC", X[0], R1, COLW, "TrainingCycle", ["(see Figure a)"], kind="ref")
cls(c, "GC", X[1], R1, COLW, "GradeComponent",
    ["name_en, name_ar: text", "weight: numeric (sum 100)", "source: company_evaluation |", "    academic"])
cls(c, "RC", X[2], R1, COLW, "RubricCriterion",
    ["name_en, name_ar: text", "levels: json (1–5, described)", "position: int"])
cls(c, "CW", X[3], R1, COLW, "CycleWeek",
    ["week_no: int", "starts_on, ends_on: date", "scheduled_days: int", "report_due_at: timestamptz"])
cls(c, "PLC", X[0], R2, COLW, "Placement", ["(see Figure a)"], kind="ref")
cls(c, "RS", X[1], R2, COLW, "ReportSlot",
    ["kind: weekly | final", "week_no: int", "due_at: timestamptz", "status: draft | submitted |",
     "    revision_requested |", "    accepted | closed_missing", "is_late, is_missing: bool"],
    ["+ save_draft(fields)", "+ submit()", "+ accept()", "+ request_revision(comment)", "+ close_missing()"])
cls(c, "RV", X[2], R2, COLW, "ReportVersion",
    ["version_no: int", "tasks_performed, learning,", "    challenges, next_week_plan", "body_text: text (final)",
     "submitted_at; is_late: bool"])
cls(c, "SIM", X[3], R2, COLW, "SimilarityCheck",
    ["status: pending | done | failed", "max_score: numeric", "is_flagged: bool; threshold", "model_version: text",
     "decision: no_issue |", "    overlap_confirmed"],
    ["+ run()", "+ decide(decision, comment)"], kind="ai")
cls(c, "ATT", X[0], R3, COLW, "AttendanceWeek",
    ["week_no: int", "scheduled_days: int", "attended_days: int", "unlocked_until: timestamptz"],
    ["+ record(days)", "+ record_full()", "+ unlock(reason, until)"])
cls(c, "EV", X[1], R3, COLW, "Evaluation",
    ["type: periodic | final", "status: draft | submitted", "scores: criterion → 1..5", "overall_comment: text",
     "mean_score: numeric", "reopen_count: int"],
    ["+ save(scores, comment)", "+ submit()", "+ reopen(reason)"])
cls(c, "GR", X[2], R3, COLW, "Grade",
    ["status: draft | submitted | final", "scores: component → 0..100", "total: numeric", "return_comment: text",
     "reopen_reason: text"],
    ["+ save_scores(scores)", "+ submit()", "+ approve()", "+ return(comment)", "+ reopen(reason)",
     "+ total(): Σ weight × score / 100"])
cls(c, "CERT", X[3], R3, COLW, "Certificate",
    ["code: text (26 characters)", "status: valid | revoked", "issued_at: timestamptz", "revoke_reason: text"],
    ["+ issue()", "+ revoke(reason)", "+ verify(code)  «public»"])

hlink(c, 0, 1, R1 + 0.30, "1", "1..*", None, kind="comp")
yd1, yd2 = R1 + 1.18, R1 + 1.36
for k, f, yd in (("RC", 0.15, yd1), ("CW", 0.15, yd2)):
    xs = X[0] + COLW * (0.62 if k == "RC" else 0.85)
    xe = box(c, k)[0] + COLW * f
    rel(c, [(xs, bot(c, "CYC")[1]), (xs, yd), (xe, yd), (xe, bot(c, k)[1])], "comp", "1", "1..*")
c.ax.text(X[1] + COLW / 2, yd1 - 0.04, "defines (grade components, rubric, weeks)", fontsize=5.6, style="italic",
          color="#333333", ha="center", va="bottom", bbox=dict(boxstyle="square,pad=0.03", fc="white", ec="none"))
yr = R2 + 0.32
hlink(c, 0, 1, yr, "1", "*", "has slots", kind="comp")
hlink(c, 1, 2, yr, "1", "1..*", "versions", kind="comp")
hlink(c, 2, 3, yr, "1", "0..1", "checked by")
rel(c, [bot(c, "PLC", 0.3), (X[0] + COLW * 0.3, R3)], "comp", "1", "*")
c.ax.text(X[0] + COLW * 0.3 + 0.1, (bot(c, "PLC")[1] + R3) / 2, "attendance\nweeks", fontsize=5.6, style="italic",
          color="#333333", ha="left", va="center")
# placement -> evaluation, grade, certificate along a line under the reports row
yb = max(bot(c, k)[1] for k in ("RS", "RV", "SIM")) + 0.16
px = X[0] + COLW * 0.85
rel(c, [bot(c, "PLC", 0.85), (px, yb)], "comp", "1")
for k, m in (("EV", "0..2"), ("GR", "1"), ("CERT", "0..*")):
    xk = box(c, k)[0] + COLW * 0.5
    rel(c, [(px, yb), (xk, yb), (xk, R3)], "assoc", None, m)
c.ax.text(X[2] + 0.2, yb - 0.04, "placement records", fontsize=5.6, style="italic", color="#333333", ha="center",
          va="bottom")
yg = R3 + 0.36
hlink(c, 1, 2, yg, "0..1", "1", "final one\nfeeds")
hlink(c, 2, 3, yg, "1", "0..*", "issued\nwhen Final")
yn = max(bot(c, k)[1] for k in ("ATT", "EV", "GR", "CERT")) + 0.12
c.ax.text(X[0], yn, "Scores: an Evaluation holds one score (1–5) per rubric criterion of the cycle; a Grade holds one "
          "score (0–100) per grade component.\nThe company component of the grade is the mean of the final evaluation "
          "÷ 5 × 100. Orange: AI result (advisory, never changes a status).", fontsize=5.8, color="#404040", va="top",
          linespacing=1.35)
c.save("../png/13b_class_training_grading")
print("ok")
