from collections.abc import Iterable

from app.models.notification import NotificationChannel
from app.providers.base import NotificationProvider


class ProviderNotConfiguredError(Exception):
    pass


class ProviderRegistry:
    def __init__(self, providers: Iterable[NotificationProvider] = ()):
        self._providers: dict[NotificationChannel, NotificationProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: NotificationProvider) -> None:
        self._providers[provider.channel] = provider

    def get(self, channel: NotificationChannel) -> NotificationProvider:
        provider = self._providers.get(channel)
        if provider is None:
            raise ProviderNotConfiguredError(
                f"Provider for channel '{channel.value}' is not configured",
            )
        return provider
