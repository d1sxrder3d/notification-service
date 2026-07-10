from collections.abc import Iterable

from models.notification import NotificationChannel
from providers.base import NotificationProvider
from providers.email.smtp import SMTPProvider


class ProviderNotConfiguredError(Exception):
    pass


class ProviderRegistry:
    def __init__(self, providers: Iterable[NotificationProvider] = ()):
        self._providers: dict[NotificationChannel, NotificationProvider] = {}
        self._providers_by_id: dict[int, NotificationProvider] = {}
        self._providers_by_code: dict[str, NotificationProvider] = {}
        self._next_provider_id = 1
        for provider in providers:
            self.register(provider)

    def register(self, provider: NotificationProvider) -> None:
        existing_provider_by_code = self._providers_by_code.get(provider.code)
        if existing_provider_by_code is not None and existing_provider_by_code is not provider:
            raise ValueError(
                f"Provider with code '{provider.code}' is already registered",
            )

        existing_provider = self._providers.get(provider.channel)
        if existing_provider is not None and existing_provider.id is not None:
            self._providers_by_id.pop(existing_provider.id, None)
            if existing_provider.code != provider.code:
                self._providers_by_code.pop(existing_provider.code, None)

        provider.id = self._next_provider_id
        self._next_provider_id += 1

        self._providers[provider.channel] = provider
        self._providers_by_id[provider.id] = provider
        self._providers_by_code[provider.code] = provider

    def get(self, channel: NotificationChannel) -> NotificationProvider:
        provider = self._providers.get(channel)
        if provider is None:
            raise ProviderNotConfiguredError(
                f"Provider for channel '{channel.value}' is not configured",
            )
        return provider

    def get_by_id(self, provider_id: int) -> NotificationProvider:
        provider = self._providers_by_id.get(provider_id)
        if provider is None:
            raise ProviderNotConfiguredError(
                f"Provider with id '{provider_id}' is not configured",
            )
        return provider

    def get_by_code(self, provider_code: str) -> NotificationProvider:
        provider = self._providers_by_code.get(provider_code)
        if provider is None:
            raise ProviderNotConfiguredError(
                f"Provider with code '{provider_code}' is not configured",
            )
        return provider


provider_registry = ProviderRegistry(
    providers=(
        SMTPProvider(),
    ),
)
