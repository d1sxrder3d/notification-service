import smtplib
from typing import Any

from core.config import settings
from providers.base import NotificationProvider, ProviderSendResult
from core.logging_config import logger

class STMPProvider(NotificationProvider):
    def __init__(self):
        self.channel: str = settings.smtp.channel
        self.host: str = settings.smtp.host
        self.port: int = settings.smtp.port
        self.address: str = settings.smtp.address
        self.password: str = settings.smtp.password

    async def send(
            self,
            recipient: str,
            template_code: str,
            payload: dict[str, Any],
    ) -> ProviderSendResult:
        try:
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.address, self.password)

                server.sendmail(
                    self.address,
                    recipient,
                    str(payload)
                )

                logger.info(f"Email sent to {recipient}")

                return ProviderSendResult(external_id=recipient, metadata=payload) #TODO: переписать
        except Exception as e:
            logger.error(e)
