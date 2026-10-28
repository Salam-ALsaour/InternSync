"""Account emails in the recipient's language (FR-AUT-02, FR-AUT-04, FR-LOC-02).

Confirmation, invitation, and reset emails are sent directly after the commit; event notifications go through the
outbox of app.notifications (Increment 3). Locally every email lands in Mailpit (http://localhost:8025)."""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

log = logging.getLogger("internsync.mail")
outbox: list[dict] = []  # used by MAIL_BACKEND=memory (tests)

TEMPLATES = {
    "email_confirmation": {
        "en": ("Confirm your InternSync email",
               "Hello {name},\n\nConfirm your email address by opening this link (valid {hours} hours):\n{link}\n\n"
               "After that, the responsible person reviews your documents.\n\nInternSync"),
        "ar": ("تأكيد بريدك في InternSync",
               "مرحباً {name}،\n\nأكّد بريدك الإلكتروني بفتح الرابط التالي (صالح {hours} ساعة):\n{link}\n\n"
               "بعدها تراجع الجهة المسؤولة مستنداتك.\n\nInternSync"),
    },
    "invitation": {
        "en": ("You are invited to InternSync",
               "Hello {name},\n\n{inviter} invited you to InternSync as {role} of {org}.\n"
               "Set your password with this link (valid {hours} hours):\n{link}\n\nInternSync"),
        "ar": ("دعوة للانضمام إلى InternSync",
               "مرحباً {name}،\n\nدعاك {inviter} للانضمام إلى InternSync بصفة {role} في {org}.\n"
               "عيّن كلمة المرور من الرابط التالي (صالح {hours} ساعة):\n{link}\n\nInternSync"),
    },
    "password_reset": {
        "en": ("Reset your InternSync password",
               "Hello {name},\n\nSet a new password with this link (valid {minutes} minutes):\n{link}\n\n"
               "If you did not ask for this, ignore this email.\n\nInternSync"),
        "ar": ("إعادة تعيين كلمة المرور في InternSync",
               "مرحباً {name}،\n\nعيّن كلمة مرور جديدة من الرابط التالي (صالح {minutes} دقيقة):\n{link}\n\n"
               "إن لم تطلب ذلك فتجاهل هذه الرسالة.\n\nInternSync"),
    },
}

ROLE_NAMES = {
    "academic_supervisor": {"en": "academic supervisor", "ar": "مشرف أكاديمي"},
    "company_supervisor": {"en": "company supervisor", "ar": "مشرف جهة تدريب"},
}


def send(template: str, to: str, lang: str, **params) -> None:
    """An account email (confirmation, invitation, reset), sent at once because the user is waiting for it."""
    subject, body = TEMPLATES[template]["ar" if lang == "ar" else "en"]
    deliver(to, subject, body.format(**params), template=template, link=params.get("link"))


def deliver(to: str, subject: str, body: str, *, template: str = "notification", link: str | None = None) -> bool:
    """Send one email; True when it was handed to the mail server (the notification outbox retries otherwise)."""
    settings = get_settings()
    message = {"to": to, "subject": subject, "body": body, "template": template, "link": link}
    if settings.mail_backend == "memory":
        outbox.append(message)
        return True
    if settings.mail_backend == "console":
        log.info("email to %s: %s\n%s", to, subject, body)
        return True
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.mail_from, to, subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException):
        # The change is already saved: account emails can be asked for again, notifications are retried.
        log.exception("email to %s failed", to)
        return False
