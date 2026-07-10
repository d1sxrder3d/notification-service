# Тестирование

## Подход

В проекте используется `unit-first` стратегия.

Основная идея:

- максимум бизнес-логики закрывается unit-тестами
- внешние зависимости мокируются
- integration-тесты добавляются только там, где они реально проверяют важный стык

## Что покрыто

Сейчас покрыты:

- `TemplateManager`
- `ProviderRegistry`
- `SMTPProvider`
- `NotificationService`
- `Celery` task отправки
- API endpoints

Отдельно есть узкий smoke-test на `SQLite`.

## Структура тестов

Тесты находятся в директории:

```text
test/
```

Основные файлы:

- `test_smtp_provider.py`
- `test_notification_service.py`
- `test_send_notification_task.py`
- `test_notification_api.py`
- `test_notification_service_sqlite.py`
- `conftest.py`

## Что является unit-тестом

Unit-тестами считаются проверки:

- рендера шаблонов
- логики registry
- отправки через provider с мокнутым `aiosmtplib`
- логики сервиса с мокнутыми сессиями и `Celery.delay`
- обработки ошибок в `Celery` task
- API с dependency overrides

## Что является integration smoke-test

Сейчас это узкий тест на `SQLite`, который проверяет:

- создание уведомления
- `idempotency`
- базовый стык `SQLAlchemy + NotificationService`

Он не заменяет unit-тесты и не должен разрастаться без необходимости.

## Запуск тестов

Из корня проекта:

```powershell
$env:PYTHONPATH='app'; .\.venv\Scripts\python -m pytest test
```

Или точечно:

```powershell
$env:PYTHONPATH='app'; .\.venv\Scripts\python -m pytest test\test_notification_api.py
```

## Что стоит тестировать при новых изменениях

Если добавляется новый provider:

- success path
- transport error path
- корректный возврат `ProviderSendResult`

Если добавляется новый шаблон:

- успешный рендер
- ошибка при неполном `payload`

Если меняется модель уведомления:

- переходы статусов
- retry behavior
- `failure_reason`
- `idempotency`

## Что сейчас не тестируется

- реальные SMTP-соединения
- реальный `Celery` worker как внешний процесс
- реальный `RabbitMQ` в тестовом окружении
- файловые логи

Это сделано осознанно, чтобы suite оставался быстрым и воспроизводимым.

## Связанные документы

- [README](../README.md)
- [Архитектура](architecture.md)
