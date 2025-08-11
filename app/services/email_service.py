"""Simple SMTP email service for sending OTP and notifications."""

import smtplib
from email.message import EmailMessage
from typing import Optional

from app.config.settings import settings
from app.config.logger import Logger

logger = Logger.get_logger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.use_tls = settings.smtp_use_tls
        self.use_ssl = settings.smtp_use_ssl
        self.mail_from = settings.mail_from
        self.mail_from_name = settings.mail_from_name

    def _connect(self):
        if self.use_ssl:
            server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            server = smtplib.SMTP(self.host, self.port)
        server.ehlo()
        if self.use_tls and not self.use_ssl:
            server.starttls()
        if self.username and self.password:
            server.login(self.username, self.password)
        return server

    def send_email(self, to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        msg = EmailMessage()
        frm = f"{self.mail_from_name} <{self.mail_from}>" if self.mail_from_name else self.mail_from
        msg["From"] = frm
        msg["To"] = to_email
        msg["Subject"] = subject
        if html:
            msg.set_content(body)
            msg.add_alternative(html, subtype="html")
        else:
            msg.set_content(body)

        try:
            with self._connect() as server:
                server.send_message(msg)
            logger.info(f"Sent email to {to_email} with subject '{subject}'")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False


email_service = EmailService()
