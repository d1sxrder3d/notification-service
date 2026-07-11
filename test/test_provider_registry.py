import pytest

from models.notification import NotificationChannel
from providers.registry import ProviderNotConfiguredError, ProviderRegistry


class StubProvider:
    def __init__(self, channel: NotificationChannel, code: str):
        self.channel = channel
        self.code = code
        self.id = None

    async def send(self, recipient, template_code, payload):
        raise NotImplementedError


def test_registry_assigns_incrementing_provider_ids_and_indexes_by_code():
    email_provider = StubProvider(NotificationChannel.EMAIL, "smtp_primary")
    telegram_provider = StubProvider(NotificationChannel.TELEGRAM, "telegram_primary")

    registry = ProviderRegistry(providers=(email_provider, telegram_provider))

    assert email_provider.id == 1
    assert telegram_provider.id == 2
    assert registry.get_by_id(1) is email_provider
    assert registry.get_by_id(2) is telegram_provider
    assert registry.get_by_code("smtp_primary") is email_provider
    assert registry.get_by_code("telegram_primary") is telegram_provider


def test_registry_reassigns_id_when_channel_provider_is_replaced():
    registry = ProviderRegistry()
    first_provider = StubProvider(NotificationChannel.EMAIL, "smtp_primary")
    second_provider = StubProvider(NotificationChannel.EMAIL, "smtp_backup")

    registry.register(first_provider)
    registry.register(second_provider)

    assert first_provider.id == 1
    assert second_provider.id == 2
    assert registry.get(NotificationChannel.EMAIL) is second_provider
    assert registry.get_by_id(2) is second_provider
    with pytest.raises(ProviderNotConfiguredError):
        registry.get_by_code("smtp_primary")
    assert registry.get_by_code("smtp_backup") is second_provider


def test_registry_rejects_duplicate_provider_codes():
    registry = ProviderRegistry()
    first_provider = StubProvider(NotificationChannel.EMAIL, "smtp_primary")
    second_provider = StubProvider(NotificationChannel.TELEGRAM, "smtp_primary")

    registry.register(first_provider)

    with pytest.raises(ValueError, match="smtp_primary"):
        registry.register(second_provider)
