# Конфигурация

## Общий принцип

Конфигурация приложения строится через `pydantic-settings` и читается из `.env`.

Шаблон для локального запуска:

- [`.env.example`](../.env.example)

Основные группы переменных:

- `APP_*`
- `DB_*`
- `CELERY_*`
- `RMQ_*`
- `SMTP_*`
- `METRICS_*`
- `GRAFANA_*`

## APP

### `APP_NAME`

Отображаемое имя сервиса.

### `APP_DEBUG`

Включает debug-режим FastAPI и более подробное логирование.

### `APP_HOST`

Хост, на котором поднимается API.

### `APP_PORT`

Порт API.

### `LOG_LEVEL`

Уровень логирования:

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

### `NOTIFICATION_MAX_ATTEMPTS`

Максимальное количество попыток отправки уведомления.

## Database

### `DB_TYPE`

Поддерживаемые значения:

- `sqlite`
- `postgres`

Для `docker-compose` используется `postgres`.

### `DB_SQLITE_PATH`

Путь до SQLite-файла. Используется только при `DB_TYPE=sqlite`.

### `DB_HOST`

Хост PostgreSQL.

### `DB_PORT`

Порт PostgreSQL.

### `DB_NAME`

Имя базы данных.

### `DB_USER`

Пользователь базы данных.

### `DB_PASSWORD`

Пароль базы данных.

### `DB_ECHO`

Включает SQLAlchemy SQL echo.

### `DB_POOL_PRE_PING`

Проверка соединений в пуле перед использованием.

## Celery / Redis

### `CELERY_BROKER_HOST`
### `CELERY_BROKER_PORT`
### `CELERY_BROKER_DB`

Настройки Redis broker для Celery.

### `CELERY_RESULT_HOST`
### `CELERY_RESULT_PORT`
### `CELERY_RESULT_DB`

Настройки Redis result backend.

### `CELERY_TASK_DEFAULT_QUEUE`

Имя очереди задач Celery.

### `CELERY_TASK_SERIALIZER`
### `CELERY_RESULT_SERIALIZER`

Сериализация задач и результатов.

### `CELERY_ACCEPT_CONTENT`

Поддерживаемые форматы входного контента. Сейчас ожидается `json`.

### `CELERY_TIMEZONE`

Таймзона Celery.

## RabbitMQ

### `RMQ_PROTOCOL`

Обычно `amqp`.

### `RMQ_USER`
### `RMQ_PASSWORD`

Учетные данные для подключения к RabbitMQ.

### `RMQ_HOST`
### `RMQ_PORT`

Хост и порт RabbitMQ.

### `RMQ_VHOST`

Можно задавать как:

- `/`
- `notifications`

Код сам нормализует это значение в URL.

### `RMQ_QUEUE_NAME`

Имя очереди уведомлений.

### `RMQ_PREFETCH_COUNT`

Количество сообщений, которые consumer может взять без подтверждения.

### `RMQ_DURABLE`

Признак durable-очереди.

### `RMQ_REQUEUE_ON_ERROR`

Нужно ли возвращать сообщение в очередь при ошибке обработки.

## SMTP

### `SMTP_CHANNEL`

Канал провайдера. Сейчас ожидается `email`.

### `SMTP_HOST`
### `SMTP_PORT`

Адрес SMTP-сервера.

### `SMTP_USERNAME`
### `SMTP_PASSWORD`

Учетные данные SMTP.

### `SMTP_SENDER_EMAIL`
### `SMTP_SENDER_NAME`

Значения поля `From` в письме.

### `SMTP_USE_TLS`
### `SMTP_START_TLS`

Настройки TLS/STARTTLS.

Обычно используется одна из двух схем:

- `SMTP_PORT=465` и `SMTP_USE_TLS=true`
- `SMTP_PORT=587` и `SMTP_START_TLS=true`

## Metrics / Monitoring

### `METRICS_API_PATH`

Путь до Prometheus metrics endpoint у API. По умолчанию используется `/metrics`.

### `METRICS_CELERY_PORT`

Порт metrics HTTP server для `celery-worker`.

### `METRICS_BROKER_PORT`

Порт metrics HTTP server для `rabbitmq-consumer`.

## Grafana

### `GRAFANA_ADMIN_USER`
### `GRAFANA_ADMIN_PASSWORD`

Учетные данные администратора Grafana для локального запуска через `docker compose`.

## Рекомендуемые dev-настройки

Для локального запуска через Docker Compose:

- `DB_TYPE=postgres`
- `DB_HOST=postgres`
- `CELERY_BROKER_HOST=redis`
- `CELERY_RESULT_HOST=redis`
- `RMQ_HOST=rabbitmq`
- `METRICS_API_PATH=/metrics`
- `METRICS_CELERY_PORT=9101`
- `METRICS_BROKER_PORT=9102`

## Связанные документы

- [README](../README.md)
- [Архитектура](architecture.md)
