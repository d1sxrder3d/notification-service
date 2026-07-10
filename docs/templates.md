# Шаблоны

## Общая структура

Шаблоны хранятся в файловой системе.

Для email-уведомлений используется структура:

```text
app/templates/email/<template_code>/
```

Пример:

```text
app/templates/email/welcome/
```

## Поддерживаемые файлы

Для email можно использовать:

- `subject.txt`
- `body.html`
- `body.txt`

Обычно рекомендуется иметь все три файла, но рендерер допускает отсутствие части файлов.

## Как работает рендер

Рендер выполняется через `TemplateManager` и `Jinja2`.

На вход подаются:

- `channel`
- `template_code`
- `payload`

На выходе получается `RenderedTemplate`:

- `subject`
- `html_body`
- `text_body`

Если шаблон отсутствует или не может быть отрендерен, выбрасывается `TemplateRenderingError`.

## Payload

`payload` должен содержать только данные для рендера шаблона.

Туда не стоит складывать transport-level параметры вроде:

- SMTP headers
- `from`
- `cc`
- `bcc`
- настройки подключения

Пример корректного payload:

```json
{
  "name": "Alex",
  "login_url": "https://example.com/login",
  "support_email": "support@example.com"
}
```

## Пример шаблона

`subject.txt`:

```text
Welcome, {{ name }}!
```

`body.html`:

```html
<h1>Hello, {{ name }}</h1>
<p>Your notification flow is working.</p>
```

`body.txt`:

```text
Hello, {{ name }}

Your notification flow is working.
```

## Как добавить новый шаблон

1. Создай директорию:

```text
app/templates/email/<new_template_code>/
```

2. Добавь `subject.txt`.
3. Добавь `body.html`.
4. Добавь `body.txt`.
5. Определи ожидаемый `payload`.
6. Добавь тест рендера.

## Рекомендации

- для каждого email-шаблона держи `body.txt` как plain-text fallback
- не смешивай данные рендера с transport-настройками
- используй понятные `template_code`
- если payload сложный, фиксируй его контракт отдельно в документации или тестах

## Текущие шаблоны

Сейчас в проекте есть:

- `welcome`

## Связанные документы

- [README](../README.md)
- [Провайдеры](providers.md)
