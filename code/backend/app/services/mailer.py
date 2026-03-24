from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

import httpx

from app.config import settings


def build_email_message(*, recipient_email: str, subject: str, text_body: str, html_body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_EMAIL}>"
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    return message


def _send_via_smtp(message: EmailMessage) -> None:
    with smtplib.SMTP(settings.MAIL_SMTP_HOST, settings.MAIL_SMTP_PORT, timeout=10) as smtp:
        if settings.MAIL_SMTP_USE_TLS:
            smtp.starttls()
        if settings.MAIL_SMTP_USERNAME:
            smtp.login(settings.MAIL_SMTP_USERNAME, settings.MAIL_SMTP_PASSWORD)
        smtp.send_message(message)


async def _send_via_brevo(
    *,
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> None:
    if not settings.BREVO_API_KEY:
        raise RuntimeError("BREVO_API_KEY is required when MAIL_PROVIDER is set to 'brevo'")

    payload = {
        "sender": {
            "email": settings.MAIL_FROM_EMAIL,
            "name": settings.MAIL_FROM_NAME,
        },
        "to": [{"email": recipient_email}],
        "subject": subject,
        "textContent": text_body,
        "htmlContent": html_body,
    }

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers)
        response.raise_for_status()


async def send_email(*, recipient_email: str, subject: str, text_body: str, html_body: str, log_label: str) -> None:
    message = build_email_message(
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )

    if settings.MAIL_PROVIDER == "log":
        print(
            f"{log_label} email (log mode): "
            f"to={recipient_email} subject={subject}"
        )
        return

    if settings.MAIL_PROVIDER == "brevo":
        await _send_via_brevo(
            recipient_email=recipient_email,
            subject=str(message["Subject"]),
            text_body=message.get_body(preferencelist=("plain",)).get_content(),
            html_body=message.get_body(preferencelist=("html",)).get_content(),
        )
        return

    await asyncio.to_thread(_send_via_smtp, message)
