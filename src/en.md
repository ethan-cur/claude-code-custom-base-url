# Use Claude Code and Codex CLI with a custom Base URL

How to point **Claude Code** and **Codex CLI** (and any OpenAI SDK) at an API relay, LLM gateway, corporate proxy or self-hosted router, plus a troubleshooting table for the errors people actually hit. Vendor-neutral; checked against the official docs in November 2026.

Quick tools: [config generator](https://ethan-cur.github.io/claude-code-config-generator/) · [endpoint checker](https://ethan-cur.github.io/llm-endpoint-check/)

## 1. Which URL goes where

Every client appends its own path to the Base URL. Most "it doesn't work" reports are a wrong prefix.

| Client | Setting | Client appends | Typical value |
|---|---|---|---|
| Claude Code | `ANTHROPIC_BASE_URL` | `/v1/messages` | `https://gateway.example.com` (no `/v1`) |
| Codex CLI | `base_url` in `[model_providers.<id>]` | `/responses` | `https://gateway.example.com/v1` |
| OpenAI SDKs, Cursor, Cline (OpenAI mode) | `base_url` / `baseURL` / `OPENAI_BASE_URL` | `/chat/completions`, `/models` | `https://gateway.example.com/v1` |

Your gateway's docs win over the "typical" column: some use their own prefixes (for example `/api` or `/openai`).

## 2. Claude Code

Claude Code reads these environment variables ([official list](https://code.claude.com/docs/en/env-vars)):

| Variable | Meaning |
|---|---|
| `ANTHROPIC_BASE_URL` | Endpoint to send requests to instead of `api.anthropic.com` |
| `ANTHROPIC_AUTH_TOKEN` | Sent as `Authorization: Bearer <value>`; what most relays expect |
| `ANTHROPIC_API_KEY` | Sent as `X-Api-Key`; use if your gateway wants that header |
| `ANTHROPIC_MODEL` | Optional: model to start with |

macOS / Linux:

```bash
export ANTHROPIC_BASE_URL="https://gateway.example.com"
export ANTHROPIC_AUTH_TOKEN="YOUR_API_KEY"
claude -p "Reply with: pong"
```

Windows PowerShell (permanent, then open a new terminal):

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://gateway.example.com", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "YOUR_API_KEY", "User")
```

Or put them in `~/.claude/settings.json`, which Claude Code applies however it is launched (terminal, VS Code, JetBrains):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://gateway.example.com",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_API_KEY"
  }
}
```

Good to know:
- A value in `settings.json` `env` overrides the same variable from your shell in most sessions. If a change "does nothing", check both places.
- Set only one of `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_API_KEY` unless your gateway needs both.
- Per the official docs, Remote Control is disabled when `ANTHROPIC_BASE_URL` points to a host other than `api.anthropic.com`.

## 3. Codex CLI

Add a custom provider to `~/.codex/config.toml` ([official docs](https://developers.openai.com/codex/config-advanced)):

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

Notes:
- Codex sends `POST {base_url}/responses`. Current Codex supports only `wire_api = "responses"`, so the endpoint must implement the OpenAI **Responses** API; Chat-Completions-only gateways won't work.
- Instead of `env_key` some gateways document `requires_openai_auth = true` plus `~/.codex/auth.json` containing `{"OPENAI_API_KEY": "YOUR_API_KEY"}`. Use one method, not both.
- Provider IDs `openai`, `ollama` and `lmstudio` are reserved. To only move the built-in OpenAI provider to a proxy, the official docs offer `openai_base_url = "..."` instead.

## 4. OpenAI SDKs and other clients

```bash
export OPENAI_BASE_URL="https://gateway.example.com/v1"
export OPENAI_API_KEY="YOUR_API_KEY"
```

```python
from openai import OpenAI
client = OpenAI(base_url="https://gateway.example.com/v1", api_key="YOUR_API_KEY")
```

## 5. Test the endpoint before blaming the tool

```bash
# OpenAI side: a healthy API returns 401 JSON without a key, a model list with one
curl -sS https://gateway.example.com/v1/models -H "Authorization: Bearer $KEY"

# Anthropic side (what Claude Code calls)
curl -sS https://gateway.example.com/v1/messages \
  -H "Authorization: Bearer $KEY" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"MODEL_ID","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}'
```

Or run all checks with latency in one go: [llm-endpoint-check](https://github.com/ethan-cur/llm-endpoint-check).

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `404 Not Found` | Wrong prefix | Claude Code: base **without** `/v1`. Codex / SDKs: usually **with** `/v1`. Follow your gateway's docs |
| URL contains `/v1/v1/` | `/v1` added twice | Remove `/v1` from the Base URL |
| `401` / `invalid x-api-key` | Wrong key or wrong header | Try `ANTHROPIC_AUTH_TOKEN` (Bearer) vs `ANTHROPIC_API_KEY` (X-Api-Key); check for spaces or quotes in the key |
| HTTP 200 but an HTML page | Not an API route, or the gateway shows a landing page when no key is sent | Fix the path; make sure the key variable is set in *this* shell |
| `301` / `302` | `http` vs `https`, trailing slash | Use the final URL; many clients drop the POST body on redirects |
| `model not found` / `model not available on this endpoint` | The model isn't served on that protocol | Use an ID from `GET /models`; on many relays Claude models are only on the Anthropic path |
| Codex: errors about `wire_api` or `/chat/completions` | Old config with `wire_api = "chat"` | Use `wire_api = "responses"` and an endpoint that supports Responses |
| Claude Code still uses your subscription | Base URL not picked up | Check `settings.json` `env`, restart `claude`, open a new terminal on Windows |
| Hangs, then times out | Network / firewall / region | Try another region endpoint of your gateway; set `HTTPS_PROXY` if you are behind a corporate proxy |
| `429` / `402` | Rate limit / quota | Wait, lower concurrency, or top up |

## 7. Example: qcode.cc

qcode.cc (maintainer of this page) uses one key for both protocols, with separate path prefixes and three hostnames (`api.qcode.cc` global routing, `asia.qcode.cc`, `us.qcode.cc`). Values from the [official docs](https://docs.qcode.cc/docs/getting-started/endpoints-and-api-paths):

| Client | Value |
|---|---|
| Claude Code `ANTHROPIC_BASE_URL` | `https://api.qcode.cc/api` |
| Codex CLI `base_url` | `https://api.qcode.cc/openai` |
| OpenAI SDK `base_url` | `https://api.qcode.cc/openai/v1` |

Claude models are served only on the Anthropic path, GPT models only on the OpenAI path. More: https://qcode.cc

---

Maintained by the team that operates [qcode.cc](https://qcode.cc), an API relay for Claude Code and Codex CLI. Everything except section 7 applies to any endpoint. Corrections welcome via [GitHub](https://github.com/ethan-cur/claude-code-custom-base-url). Contact: hi@qcode.cc · MIT License
