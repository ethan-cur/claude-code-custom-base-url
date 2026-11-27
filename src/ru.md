# Claude Code и Codex CLI со своим Base URL

Как подключить **Claude Code** и **Codex CLI** (и любой OpenAI SDK) к API-релею, LLM-шлюзу, корпоративному прокси или собственному роутеру, плюс таблица частых ошибок. Без привязки к поставщику; сверено с официальной документацией в ноябре 2026.

Инструменты: [генератор конфигурации](https://ethan-cur.github.io/claude-code-config-generator/) · [проверка эндпоинта](https://ethan-cur.github.io/llm-endpoint-check/)

## 1. Какой адрес куда

Каждый клиент сам дописывает путь к Base URL. Большинство проблем — неверный префикс.

| Клиент | Настройка | Клиент дописывает | Обычное значение |
|---|---|---|---|
| Claude Code | `ANTHROPIC_BASE_URL` | `/v1/messages` | `https://gateway.example.com` (без `/v1`) |
| Codex CLI | `base_url` в `[model_providers.<id>]` | `/responses` | `https://gateway.example.com/v1` |
| OpenAI SDK, Cursor, Cline (режим OpenAI) | `base_url` / `baseURL` / `OPENAI_BASE_URL` | `/chat/completions`, `/models` | `https://gateway.example.com/v1` |

Документация вашего шлюза важнее колонки «обычное значение»: у некоторых свои префиксы (например, `/api` или `/openai`).

## 2. Claude Code

Claude Code читает эти переменные окружения ([официальный список](https://code.claude.com/docs/en/env-vars)):

| Переменная | Назначение |
|---|---|
| `ANTHROPIC_BASE_URL` | Куда отправлять запросы вместо `api.anthropic.com` |
| `ANTHROPIC_AUTH_TOKEN` | Отправляется как `Authorization: Bearer <значение>`; это ждут большинство релеев |
| `ANTHROPIC_API_KEY` | Отправляется как `X-Api-Key`; если шлюз требует этот заголовок |
| `ANTHROPIC_MODEL` | Необязательно: модель при запуске |

macOS / Linux:

```bash
export ANTHROPIC_BASE_URL="https://gateway.example.com"
export ANTHROPIC_AUTH_TOKEN="YOUR_API_KEY"
claude -p "Reply with: pong"
```

Windows PowerShell (постоянно; затем откройте новый терминал):

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://gateway.example.com", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "YOUR_API_KEY", "User")
```

Или в `~/.claude/settings.json` — работает при любом способе запуска (терминал, VS Code, JetBrains):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://gateway.example.com",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_API_KEY"
  }
}
```

Полезно знать:
- В большинстве сессий значение из `env` в `settings.json` перекрывает одноимённую переменную shell. Если изменение «не работает», проверьте оба места.
- Задавайте только одну из `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_API_KEY`, если шлюзу не нужны обе.
- По официальной документации Remote Control отключается, когда `ANTHROPIC_BASE_URL` указывает не на `api.anthropic.com`.

## 3. Codex CLI

Добавьте свой провайдер в `~/.codex/config.toml` ([официальная документация](https://developers.openai.com/codex/config-advanced)):

```toml
model_provider = "mygateway"
model = "MODEL_ID"

[model_providers.mygateway]
name = "mygateway"
base_url = "https://gateway.example.com/v1"
wire_api = "responses"
env_key = "MYGATEWAY_API_KEY"
```

```bash
export MYGATEWAY_API_KEY="YOUR_API_KEY"
codex
```

Заметки:
- Codex шлёт `POST {base_url}/responses`. Текущий Codex поддерживает только `wire_api = "responses"`, поэтому эндпоинт должен реализовывать OpenAI **Responses** API; шлюзы только с Chat Completions не подойдут.
- Вместо `env_key` некоторые сервисы используют `requires_openai_auth = true` и `~/.codex/auth.json` с `{"OPENAI_API_KEY": "YOUR_API_KEY"}`. Выберите один способ.
- ID `openai`, `ollama` и `lmstudio` зарезервированы. Чтобы просто направить встроенный OpenAI-провайдер через прокси, есть `openai_base_url = "..."`.

## 4. OpenAI SDK и другие клиенты

```bash
export OPENAI_BASE_URL="https://gateway.example.com/v1"
export OPENAI_API_KEY="YOUR_API_KEY"
```

```python
from openai import OpenAI
client = OpenAI(base_url="https://gateway.example.com/v1", api_key="YOUR_API_KEY")
```

## 5. Сначала проверьте эндпоинт

```bash
# OpenAI: без ключа исправный API отвечает 401 JSON, с ключом — списком моделей
curl -sS https://gateway.example.com/v1/models -H "Authorization: Bearer $KEY"

# Anthropic (то, что вызывает Claude Code)
curl -sS https://gateway.example.com/v1/messages \
  -H "Authorization: Bearer $KEY" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"MODEL_ID","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}'
```

Или все проверки с замером задержки сразу: [llm-endpoint-check](https://github.com/ethan-cur/llm-endpoint-check).

## 6. Частые ошибки

| Симптом | Вероятная причина | Решение |
|---|---|---|
| `404 Not Found` | Неверный префикс | Claude Code: Base URL **без** `/v1`. Codex / SDK: обычно **с** `/v1`. Смотрите документацию шлюза |
| В адресе `/v1/v1/` | `/v1` дважды | Уберите `/v1` из Base URL |
| `401` / `invalid x-api-key` | Неверный ключ или заголовок | Попробуйте `ANTHROPIC_AUTH_TOKEN` (Bearer) или `ANTHROPIC_API_KEY` (X-Api-Key); проверьте пробелы и кавычки в ключе |
| HTTP 200, но HTML-страница | Не API-маршрут, или шлюз показывает лендинг без ключа | Исправьте путь; убедитесь, что переменная с ключом задана в *этом* терминале |
| `301` / `302` | `http` вместо `https`, слэш в конце | Укажите конечный адрес; многие клиенты теряют тело POST при редиректе |
| `model not found` / `model not available on this endpoint` | Модель не обслуживается по этому протоколу | Берите ID из `GET /models`; у многих релеев Claude доступен только через Anthropic-путь |
| Codex: ошибки про `wire_api` или `/chat/completions` | Старый конфиг с `wire_api = "chat"` | `wire_api = "responses"` и эндпоинт с поддержкой Responses |
| Claude Code всё ещё использует подписку | Base URL не подхватился | Проверьте `env` в `settings.json`, перезапустите `claude`; в Windows откройте новый терминал |
| Зависает, потом таймаут | Сеть / файрвол / регион | Другой региональный адрес шлюза; за корпоративным прокси задайте `HTTPS_PROXY` |
| `429` / `402` | Лимит запросов / квота | Подождите, снизьте параллелизм или пополните баланс |

## 7. Пример: qcode.cc

qcode.cc (мейнтейнер этой страницы) использует один ключ для обоих протоколов, разные префиксы путей и три домена (`api.qcode.cc` — глобальная маршрутизация, `asia.qcode.cc`, `us.qcode.cc`). Значения из [официальной документации](https://docs.qcode.cc/docs/getting-started/endpoints-and-api-paths):

| Клиент | Значение |
|---|---|
| Claude Code `ANTHROPIC_BASE_URL` | `https://api.qcode.cc/api` |
| Codex CLI `base_url` | `https://api.qcode.cc/openai` |
| OpenAI SDK `base_url` | `https://api.qcode.cc/openai/v1` |

Модели Claude доступны только через Anthropic-путь, GPT — только через OpenAI-путь. Подробнее: https://qcode.cc

---

Страницу поддерживает команда [qcode.cc](https://qcode.cc) — API-релея для Claude Code и Codex CLI. Всё, кроме раздела 7, подходит для любого эндпоинта. Исправления — через [GitHub](https://github.com/ethan-cur/claude-code-custom-base-url). Контакт: hi@qcode.cc · Лицензия MIT
