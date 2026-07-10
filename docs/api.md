# API

## Базовый префикс

```text
/api/v1
```

## Основные endpoints

### `POST /notifications`

Создает новое уведомление.

#### Тело запроса

```json
{
  "user_id": 10,
  "channel": "email",
  "recipient": "user@example.com",
  "template_code": "welcome",
  "payload": {
    "name": "Alex"
  },
  "idempotency_key": "welcome-email-1",
  "scheduled_at": null
}
```

#### Поля

- `user_id` - идентификатор пользователя
- `channel` - канал доставки
- `recipient` - адрес получателя
- `template_code` - код шаблона
- `payload` - данные для рендера шаблона
- `idempotency_key` - ключ идемпотентности
- `scheduled_at` - поле под будущую отложенную отправку

#### Ответ

```json
{
  "id": 1,
  "status": "pending"
}
```

### `POST /notifications/{notification_id}/retry`

Повторно ставит уведомление в отправку, если retry допустим.

#### Ответ

```json
{
  "id": 1,
  "status": "pending"
}
```

#### Ошибки

- `404` - уведомление не найдено
- `409` - retry запрещен

### `GET /notifications/{notification_id}`

Возвращает полное состояние уведомления.

#### Ответ

```json
{
  "id": 1,
  "user_id": 10,
  "channel": "email",
  "recipient": "user@example.com",
  "template_code": "welcome",
  "payload": {
    "name": "Alex"
  },
  "status": "sent",
  "attempts": 1,
  "max_attempts": 3,
  "scheduled_at": null,
  "sent_at": "2026-07-10T12:00:00Z",
  "created_at": "2026-07-10T11:59:00Z",
  "updated_at": "2026-07-10T12:00:00Z"
}
```

## Каналы

Сейчас поддерживается:

- `email`

## Статусы

Поддерживаются:

- `pending`
- `processing`
- `sent`
- `failed`

## Ошибки

На уровне API сейчас используются стандартные FastAPI/HTTP ошибки:

- `422` - ошибка валидации входного payload
- `404` - сущность не найдена
- `409` - конфликт состояния, например retry недопустим

## OpenAPI

После запуска приложения:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Связанные документы

- [README](../README.md)
- [Архитектура](architecture.md)
