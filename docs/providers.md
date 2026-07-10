# Провайдеры

## Общая идея

Провайдер отвечает за доставку уведомления в конкретный канал.

Сейчас в проекте реализован один канал:

- `email`

И один провайдер:

- `SMTPProvider`

## Базовый контракт

Все провайдеры следуют интерфейсу `NotificationProvider`.

Основной метод:

```python
async def send(
    recipient: str,
    template_code: str,
    payload: dict[str, Any],
) -> ProviderSendResult
```

На вход провайдер получает:

- `recipient`
- `template_code`
- `payload`

На выходе возвращает `ProviderSendResult`.

## ProviderSendResult

Сейчас результат содержит:

- `external_id`
- `metadata`

В текущей реализации это используется как технический результат доставки, но не вся информация пока сохраняется в БД.

## ProviderRegistry

`ProviderRegistry` отвечает за регистрацию и поиск провайдеров.

Что делает registry:

- регистрирует провайдер по `channel`
- назначает runtime `provider_id`
- умеет вернуть провайдер по `channel`
- умеет вернуть провайдер по `id`

Важно:

- `provider_id` сейчас runtime-идентификатор
- он удобен для процесса исполнения, но не должен восприниматься как стабильный бизнес-идентификатор между разными деплоями

## SMTPProvider

Находится в:

```text
app/providers/email/smtp.py
```

Что делает:

1. вызывает `TemplateManager`
2. получает `subject`, `body.html`, `body.txt`
3. собирает `EmailMessage`
4. отправляет письмо через `aiosmtplib`
5. возвращает `ProviderSendResult`

Основные настройки идут из:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_SENDER_EMAIL`
- `SMTP_SENDER_NAME`
- `SMTP_USE_TLS`
- `SMTP_START_TLS`

## Как добавить новый провайдер

1. Создать новый класс, наследующий `NotificationProvider`.
2. Реализовать `send(...)`.
3. Назначить `channel`.
4. Зарегистрировать провайдер в `ProviderRegistry`.
5. Добавить тесты:
   - success path
   - error path
   - корректный `ProviderSendResult`


## Связанные документы

- [README](../README.md)
- [Архитектура](architecture.md)
- [Шаблоны](templates.md)
