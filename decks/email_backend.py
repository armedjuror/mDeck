import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendEmailBackend(BaseEmailBackend):
    """Django email backend that sends via the Resend API."""

    def send_messages(self, email_messages):
        resend.api_key = settings.RESEND_API_KEY
        sent = 0
        for msg in email_messages:
            try:
                params = {
                    "from": msg.from_email or settings.DEFAULT_FROM_EMAIL,
                    "to": list(msg.to),
                    "subject": msg.subject,
                    "text": msg.body,
                }
                # Attach HTML alternative if present (allauth sends both)
                if hasattr(msg, "alternatives"):
                    for content, mimetype in msg.alternatives:
                        if mimetype == "text/html":
                            params["html"] = content
                            break
                resend.Emails.send(params)
                sent += 1
            except Exception as exc:
                if not self.fail_silently:
                    raise exc
        return sent
