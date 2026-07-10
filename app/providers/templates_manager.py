from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound, select_autoescape

from core.config import settings
from models.notification import NotificationChannel


class TemplateRenderingError(Exception):
    pass


@dataclass(slots=True, frozen=True)
class RenderedTemplate:
    subject: str | None = None
    html_body: str | None = None
    text_body: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TemplateManager:
    def __init__(self, templates_dir: Path | None = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        self.environment = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        channel: NotificationChannel,
        template_code: str,
        payload: dict[str, Any],
    ) -> RenderedTemplate:
        template_dir = f"{channel.value}/{template_code}"

        try:
            subject = self._render_optional_template(
                f"{template_dir}/subject.txt",
                payload,
            )
            html_body = self._render_optional_template(
                f"{template_dir}/body.html",
                payload,
            )
            text_body = self._render_optional_template(
                f"{template_dir}/body.txt",
                payload,
            )
        except TemplateNotFound as exc:
            raise TemplateRenderingError(
                f"Template '{template_code}' for channel '{channel.value}' was not found",
            ) from exc
        except Exception as exc:
            raise TemplateRenderingError(
                f"Failed to render template '{template_code}' for channel '{channel.value}'",
            ) from exc

        if subject is None and html_body is None and text_body is None:
            raise TemplateRenderingError(
                f"Template '{template_code}' for channel '{channel.value}' is empty",
            )

        return RenderedTemplate(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

    def _render_optional_template(
        self,
        template_name: str,
        payload: dict[str, Any],
    ) -> str | None:
        try:
            template = self.environment.get_template(template_name)
        except TemplateNotFound:
            return None

        rendered = template.render(**payload).strip()
        return rendered or None


template_manager = TemplateManager()
