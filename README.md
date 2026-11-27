# Claude Code & Codex CLI with a custom Base URL

**Read it: https://ethan-cur.github.io/claude-code-custom-base-url/**
Languages: [English](https://ethan-cur.github.io/claude-code-custom-base-url/) · [中文](https://ethan-cur.github.io/claude-code-custom-base-url/zh/) · [Русский](https://ethan-cur.github.io/claude-code-custom-base-url/ru/) · [Português](https://ethan-cur.github.io/claude-code-custom-base-url/pt/) · [한국어](https://ethan-cur.github.io/claude-code-custom-base-url/ko/)

A short, vendor-neutral guide to pointing **Claude Code** (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `~/.claude/settings.json`) and **Codex CLI** (`~/.codex/config.toml`, `[model_providers]`, `wire_api = "responses"`) at an API relay, LLM gateway, corporate proxy or self-hosted router, with a troubleshooting table for the errors people actually hit:

- `404` from a wrong prefix, or `/v1/v1/` from a doubled `/v1`
- `401` / `invalid x-api-key` from `Bearer` vs `X-Api-Key`
- HTTP 200 with an HTML page instead of JSON
- redirects that drop the POST body
- `model not found` / model not available on this endpoint
- Codex `wire_api` errors on Chat-Completions-only gateways
- Claude Code still using the subscription because the Base URL wasn't picked up

Every config key is checked against the official [Claude Code env var docs](https://code.claude.com/docs/en/env-vars) and [Codex config docs](https://developers.openai.com/codex/config-advanced).

Sources are in [`src/`](src/) (one Markdown file per language). `python3 src/make_site.py` regenerates the HTML pages (uses the `gh` CLI's GitHub Markdown API). Fixes and new translations are welcome as PRs.

## Related tools

- [claude-code-config-generator](https://ethan-cur.github.io/claude-code-config-generator/): generate the env vars, `settings.json` or `config.toml` for your endpoint in the browser.
- [llm-endpoint-check](https://github.com/ethan-cur/llm-endpoint-check): zero-dependency CLI that tests `/models`, `/chat/completions`, `/responses` and `/v1/messages` with latency.

## Disclosure

Maintained by the team that operates [qcode.cc](https://qcode.cc), an API relay for Claude Code and Codex CLI. Section 7 of the guide uses qcode.cc as a worked example; everything else applies to any endpoint. Contact: hi@qcode.cc

## License

MIT
