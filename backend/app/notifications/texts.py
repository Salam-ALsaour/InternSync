"""The words of each notification in Arabic and English (FR-NOT-06; Design Table 5.6).

A text is chosen by the event, or by `event.variant` when the params carry a `variant`. Params ending in `_en` or `_ar`
fill the placeholder without the suffix in that language, so one stored row reads well in both."""
from collections import defaultdict

TEXTS: dict[str, dict[str, tuple[str, str]]] = {
    "verification.submitted": {
        "en": ("New verification request", "{name} sent a verification request ({kind}). Review the documents."),
        "ar": ("طلب تحقق جديد", "أرسل {name} طلب تحقق ({kind}). راجع المستندات."),
    },
    "verification.approved": {
        "en": ("Your account is verified", "Your verification request was approved. You can now use every page of "
                                           "your role."),
        "ar": ("تم التحقق من حسابك", "تمت الموافقة على طلب التحقق. يمكنك الآن استخدام كل صفحات دورك."),
    },
    "verification.rejected": {
        "en": ("Verification request rejected", "Your verification request was rejected: {reason}. You can correct "
                                                "it and send it again."),
        "ar": ("رُفض طلب التحقق", "رُفض طلب التحقق: {reason}. يمكنك تصحيحه وإرساله من جديد."),
    },
    "role.transferred.received": {
        "en": ("You are now {role}", "The Platform Admin made you {role} of {org}. Reason: {reason}"),
        "ar": ("أصبحت {role}", "عيّنك مشرف المنصة {role} في {org}. السبب: {reason}"),
    },
    "role.transferred.removed": {
        "en": ("Your role changed", "You are no longer {role} of {org}; {new_holder} took over. Reason: {reason}"),
        "ar": ("تغيّر دورك", "لم تعد {role} في {org}؛ انتقل الدور إلى {new_holder}. السبب: {reason}"),
    },
    "application.received": {
        "en": ("New applicant", "{student} applied to {vacancy}."),
        "ar": ("متقدم جديد", "تقدّم {student} إلى {vacancy}."),
    },
    "application.accepted": {
        "en": ("Placement to confirm", "{company} accepted {student} for {vacancy}. Confirm the placement."),
        "ar": ("توزيع بانتظار الاعتماد", "قبلت {company} الطالب {student} في {vacancy}. اعتمد التوزيع."),
    },
    "application.decided.accepted": {
        "en": ("Application accepted", "{company} accepted your application to {vacancy}. Your coordinator "
                                       "confirms the placement next."),
        "ar": ("قُبل طلبك", "قبلت {company} طلبك في {vacancy}. يعتمد منسق التدريب التوزيع بعد ذلك."),
    },
    "application.decided.declined": {
        "en": ("Application declined", "{company} declined your application to {vacancy}."),
        "ar": ("لم يُقبل طلبك", "اعتذرت {company} عن طلبك في {vacancy}."),
    },
    "application.withdrawn_auto": {
        "en": ("Application withdrawn", "Your application to {vacancy} was withdrawn because {why}."),
        "ar": ("سُحب طلبك", "سُحب طلبك في {vacancy} لأن {why}."),
    },
    "placement.confirmed": {
        "en": ("Placement confirmed", "{student} is placed at {company} ({vacancy})."),
        "ar": ("اعتُمد التوزيع", "وُزّع {student} على {company} ({vacancy})."),
    },
    "placement.cancelled": {
        "en": ("Placement cancelled", "The placement of {student} at {company} was cancelled: {reason}"),
        "ar": ("أُلغي التوزيع", "أُلغي توزيع {student} على {company}: {reason}"),
    },
    "placement.supervisor_changed": {
        "en": ("Academic supervisor changed", "{supervisor} is now the academic supervisor of {student}."),
        "ar": ("تغيّر المشرف الأكاديمي", "أصبح {supervisor} المشرف الأكاديمي للطالب {student}."),
    },
    "report.reminder": {
        "en": ("Report due soon", "Your {report} is due on {due}."),
        "ar": ("موعد تقرير قريب", "موعد تسليم {report} هو {due}."),
    },
    "report.submitted": {
        "en": ("Report to review", "{student} submitted the {report}."),
        "ar": ("تقرير للمراجعة", "سلّم {student} {report}."),
    },
    "report.revision_requested": {
        "en": ("Revision requested", "Your supervisor asked for changes to your {report}: {comment}"),
        "ar": ("طُلب تعديل", "طلب مشرفك تعديل {report}: {comment}"),
    },
    "report.accepted": {
        "en": ("Report accepted", "Your {report} was accepted."),
        "ar": ("قُبل التقرير", "قُبل {report}."),
    },
    "report.missing": {
        "en": ("Report missing", "The {report} of {student} was not submitted by its deadline ({due})."),
        "ar": ("تقرير لم يُسلَّم", "لم يُسلَّم {report} للطالب {student} في موعده ({due})."),
    },
    "evaluation.submitted": {
        "en": ("Evaluation submitted", "{company} submitted the {evaluation} of {student}."),
        "ar": ("أُرسل التقييم", "أرسلت {company} {evaluation} للطالب {student}."),
    },
    "grade.submitted": {
        "en": ("Grade to approve", "The grade of {student} was submitted for approval."),
        "ar": ("درجة للاعتماد", "أُرسلت درجة {student} للاعتماد."),
    },
    "grade.returned": {
        "en": ("Grade returned", "The coordinator returned the grade of {student}: {comment}"),
        "ar": ("أُعيدت الدرجة", "أعاد المنسق درجة {student}: {comment}"),
    },
    "grade.final": {
        "en": ("Grade final", "The grade of {student} is final."),
        "ar": ("اعتُمدت الدرجة", "اعتُمدت درجة {student} نهائياً."),
    },
    "certificate.issued": {
        "en": ("Certificate issued", "Your completion certificate for the training at {company} is ready."),
        "ar": ("صدرت الشهادة", "شهادة إتمام تدريبك لدى {company} جاهزة."),
    },
    "certificate.revoked": {
        "en": ("Certificate revoked", "Your completion certificate was revoked: {reason}"),
        "ar": ("أُلغيت الشهادة", "أُلغيت شهادة إتمام تدريبك: {reason}"),
    },
    "grade.reopened": {
        "en": ("Grade reopened", "The grade of {student} was reopened for correction: {reason}"),
        "ar": ("أُعيد فتح الدرجة", "أُعيد فتح درجة {student} للتصحيح: {reason}"),
    },
    "escalation.overdue": {
        "en": ("Overdue for {days} days", "{item} of {student} is still outstanding {days} days after its "
                                          "deadline."),
        "ar": ("متأخر منذ {days} أيام", "{item} للطالب {student} ما زال معلقاً بعد {days} أيام من موعده."),
    },
}

GREETING = {"en": "Hello {name},", "ar": "مرحباً {name}،"}
OPEN = {"en": "Open InternSync", "ar": "افتح InternSync"}


def localize(params: dict, lang: str) -> dict:
    out = defaultdict(str)
    for key, value in params.items():
        out[key] = value
    for key, value in params.items():
        if key.endswith(f"_{lang}"):
            out[key[: -len(lang) - 1]] = value
    return out


def render(event: str, params: dict, lang: str) -> tuple[str, str]:
    """(title, body) of one notification in `lang`."""
    lang = "ar" if lang == "ar" else "en"
    variant = params.get("variant")
    texts = TEXTS.get(f"{event}.{variant}") if variant else None
    title, body = (texts or TEXTS[event])[lang]
    values = localize(params, lang)
    return title.format_map(values), body.format_map(values)


def report_label(week_no: int | None) -> dict:
    """Params for {report}: "week 3 report" or "final report" in both languages."""
    if week_no is None:
        return {"report_en": "final report", "report_ar": "التقرير النهائي"}
    return {"report_en": f"week {week_no} report", "report_ar": f"تقرير الأسبوع {week_no}"}


def names(prefix: str, name_en: str | None, name_ar: str | None) -> dict:
    return {f"{prefix}_en": name_en or name_ar or "", f"{prefix}_ar": name_ar or name_en or ""}
