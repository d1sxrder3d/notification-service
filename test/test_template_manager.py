from pathlib import Path

import pytest

from models.notification import NotificationChannel
from providers.templates_manager import TemplateManager, TemplateRenderingError


@pytest.fixture
def template_manager(templates_dir: Path):
    return TemplateManager(templates_dir=templates_dir)


def test_render_welcome_template_successfully(template_manager: TemplateManager):
    rendered = template_manager.render(
        channel=NotificationChannel.EMAIL,
        template_code="welcome",
        payload={"name": "Alex"},
    )

    assert rendered.subject == "Welcome, Alex!"
    assert "Hello, Alex" in rendered.html_body
    assert "Hello, Alex" in rendered.text_body


@pytest.mark.parametrize(
    ("template_code", "payload", "expected_subject_fragment", "expected_body_fragment"),
    [
        (
            "password_reset",
            {
                "name": "Alex",
                "reset_url": "https://example.com/reset",
                "expires_in_minutes": 30,
            },
            "Reset your password, Alex",
            "https://example.com/reset",
        ),
        (
            "email_verification",
            {
                "name": "Alex",
                "verification_url": "https://example.com/verify",
            },
            "Verify your email, Alex",
            "https://example.com/verify",
        ),
        (
            "generic_alert",
            {
                "name": "Alex",
                "alert_title": "Security alert",
                "alert_message": "A new login was detected.",
                "action_url": "https://example.com/activity",
            },
            "Security alert",
            "A new login was detected.",
        ),
    ],
)
def test_render_example_templates(
    template_manager: TemplateManager,
    template_code: str,
    payload: dict,
    expected_subject_fragment: str,
    expected_body_fragment: str,
):
    rendered = template_manager.render(
        channel=NotificationChannel.EMAIL,
        template_code=template_code,
        payload=payload,
    )

    assert expected_subject_fragment in rendered.subject
    assert expected_body_fragment in rendered.html_body
    assert expected_body_fragment in rendered.text_body


def test_render_template_fails_for_missing_payload_field(template_manager: TemplateManager):
    with pytest.raises(TemplateRenderingError):
        template_manager.render(
            channel=NotificationChannel.EMAIL,
            template_code="welcome",
            payload={},
        )


def test_render_template_fails_for_unknown_template(template_manager: TemplateManager):
    with pytest.raises(TemplateRenderingError):
        template_manager.render(
            channel=NotificationChannel.EMAIL,
            template_code="does_not_exist",
            payload={"name": "Alex"},
        )
