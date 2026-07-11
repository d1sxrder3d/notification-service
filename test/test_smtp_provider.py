from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from providers.base import ProviderSendResult
from providers.email.smtp import SMTPProvider


class StubRenderer:
    def __init__(self, rendered_template):
        self.rendered_template = rendered_template
        self.calls = []

    def render(self, channel, template_code, payload):
        self.calls.append(
            {
                "channel": channel,
                "template_code": template_code,
                "payload": payload,
            },
        )
        return self.rendered_template


@pytest.mark.anyio
async def test_smtp_provider_sends_multipart_email(monkeypatch):
    renderer = StubRenderer(
        SimpleNamespace(
            subject="Welcome, Alex!",
            text_body="Hello, Alex",
            html_body="<h1>Hello, Alex</h1>",
        ),
    )
    send_mock = AsyncMock(return_value={"accepted_recipients": ["user@example.com"]})
    monkeypatch.setattr("providers.email.smtp.aiosmtplib.send", send_mock)

    provider = SMTPProvider(renderer=renderer)
    assert provider.code == "smtp_primary"

    result = await provider.send(
        recipient="user@example.com",
        template_code="welcome",
        payload={"name": "Alex"},
    )

    assert isinstance(result, ProviderSendResult)
    assert renderer.calls[0]["template_code"] == "welcome"

    message = send_mock.await_args.args[0]
    assert message["To"] == "user@example.com"
    assert message["Subject"] == "Welcome, Alex!"
    assert message.is_multipart()
    assert "Hello, Alex" in message.as_string()

    assert send_mock.await_args.kwargs["hostname"] == provider.host
    assert send_mock.await_args.kwargs["username"] == provider.username
    assert result.metadata["template_code"] == "welcome"


@pytest.mark.anyio
async def test_smtp_provider_uses_template_code_as_subject_fallback(monkeypatch):
    renderer = StubRenderer(
        SimpleNamespace(
            subject=None,
            text_body="Body only",
            html_body=None,
        ),
    )
    send_mock = AsyncMock(return_value="queued")
    monkeypatch.setattr("providers.email.smtp.aiosmtplib.send", send_mock)

    provider = SMTPProvider(renderer=renderer)

    await provider.send(
        recipient="user@example.com",
        template_code="password_reset",
        payload={"name": "Alex"},
    )

    message = send_mock.await_args.args[0]
    assert message["Subject"] == "password_reset"
    assert not message.is_multipart()
    assert "Body only" in message.as_string()


@pytest.mark.anyio
async def test_smtp_provider_propagates_smtp_errors(monkeypatch):
    renderer = StubRenderer(
        SimpleNamespace(
            subject="Subject",
            text_body="Body",
            html_body=None,
        ),
    )
    send_mock = AsyncMock(side_effect=RuntimeError("smtp down"))
    monkeypatch.setattr("providers.email.smtp.aiosmtplib.send", send_mock)

    provider = SMTPProvider(renderer=renderer)

    with pytest.raises(RuntimeError, match="smtp down"):
        await provider.send(
            recipient="user@example.com",
            template_code="welcome",
            payload={"name": "Alex"},
        )
