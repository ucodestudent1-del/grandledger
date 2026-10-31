"""Email service for sending transactional emails."""
from __future__ import annotations

import logging

from src.config import settings

logger = logging.getLogger("grandledger")


class EmailService:
    """Sends emails via SMTP or logs to console in dev mode."""

    def __init__(self) -> None:
        self.enabled = bool(settings.SMTP_HOST)

    def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> None:
        """Send an email. In dev/test mode, logs instead of sending."""
        if not self.enabled:
            logger.debug("Email (dev mode): to=%s subject=%s", to, subject)
            logger.debug("HTML: %s", html_content[:500])
            return

        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg.attach(MIMEText(text_content or html_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASS:
                    server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.sendmail(settings.SMTP_FROM, to, msg.as_string())
            logger.info("Email sent to %s: %s", to, subject)
        except Exception:
            logger.exception("Failed to send email to %s", to)

    def send_password_reset(self, to: str, reset_url: str, user_name: str) -> None:
        html = f"""
        <html>
        <body>
        <h2>Password Reset Request</h2>
        <p>Hello {user_name},</p>
        <p>You requested a password reset. Click the link below:</p>
        <p><a href="{reset_url}">Reset Your Password</a></p>
        <p>This link expires in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        text = f"Reset your password: {reset_url}\nThis link expires in 1 hour."
        self.send_email(to, "GrandLedger Password Reset", html, text)

    def send_verification_email(self, to: str, verify_url: str, user_name: str) -> None:
        html = f"""
        <html>
        <body>
        <h2>Verify Your Email</h2>
        <p>Hello {user_name},</p>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verify_url}">Verify Email</a></p>
        </body>
        </html>
        """
        text = f"Verify your email: {verify_url}"
        self.send_email(to, "GrandLedger Email Verification", html, text)

    def send_invitation(
        self,
        to: str,
        login_url: str,
        user_name: str,
        company_name: str,
        temp_password: str,
    ) -> None:
        html = f"""
        <html>
        <body>
        <h2>You've been invited to {company_name}</h2>
        <p>Hello {user_name},</p>
        <p>An administrator has invited you to join {company_name} on GrandLedger.</p>
        <p>Temporary password: <strong>{temp_password}</strong></p>
        <p><a href="{login_url}">Log In</a></p>
        </body>
        </html>
        """
        text = f"You've been invited to {company_name}. Login: {login_url}. Temp password: {temp_password}"
        self.send_email(to, f"Invitation to {company_name} on GrandLedger", html, text)


email_service = EmailService()
