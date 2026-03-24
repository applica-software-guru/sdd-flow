from app.config import settings
from app.services.email_templates import render_template
from app.services.mailer import send_email


async def send_tenant_invitation_email(
    *,
    recipient_email: str,
    tenant_name: str,
    inviter_name: str,
    role: str,
    token: str,
) -> None:
    accept_url = f"{settings.FRONTEND_URL.rstrip('/')}/invitations/{token}"

    context = {
        "title": "You are invited to collaborate",
        "cta_label": "Accept invitation",
        "cta_url": accept_url,
        "tenant_name": tenant_name,
        "inviter_name": inviter_name,
        "role": role,
        "accept_url": accept_url,
    }
    subject = render_template("emails/invitation_subject.txt", **context)
    text_body = render_template("emails/invitation_text.txt", **context)
    html_body = render_template("emails/invitation.html", **context)

    await send_email(
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        log_label="Invitation",
    )