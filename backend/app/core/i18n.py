"""Error and email texts in Arabic and English (FR-LOC-02). User-entered content is never translated."""
from contextvars import ContextVar

SUPPORTED = ("ar", "en")
_lang: ContextVar[str] = ContextVar("lang", default="ar")


def set_language(lang: str | None) -> None:
    _lang.set(lang if lang in SUPPORTED else "ar")


def get_language() -> str:
    return _lang.get()


def language_from_header(value: str | None) -> str:
    if not value:
        return "ar"
    for part in value.split(","):
        code = part.split(";")[0].strip().lower()[:2]
        if code in SUPPORTED:
            return code
    return "ar"


# code -> (English, Arabic)
MESSAGES: dict[str, tuple[str, str]] = {
    "VALIDATION_ERROR": ("Some fields are not valid.", "بعض الحقول غير صحيحة."),
    "UNAUTHENTICATED": ("Please log in.", "يرجى تسجيل الدخول."),
    "SESSION_EXPIRED": ("Your session has ended. Please log in again.", "انتهت جلستك. يرجى تسجيل الدخول مجدداً."),
    "FORBIDDEN": ("You are not allowed to do this.", "لا تملك صلاحية تنفيذ هذا الإجراء."),
    "CONSENT_REQUIRED": ("Please read and accept the privacy notice first.", "يرجى قراءة إشعار الخصوصية والموافقة عليه أولاً."),
    "NOT_FOUND": ("Not found.", "غير موجود."),
    "INVALID_TRANSITION": ("This action is not allowed in the current state.", "هذا الإجراء غير مسموح في الحالة الحالية."),
    "CYCLE_CLOSED": ("The training cycle is closed.", "دورة التدريب مغلقة."),
    "RATE_LIMITED": ("Too many requests. Try again later.", "طلبات كثيرة. حاول لاحقاً."),
    "INVALID_CREDENTIALS": ("Wrong email or password.", "البريد أو كلمة المرور غير صحيحة."),
    "ACCOUNT_LOCKED": ("Login is locked for 15 minutes after 5 failed attempts.",
                       "أُوقف الدخول مؤقتاً لمدة 15 دقيقة بعد 5 محاولات خاطئة."),
    "ACCOUNT_INACTIVE": ("This account is deactivated.", "هذا الحساب موقوف."),
    "EMAIL_NOT_CONFIRMED": ("Confirm your email address first; check your inbox.",
                            "أكّد بريدك الإلكتروني أولاً؛ راجع صندوق الوارد."),
    "VERIFICATION_REQUIRED": ("Your account is not verified yet.", "حسابك لم يُوثَّق بعد."),
    "EMAIL_TAKEN": ("This email is already registered.", "هذا البريد مسجّل مسبقاً."),
    "COLLEGE_HAS_COORDINATOR": ("This college already has a coordinator. Contact the platform admin.",
                                "لهذه الكلية منسق بالفعل. تواصل مع مدير المنصة."),
    "DUPLICATE_COMMERCIAL_REG": ("A company with this commercial registration number is already registered.",
                                 "توجد شركة مسجّلة بهذا السجل التجاري."),
    "DOCUMENT_REQUIRED": ("A required document is missing.", "مستند مطلوب غير مرفق."),
    "GPA_ABOVE_SCALE": ("The GPA is above the university's scale.", "المعدل أعلى من سلم الجامعة."),
    "CYCLE_NOT_OPEN": ("The cycle is not open.", "الدورة ليست مفتوحة."),
    "COMPANY_NOT_VERIFIED": ("The company is not verified.", "الشركة غير موثّقة."),
    "TOKEN_INVALID": ("This link is not valid.", "هذا الرابط غير صالح."),
    "TOKEN_EXPIRED": ("This link has expired. Ask for a new one.", "انتهت صلاحية الرابط. اطلب رابطاً جديداً."),
    "TOKEN_USED": ("This link was already used.", "هذا الرابط استُخدم من قبل."),
    "WEAK_PASSWORD": ("The password needs at least 8 characters with letters and digits.",
                      "كلمة المرور تحتاج 8 أحرف على الأقل فيها حروف وأرقام."),
    "READ_ONLY_FIELD": ("This field cannot be changed after verification.", "لا يمكن تعديل هذا الحقل بعد التوثيق."),
    "WEIGHTS_NOT_100": ("The weights must total 100%.", "يجب أن يكون مجموع الأوزان 100%."),
    "GRADES_EXIST": ("Grades already exist for this cycle.", "توجد درجات مرسلة في هذه الدورة."),
    "RUBRIC_LOCKED": ("The rubric is read-only since the first evaluation.", "المعيار للقراءة فقط منذ أول تقييم."),
    "SCHEDULE_LOCKED": ("The schedule cannot change after the first placement.", "لا يمكن تغيير الجدول بعد أول توزيع."),
    "REASON_REQUIRED": ("A reason is required.", "السبب مطلوب."),
    "COMMENT_REQUIRED": ("A comment is required.", "التعليق مطلوب."),
    "TRANSFER_TARGET_INVALID": ("Choose an active member of the same college or company who has set a password.",
                                "اختر عضواً نشطاً من نفس الكلية أو الجهة أكمل تعيين كلمة المرور."),
    "SUPERVISOR_HAS_STUDENTS": ("This supervisor still has active students. Change their academic supervisor first.",
                                "لدى هذا المشرف طلاب نشطون. غيّر مشرفهم الأكاديمي أولاً."),
    "NOT_FLAGGED": ("A decision is recorded only for a flagged similarity check.",
                    "يُسجَّل القرار لفحص تشابه مُعلَّم فقط."),
    "FILE_TOO_LARGE": ("The file is too large.", "الملف أكبر من الحد المسموح."),
    "UNSUPPORTED_FILE_TYPE": ("This file type is not allowed.", "نوع الملف غير مسموح."),
    "TOO_MANY_ATTACHMENTS": ("At most 3 attachments are allowed.", "يُسمح بثلاثة مرفقات على الأكثر."),
    "MAIN_DOCUMENT_REQUIRED": ("The final report needs its main document.", "التقرير النهائي يحتاج مستنده الرئيسي."),
    "NOT_ELIGIBLE": ("You are not eligible for this vacancy.", "لا تنطبق عليك شروط هذه الفرصة."),
    "VACANCY_NOT_OPEN": ("The vacancy is not open.", "الفرصة غير مفتوحة."),
    "DEADLINE_PASSED": ("The application deadline has passed.", "انتهى موعد التقديم."),
    "DUPLICATE_APPLICATION": ("You already applied to this vacancy.", "قدّمت على هذه الفرصة من قبل."),
    "APPLICATION_LIMIT_REACHED": ("You have 5 active applications. Withdraw one before applying again.",
                                  "لديك 5 طلبات نشطة. اسحب طلباً قبل التقديم على فرصة أخرى."),
    "ALREADY_PLACED": ("The student already has a placement in this cycle.", "للطالب توزيع في هذه الدورة."),
    "NO_SEATS": ("The vacancy has no free seat.", "لا توجد مقاعد شاغرة في الفرصة."),
    "SLOT_CLOSED": ("This report was closed as missing.", "أُغلق هذا التقرير كغير مُسلَّم."),
    "NOTHING_TO_SUBMIT": ("There is no draft to submit.", "لا توجد مسودة لإرسالها."),
    "REQUIRED_FIELDS_MISSING": ("Fill in all report fields.", "املأ جميع حقول التقرير."),
    "DEADLINE_NOT_PASSED": ("The deadline has not passed yet.", "لم ينتهِ الموعد بعد."),
    "SEATS_BELOW_PLACEMENTS": ("Seats cannot be fewer than confirmed placements.", "لا يمكن أن تقل المقاعد عن التوزيعات المؤكدة."),
    "COMPANY_SUPERVISOR_INVALID": ("Choose an active supervisor of the vacancy's company.",
                                   "اختر مشرفاً نشطاً من شركة الفرصة."),
    "ACADEMIC_SUPERVISOR_INVALID": ("Choose an active academic supervisor of the student's college.",
                                    "اختر مشرفاً أكاديمياً نشطاً من كلية الطالب."),
    "STUDENT_NUMBER_TAKEN": ("This student number is already registered at the university.",
                             "هذا الرقم الجامعي مسجّل مسبقاً في الجامعة."),
    "DUPLICATE_NAME": ("This name already exists.", "هذا الاسم موجود مسبقاً."),
    "FILE_PURGED": ("This document was deleted after the retention period.", "حُذف هذا المستند بعد انتهاء مدة الاحتفاظ."),
    "INTERNAL_ERROR": ("Something went wrong. Please try again.", "حدث خطأ. حاول مجدداً."),
    "SKILLS_NOT_CONFIRMED": ("Confirm your skills first to see recommended vacancies.",
                             "أكّد مهاراتك أولاً لترى الفرص المقترحة."),
    "WEEK_NOT_STARTED": ("This week has not started yet.", "هذا الأسبوع لم يبدأ بعد."),
    "WEEK_LOCKED": ("This week is locked. Ask the coordinator to unlock it.",
                    "هذا الأسبوع مقفل. اطلب من المنسق فتحه."),
    "ATTENDED_EXCEEDS_SCHEDULED": ("Attended days cannot exceed the scheduled working days.",
                                   "لا يمكن أن تتجاوز أيام الحضور أيام العمل المجدولة."),
    "EVALUATION_INCOMPLETE": ("Rate every criterion and write the overall comment.",
                              "قيّم كل المعايير واكتب الملاحظة العامة."),
    "ALREADY_REOPENED": ("This evaluation was already reopened once.", "أُعيد فتح هذا التقييم مرة من قبل."),
    "PRECONDITIONS_UNMET": ("The grade cannot be submitted yet. Complete the items listed first.",
                            "لا يمكن إرسال الدرجة بعد. أكمل العناصر المذكورة أولاً."),
    "GRADE_LOCKED": ("This grade is locked. Only the coordinator can reopen it.",
                     "هذه الدرجة مقفلة. يعيد فتحها المنسق فقط."),
    "GRADE_NOT_FINAL": ("A certificate is issued only for a Final grade.", "تصدر الشهادة للدرجة المعتمدة فقط."),
    "CERTIFICATE_EXISTS": ("This placement already has a valid certificate. Revoke it first to issue a new one.",
                           "لهذا التدريب شهادة سارية. ألغها أولاً لإصدار شهادة جديدة."),
    "CERTIFICATE_REVOKED": ("This certificate is already revoked.", "هذه الشهادة ملغاة من قبل."),
    "FEEDBACK_NOT_OPEN": ("This opens when your training ends or your grade is final.",
                          "يُتاح هذا عند انتهاء تدريبك أو اعتماد درجتك."),
    "ALREADY_SUBMITTED": ("You already submitted this evaluation. It cannot be changed.",
                          "أرسلت هذا التقييم من قبل، ولا يمكن تعديله."),
    "CYCLE_NOT_CLOSED": ("Close the cycle first.", "أغلق الدورة أولاً."),
    "RETENTION_NOT_OVER": ("The retention period of this cycle has not ended yet.",
                           "لم تنتهِ مدة الاحتفاظ ببيانات هذه الدورة بعد."),
    "ALREADY_ANONYMIZED": ("This cycle was already anonymized.", "أُخفيت بيانات هذه الدورة من قبل."),
    "CONFIRM_REQUIRED": ("Confirm the action to continue.", "أكّد الإجراء للمتابعة."),
}


def message(code: str, lang: str | None = None) -> str:
    en, ar = MESSAGES.get(code, (code, code))
    return ar if (lang or get_language()) == "ar" else en
