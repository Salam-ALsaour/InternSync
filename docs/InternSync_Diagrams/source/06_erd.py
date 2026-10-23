"""Generate four crow's-foot ERDs (Graphviz) from one data model.

The model must match Section 4.3 of docs/Design/InternSync_Design.md (the data dictionary is authoritative).
Writes 06a/06b/06c/06d .dot files and renders PNG and SVG with Graphviz `dot` when it is installed.
"""
import shutil
import subprocess

NAVY, HEAD_TXT, FILL, REF_FILL, REF_EDGE, AI = "#1F3864", "#FFFFFF", "#F5F8FC", "#F2F2F2", "#7F7F7F", "#C55A11"

# entity: list of (column, type, key)  key in {"PK","FK","PK, FK","UQ","FK, UQ",""}
E = {
    # ---------------------------------------------------------------- organizations and accounts
    "universities": [("id", "uuid", "PK"), ("name_en", "text", "UQ"), ("name_ar", "text", ""),
                     ("email_domains", "text[]", ""), ("gpa_scale", "numeric", ""), ("is_active", "bool", "")],
    "colleges": [("id", "uuid", "PK"), ("university_id", "uuid", "FK"), ("name_en, name_ar", "text", ""),
                 ("is_active", "bool", ""), ("(university_id, name_en)", "", "UQ")],
    "companies": [("id", "uuid", "PK"), ("name", "text", ""), ("commercial_reg_no", "text", "UQ"),
                  ("city, website", "text", ""), ("status", "pending … suspended", ""), ("verified_at", "ts", "")],
    "users": [("id", "uuid", "PK"), ("email", "text", "UQ"), ("password_hash", "text", ""),
              ("role", "ST | CS | AS | CO | PA", ""), ("name_en, name_ar", "text", ""), ("language", "ar | en", ""),
              ("college_id", "uuid", "FK"), ("company_id", "uuid", "FK"), ("is_company_admin", "bool", ""),
              ("email_confirmed_at", "ts", ""), ("verification_status", "pending … not_required", ""),
              ("is_active", "bool", ""), ("failed_logins, locked_until", "int, ts", ""),
              ("consent_at, last_login_at", "ts", "")],
    "account_tokens": [("id", "uuid", "PK"), ("user_id", "uuid", "FK"),
                       ("purpose", "confirmation | invitation | reset", ""), ("token_hash", "text", "UQ"),
                       ("expires_at, used_at, revoked_at", "ts", "")],
    "user_sessions": [("id (sid)", "uuid", "PK"), ("user_id", "uuid", "FK"),
                      ("created_at, last_seen_at, expires_at", "ts", ""), ("revoked_at, revoke_reason", "ts, text", "")],
    "push_subscriptions": [("id", "uuid", "PK"), ("user_id", "uuid", "FK"), ("endpoint", "text", "UQ"),
                           ("p256dh, auth", "text", "")],
    "verification_requests": [("id", "uuid", "PK"), ("user_id", "uuid", "FK"),
                              ("kind", "coordinator | company | student", ""), ("college_id", "uuid", "FK"),
                              ("company_id", "uuid", "FK"), ("submitted_data", "jsonb", ""),
                              ("status", "pending | approved | rejected", ""), ("reviewer_id", "uuid", "FK"),
                              ("decided_at, reason", "ts, text", ""), ("cycle_id", "uuid", "FK")],
    "verification_documents": [("id", "uuid", "PK"), ("request_id", "uuid", "FK"),
                               ("kind", "appointment … course_registration", ""), ("file_id", "uuid", "FK"),
                               ("purged_at", "ts", "")],
    # ---------------------------------------------------------------- cycles and configuration
    "training_cycles": [("id", "uuid", "PK"), ("college_id", "uuid", "FK"), ("name", "text", ""),
                        ("type", "coop | summer", ""), ("start_date, end_date, weeks", "date, int", ""),
                        ("working_days", "smallint[]", ""), ("report_weekday, report_time", "int, time", ""),
                        ("eval / final due dates", "ts", ""), ("status", "open | closed", ""),
                        ("rubric_locked_at, closed_at", "ts", ""), ("created_by", "uuid", "FK"),
                        ("(college_id, name)", "", "UQ")],
    "cycle_weeks": [("cycle_id", "uuid", "PK, FK"), ("week_no", "int", "PK"), ("starts_on, ends_on", "date", ""),
                    ("report_due_at", "ts", ""), ("scheduled_days", "int", "")],
    "grade_components": [("id", "uuid", "PK"), ("cycle_id", "uuid", "FK"), ("name_en, name_ar", "text", ""),
                         ("weight", "numeric, Σ = 100", ""), ("source", "company_eval | AS", ""), ("position", "int", "")],
    "rubric_criteria": [("id", "uuid", "PK"), ("cycle_id", "uuid", "FK"), ("name_en, name_ar", "text", ""),
                        ("levels", "jsonb 1–5", ""), ("position", "int", "")],
    "skills": [("id", "uuid", "PK"), ("name_en", "text", "UQ"), ("name_ar", "text", ""), ("synonyms", "text[]", ""),
               ("match_terms", "text[]", ""), ("is_active", "bool", "")],
    "skill_resources": [("id", "uuid", "PK"), ("skill_id", "uuid", "FK"), ("title, url", "text", ""),
                        ("estimated_effort, language", "text", "")],
    "majors": [("id", "uuid", "PK"), ("name_en", "text", "UQ"), ("name_ar", "text", "")],
    "system_settings": [("key", "text", "PK"), ("value", "jsonb", ""), ("updated_by", "uuid", "FK"),
                        ("updated_at", "ts", "")],
    # ---------------------------------------------------------------- students
    "student_profiles": [("user_id", "uuid", "PK, FK"), ("student_number", "text", ""), ("major_id", "uuid", "FK"),
                         ("gpa", "numeric(3,2)", ""), ("level", "int", ""), ("languages, interests", "text[]", ""),
                         ("skills_confirmed_at", "ts", ""), ("embedding", "halfvec(384)", ""),
                         ("embedding_model, embedded_at", "text, ts", "")],
    "enrollments": [("cycle_id", "uuid", "PK, FK"), ("student_id", "uuid", "PK, FK"),
                    ("verification_request_id", "uuid", "FK"), ("created_by", "uuid", "FK")],
    "cvs": [("id", "uuid", "PK"), ("student_id", "uuid", "FK"), ("version_no", "int", ""), ("file_id", "uuid", "FK"),
            ("extracted_text", "text", ""), ("text_status, language", "text", ""), ("uploaded_at", "ts", "")],
    "cv_extracted_skills": [("cv_id", "uuid", "PK, FK"), ("skill_id", "uuid", "PK, FK"), ("evidence", "text", "")],
    "student_skills": [("student_id", "uuid", "PK, FK"), ("skill_id", "uuid", "PK, FK"),
                       ("source", "extracted | manual", ""), ("confirmed_at", "ts", "")],
    # ---------------------------------------------------------------- vacancies and matching
    "vacancies": [("id", "uuid", "PK"), ("company_id", "uuid", "FK"), ("company_supervisor_id", "uuid", "FK"),
                  ("created_by", "uuid", "FK"), ("title, city, description", "text", ""),
                  ("training_type, start, end", "text, date", ""), ("min_gpa, seats", "numeric, int", ""),
                  ("application_deadline", "ts", ""), ("status", "draft | published | closed", ""),
                  ("embedding", "halfvec(384)", ""), ("embedding_model", "text", "")],
    "vacancy_skills": [("vacancy_id", "uuid", "PK, FK"), ("skill_id", "uuid", "PK, FK"),
                       ("kind", "required | preferred", "")],
    "vacancy_majors": [("vacancy_id", "uuid", "PK, FK"), ("major_id", "uuid", "PK, FK")],
    "vacancy_universities": [("vacancy_id", "uuid", "PK, FK"), ("university_id", "uuid", "PK, FK")],
    "applications": [("id", "uuid", "PK"), ("vacancy_id", "uuid", "FK"), ("student_id", "uuid", "FK"),
                     ("status", "submitted … placed", ""), ("withdraw_reason", "text", ""),
                     ("fit_score, match_mode, model_version", "numeric, text", ""), ("decided_by", "uuid", "FK"),
                     ("(vacancy_id, student_id)", "", "UQ")],
    "placements": [("id", "uuid", "PK"), ("application_id", "uuid", "FK, UQ"), ("student_id", "uuid", "FK"),
                   ("cycle_id", "uuid", "FK"), ("vacancy_id", "uuid", "FK"), ("company_supervisor_id", "uuid", "FK"),
                   ("academic_supervisor_id", "uuid", "FK"), ("status", "active | completed | cancelled", ""),
                   ("confirmed_by, confirmed_at", "uuid, ts", ""), ("cancel_reason", "text", ""),
                   ("(student_id, cycle_id) not cancelled", "", "UQ")],
    "match_scores": [("student_id", "uuid", "PK, FK"), ("vacancy_id", "uuid", "PK, FK"), ("fit_score", "numeric", ""),
                     ("semantic, required_ratio, preferred_ratio", "numeric", ""), ("mode", "semantic | basic", ""),
                     ("matched / missing skill ids", "uuid[]", ""), ("model_version, computed_at", "text, ts", "")],
    # ---------------------------------------------------------------- reports and similarity
    "report_slots": [("id", "uuid", "PK"), ("placement_id", "uuid", "FK"), ("kind, week_no", "weekly | final, int", ""),
                     ("due_at", "ts", ""), ("status", "draft … closed_missing", ""), ("is_late, is_missing", "bool", ""),
                     ("accepted_at, closed_at", "ts", ""), ("closed_by", "uuid", "FK")],
    "report_versions": [("id", "uuid", "PK"), ("slot_id", "uuid", "FK"), ("version_no", "int", ""),
                        ("tasks, learning, challenges, plan", "text", ""), ("summary, body_text", "text", ""),
                        ("submitted_at (null = draft)", "ts", ""), ("is_late", "bool", "")],
    "report_attachments": [("id", "uuid", "PK"), ("version_id", "uuid", "FK"), ("file_id", "uuid", "FK"),
                           ("role", "main | attachment", ""), ("position", "int", "")],
    "report_reviews": [("id", "uuid", "PK"), ("version_id", "uuid", "FK"), ("reviewer_id", "uuid", "FK"),
                       ("decision", "accepted | revision", ""), ("comment", "text", ""), ("created_at", "ts", "")],
    "report_comments": [("id", "uuid", "PK"), ("slot_id", "uuid", "FK"), ("author_id", "uuid", "FK"),
                        ("body", "text", ""), ("created_at", "ts", "")],
    "report_passages": [("id", "bigint", "PK"), ("version_id", "uuid", "FK"), ("university_id", "uuid", "FK"),
                        ("idx, char_start, char_end", "int", ""), ("text", "text", ""),
                        ("embedding", "halfvec(384)", "")],
    "similarity_checks": [("id", "uuid", "PK"), ("version_id", "uuid", "FK, UQ"), ("status", "pending | done | failed", ""),
                          ("max_score, is_flagged, threshold", "numeric, bool", ""), ("model_version", "text", ""),
                          ("decision, decision_comment", "no_issue | confirmed", ""), ("decided_by", "uuid", "FK")],
    "similarity_matches": [("id", "uuid", "PK"), ("check_id", "uuid", "FK"), ("source_version_id", "uuid", "FK"),
                           ("score", "numeric", ""), ("passages", "jsonb", "")],
    # ---------------------------------------------------------------- attendance and evaluations
    "attendance_weeks": [("id", "uuid", "PK"), ("placement_id", "uuid", "FK"), ("week_no", "int", ""),
                         ("scheduled_days, attended_days", "int", ""), ("note", "text", ""),
                         ("recorded_by", "uuid", "FK"), ("unlocked_until, unlock_reason", "ts, text", ""),
                         ("(placement_id, week_no)", "", "UQ")],
    "evaluations": [("id", "uuid", "PK"), ("placement_id", "uuid", "FK"), ("type", "periodic | final", ""),
                    ("status", "draft | submitted", ""), ("overall_comment, mean_score", "text, numeric", ""),
                    ("submitted_by, submitted_at", "uuid, ts", ""), ("reopen_count, reopen_reason", "int, text", ""),
                    ("(placement_id, type)", "", "UQ")],
    "evaluation_scores": [("evaluation_id", "uuid", "PK, FK"), ("criterion_id", "uuid", "PK, FK"),
                          ("score", "int 1–5", "")],
    "company_evaluations": [("placement_id", "uuid", "PK, FK"), ("four ratings", "int 1–5", ""),
                            ("would_recommend", "bool", ""), ("comment", "text", "")],
    "outcome_surveys": [("placement_id", "uuid", "PK, FK"), ("job_offer", "yes | no | pending", "")],
    # ---------------------------------------------------------------- grades and certificates
    "grades": [("id", "uuid", "PK"), ("placement_id", "uuid", "FK, UQ"), ("status", "draft | submitted | final", ""),
               ("total", "numeric", ""), ("submitted_by, approved_by", "uuid", "FK"),
               ("return_comment, reopen_reason", "text", "")],
    "grade_component_scores": [("grade_id", "uuid", "PK, FK"), ("component_id", "uuid", "PK, FK"),
                               ("score", "numeric 0–100", "")],
    "certificates": [("id", "uuid", "PK"), ("placement_id", "uuid", "FK"), ("code", "text (random)", "UQ"),
                     ("file_id", "uuid", "FK"), ("status", "valid | revoked", ""), ("issued_by, revoked_by", "uuid", "FK"),
                     ("revoke_reason", "text", "")],
    # ---------------------------------------------------------------- platform
    "files": [("id", "uuid", "PK"), ("storage_key", "text", "UQ"), ("original_name, mime_type", "text", ""),
              ("size_bytes, sha256", "int, char(64)", ""), ("purpose", "cv … verification … cert", ""),
              ("uploaded_by", "uuid", "FK")],
    "notifications": [("id", "uuid", "PK"), ("user_id", "uuid", "FK"), ("event, params, link", "text, jsonb", ""),
                      ("idempotency_key", "text", "UQ"), ("read_at", "ts", ""),
                      ("email_status, push_status", "pending … failed", "")],
    "audit_log": [("id", "bigint", "PK"), ("at", "ts", ""), ("user_id", "uuid", "FK"), ("role, action", "text", ""),
                  ("entity_type, entity_id", "text", ""), ("student_id", "uuid", ""),
                  ("college_id, company_id, cycle_id", "uuid", ""), ("old_value, new_value", "jsonb", ""),
                  ("reason", "text", "")],
    "job_runs": [("id", "bigint", "PK"), ("job_name", "text", ""), ("started_at, finished_at", "ts", ""),
                 ("status, items, error", "text, int", "")],
}

ONE, ZERO_ONE, MANY, ONE_MANY, ZERO_ONE_HEAD = "teetee", "teeodot", "crowodot", "crowtee", "teeodot"


def label(name, ref=False):
    head_bg = REF_EDGE if ref else NAVY
    rows = [f'<TR><TD COLSPAN="2" BGCOLOR="{head_bg}" ALIGN="CENTER"><FONT COLOR="{HEAD_TXT}" POINT-SIZE="11"><B>{name}</B></FONT></TD></TR>']
    cols = E[name] if not ref else [c for c in E[name] if "PK" in c[2]]
    for col, typ, key in cols:
        k = f'<FONT COLOR="{NAVY}"><B>{key}</B></FONT>' if key else " "
        colname = f"<U>{col}</U>" if "PK" in key else col
        if "vec" in typ:
            colname = f'<FONT COLOR="{AI}">{col} (vector)</FONT>'
        rows.append(f'<TR><TD ALIGN="LEFT">{k}</TD><TD ALIGN="LEFT">{colname}</TD></TR>')
    if ref:
        rows.append('<TR><TD COLSPAN="2" ALIGN="CENTER"><FONT POINT-SIZE="8" COLOR="#7F7F7F"><I>see other part</I></FONT></TD></TR>')
    bg = REF_FILL if ref else FILL
    return (f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="{REF_EDGE if ref else NAVY}" '
            f'BGCOLOR="{bg}">' + "".join(rows) + "</TABLE>>")


def build(name, entities, refs, rels, rankdir="LR", extra=""):
    lines = [f'digraph {name} {{',
             f'  graph [rankdir={rankdir}, fontname="Liberation Sans", nodesep=0.25, ranksep=0.55, pad=0.2, bgcolor="white", splines=spline];',
             '  node [shape=plain, fontname="Liberation Sans", fontsize=10];',
             '  edge [color="#44546A", arrowsize=0.9, penwidth=1.0, dir=both, fontname="Liberation Sans", fontsize=9, fontcolor="#333333"];']
    for e in entities:
        lines.append(f'  {e} [label={label(e)}];')
    for e in refs:
        lines.append(f'  {e} [label={label(e, ref=True)}];')
    for parent, child, tail, head, lab in rels:
        l = f', label=" {lab}"' if lab else ""
        lines.append(f'  {parent} -> {child} [arrowtail={tail}, arrowhead={head}{l}];')
    lines.append(extra)
    lines.append("}")
    return "\n".join(lines)


# Part 1 -- organizations, accounts, cycles, student profiles
part1 = build(
    "ERD1",
    ["universities", "colleges", "companies", "users", "student_profiles", "majors", "enrollments", "cvs",
     "cv_extracted_skills", "student_skills", "skills", "skill_resources", "training_cycles", "cycle_weeks",
     "grade_components", "rubric_criteria"],
    ["files", "verification_requests"],
    [("universities", "colleges", ONE, ONE_MANY, "has"),
     ("colleges", "users", ZERO_ONE, MANY, "members (ST, AS, CO)"),
     ("companies", "users", ZERO_ONE, MANY, "employs (CS)"),
     ("colleges", "training_cycles", ONE, MANY, "runs"),
     ("users", "student_profiles", ONE, ZERO_ONE_HEAD, ""),
     ("majors", "student_profiles", ONE, MANY, ""),
     ("student_profiles", "cvs", ONE, MANY, ""),
     ("files", "cvs", ONE, ZERO_ONE_HEAD, ""),
     ("cvs", "cv_extracted_skills", ONE, MANY, ""),
     ("skills", "cv_extracted_skills", ONE, MANY, ""),
     ("student_profiles", "student_skills", ONE, MANY, "confirms"),
     ("skills", "student_skills", ONE, MANY, ""),
     ("skills", "skill_resources", ONE, MANY, ""),
     ("student_profiles", "enrollments", ONE, MANY, ""),
     ("training_cycles", "enrollments", ONE, MANY, ""),
     ("verification_requests", "enrollments", ZERO_ONE, ZERO_ONE_HEAD, "creates"),
     ("training_cycles", "cycle_weeks", ONE, ONE_MANY, ""),
     ("training_cycles", "grade_components", ONE, ONE_MANY, ""),
     ("training_cycles", "rubric_criteria", ONE, ONE_MANY, ""),
     ],
    extra='  { rank=same; skills; training_cycles; }')

# Part 2 -- vacancies, matching, applications, placements
part2 = build(
    "ERD2",
    ["vacancies", "vacancy_skills", "vacancy_majors", "vacancy_universities", "applications", "placements",
     "match_scores"],
    ["companies", "users", "skills", "majors", "universities", "student_profiles", "training_cycles"],
    [("companies", "vacancies", ONE, MANY, "offers"),
     ("users", "vacancies", ONE, MANY, "responsible (CS)"),
     ("vacancies", "vacancy_skills", ONE, MANY, ""),
     ("skills", "vacancy_skills", ONE, MANY, ""),
     ("vacancies", "vacancy_majors", ONE, ONE_MANY, ""),
     ("majors", "vacancy_majors", ONE, MANY, ""),
     ("vacancies", "vacancy_universities", ONE, MANY, "targets (none = all)"),
     ("universities", "vacancy_universities", ONE, MANY, ""),
     ("vacancies", "applications", ONE, MANY, ""),
     ("student_profiles", "applications", ONE, MANY, "applies"),
     ("applications", "placements", ONE, ZERO_ONE_HEAD, "becomes"),
     ("training_cycles", "placements", ONE, MANY, "in cycle"),
     ("users", "placements", ONE, MANY, "supervises (CS, AS)"),
     ("student_profiles", "match_scores", ONE, MANY, ""),
     ("vacancies", "match_scores", ONE, MANY, ""),
     ])

# Part 3 -- reports, similarity, attendance, evaluations, grades, certificates
part3 = build(
    "ERD3",
    ["placements", "report_slots", "report_versions", "report_attachments", "report_reviews", "report_comments",
     "report_passages", "similarity_checks", "similarity_matches", "attendance_weeks", "evaluations",
     "evaluation_scores", "company_evaluations", "outcome_surveys", "grades", "grade_component_scores",
     "certificates"],
    ["users", "rubric_criteria", "grade_components", "files", "universities"],
    [("placements", "report_slots", ONE, ONE_MANY, "weekly + final"),
     ("report_slots", "report_versions", ONE, MANY, ""),
     ("report_versions", "report_attachments", ONE, MANY, ""),
     ("files", "report_attachments", ONE, MANY, ""),
     ("report_versions", "report_reviews", ONE, MANY, ""),
     ("report_slots", "report_comments", ONE, MANY, ""),
     ("users", "report_comments", ONE, MANY, "writes"),
     ("report_versions", "report_passages", ONE, MANY, ""),
     ("universities", "report_passages", ONE, MANY, "search scope"),
     ("report_versions", "similarity_checks", ONE, ZERO_ONE_HEAD, "checked"),
     ("similarity_checks", "similarity_matches", ONE, MANY, ""),
     ("report_versions", "similarity_matches", ONE, MANY, "source"),
     ("placements", "attendance_weeks", ONE, MANY, ""),
     ("placements", "evaluations", ONE, MANY, "periodic, final"),
     ("evaluations", "evaluation_scores", ONE, ONE_MANY, ""),
     ("rubric_criteria", "evaluation_scores", ONE, MANY, ""),
     ("placements", "grades", ONE, ONE, ""),
     ("grades", "grade_component_scores", ONE, ONE_MANY, ""),
     ("grade_components", "grade_component_scores", ONE, MANY, ""),
     ("placements", "certificates", ONE, MANY, "≤ 1 valid"),
     ("files", "certificates", ONE, ZERO_ONE_HEAD, ""),
     ("placements", "company_evaluations", ONE, ZERO_ONE_HEAD, ""),
     ("placements", "outcome_surveys", ONE, ZERO_ONE_HEAD, ""),
     ],
    extra='  { rank=same; rubric_criteria; grade_components; }')

# Part 4 -- verification and platform services
part4 = build(
    "ERD4",
    ["users", "verification_requests", "verification_documents", "account_tokens", "user_sessions",
     "push_subscriptions", "notifications", "audit_log", "files", "system_settings", "job_runs"],
    ["colleges", "companies", "training_cycles"],
    [("users", "verification_requests", ONE, MANY, "applies"),
     ("users", "verification_requests", ZERO_ONE, MANY, "reviews"),
     ("colleges", "verification_requests", ZERO_ONE, MANY, ""),
     ("companies", "verification_requests", ZERO_ONE, MANY, ""),
     ("training_cycles", "verification_requests", ZERO_ONE, MANY, "enrols in"),
     ("verification_requests", "verification_documents", ONE, ONE_MANY, ""),
     ("files", "verification_documents", ZERO_ONE, ZERO_ONE_HEAD, ""),
     ("users", "account_tokens", ONE, MANY, ""),
     ("users", "user_sessions", ONE, MANY, ""),
     ("users", "push_subscriptions", ONE, MANY, ""),
     ("users", "notifications", ONE, MANY, ""),
     ("users", "audit_log", ZERO_ONE, MANY, "acts"),
     ("users", "files", ZERO_ONE, MANY, "uploads"),
     ("users", "system_settings", ZERO_ONE, MANY, "updates (PA)"),
     ],
    extra='  { rank=same; job_runs; system_settings; }')

PARTS = (("06a_erd_organizations_profiles", part1), ("06b_erd_vacancies_placement", part2),
         ("06c_erd_training_grading", part3), ("06d_erd_platform", part4))

if __name__ == "__main__":
    for fname, src in PARTS:
        with open(f"{fname}.dot", "w", encoding="utf-8") as f:
            f.write(src)
    if shutil.which("dot"):
        for fname, _ in PARTS:
            subprocess.run(["dot", "-Tpng", "-Gdpi=250", f"{fname}.dot", "-o", f"../png/{fname}.png"], check=True)
            subprocess.run(["dot", "-Tsvg", f"{fname}.dot", "-o", f"../svg/{fname}.svg"], check=True)
        print("ok: .dot, PNG and SVG written")
    else:
        print("ok: .dot written; install Graphviz (`dot`) to render PNG and SVG")
