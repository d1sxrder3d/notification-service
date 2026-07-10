from email.message import EmailMessage
from email.utils import formataddr
from typing import Any

import aiosmtplib

from core.config import settings
from core.logging_config import logger
from models.notification import NotificationChannel
from providers.base import NotificationProvider, ProviderSendResult
from providers.templates_manager import TemplateManager, template_manager


class SMTPProvider(NotificationProvider):
    def __init__(self, renderer: TemplateManager = template_manager):
        self.channel = NotificationChannel(settings.smtp.channel)
        self.host: str = settings.smtp.host
        self.port: int = settings.smtp.port
        self.username: str = settings.smtp.username
        self.password: str = settings.smtp.password
        self.sender_email: str = settings.smtp.sender_email
        self.sender_name: str = settings.smtp.sender_name
        self.use_tls: bool = settings.smtp.use_tls
        self.start_tls: bool = settings.smtp.start_tls
        self.renderer = renderer

    async def send(
        self,
        recipient: str,
        template_code: str,
        payload: dict[str, Any],
    ) -> ProviderSendResult:
        rendered = self.renderer.render(
            channel=self.channel,
            template_code=template_code,
            payload=payload,
        )

        message = EmailMessage()
        message["To"] = recipient
        message["From"] = formataddr((self.sender_name, self.sender_email))
        message["Subject"] = rendered.subject or template_code

        if rendered.text_body is not None:
            message.set_content(rendered.text_body)
        else:
            message.set_content("")

        if rendered.html_body is not None:
            message.add_alternative(rendered.html_body, subtype="html")

        smtp_response = await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls,
            start_tls=self.start_tls,
        )

        logger.info(
            "SMTP notification sent to {} using template {}",
            recipient,
            template_code,
        )

        return ProviderSendResult(
            metadata={
                "smtp_response": str(smtp_response),
                "template_code": template_code,
            },
        )
