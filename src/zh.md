# Claude Code 与 Codex CLI 自定义 Base URL 配置指南

把 **Claude Code**、**Codex CLI**（以及任意 OpenAI SDK）接到 API 中转站、LLM 网关、公司代理或自建路由上的完整步骤，附常见报错排查表。内容不绑定任何服务商，2026 年 11 月对照官方文档核对。

快捷工具：[配置生成器](https://ethan-cur.github.io/claude-code-config-generator/) · [端点检测脚本](https://ethan-cur.github.io/llm-endpoint-check/)

## 1. 哪个地址填在哪里

每个客户端都会在 Base URL 后面自动拼上自己的路径。大多数"连不上"都是前缀填错了。

| 客户端 | 配置项 | 客户端自动拼接 | 常见填法 |
|---|---|---|---|
| Claude Code | `ANTHROPIC_BASE_URL` | `/v1/messages` | `https://gateway.example.com`（不带 `/v1`） |
| Codex CLI | `[model_providers.<id>]` 里的 `base_url` | `/responses` | `https://gateway.example.com/v1` |
| OpenAI SDK、Cursor、Cline（OpenAI 模式） | `base_url` / `baseURL` / `OPENAI_BASE_URL` | `/chat/completions`、`/models` | `https://gateway.example.com/v1` |

以你所用网关的文档为准：有些服务用自己的前缀（例如 `/api`、`/openai`）。

## 2. Claude Code

Claude Code 读取以下环境变量（[官方列表](https://code.claude.com/docs/en/env-vars)）：

| 变量 | 作用 |
|---|---|
| `ANTHROPIC_BASE_URL` | 请求发往这个地址，而不是 `api.anthropic.com` |
| `ANTHROPIC_AUTH_TOKEN` | 以 `Authorization: Bearer <值>` 发送，多数中转站用这个 |
| `ANTHROPIC_API_KEY` | 以 `X-Api-Key` 发送，网关要求这个请求头时使用 |
| `ANTHROPIC_MODEL` | 可选：启动时使用的模型 |

macOS / Linux：

```bash
export ANTHROPIC_BASE_URL="https://gateway.example.com"
export ANTHROPIC_AUTH_TOKEN="YOUR_API_KEY"
claude -p "Reply with: pong"
```

Windows PowerShell（永久生效，设置后新开一个终端）：

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://gateway.example.com", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "YOUR_API_KEY", "User")
```

也可以写进 `~/.claude/settings.json`，无论从终端、VS Code 还是 JetBrains 启动都会生效：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://gateway.example.com",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_API_KEY"
  }
}
```

注意：
- 多数情况下 `settings.json` 的 `env` 会覆盖 shell 里的同名变量。改了没效果时，两处都检查一下。
- `ANTHROPIC_AUTH_TOKEN` 和 `ANTHROPIC_API_KEY` 只设一个，除非网关要求两个都有。
- 官方文档说明：`ANTHROPIC_BASE_URL` 指向 `api.anthropic.com` 以外的地址时，Remote Control 功能不可用。

## 3. Codex CLI

在 `~/.codex/config.toml` 里加一个自定义 provider（[官方文档](https://developers.openai.com/codex/config-advanced)）：

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

说明：
- Codex 请求的是 `POST {base_url}/responses`。当前版本只支持 `wire_api = "responses"`，所以端点必须实现 OpenAI **Responses** 接口，只支持 Chat Completions 的网关用不了。
- 有些服务的文档用 `requires_openai_auth = true` 加 `~/.codex/auth.json`（内容 `{"OPENAI_API_KEY": "YOUR_API_KEY"}`）代替 `env_key`。两种方式二选一。
- `openai`、`ollama`、`lmstudio` 是保留的 provider ID。如果只想把内置 OpenAI provider 指到代理，官方提供 `openai_base_url = "..."`。

## 4. OpenAI SDK 和其他客户端

```bash
export OPENAI_BASE_URL="https://gateway.example.com/v1"
export OPENAI_API_KEY="YOUR_API_KEY"
```

```python
from openai import OpenAI
client = OpenAI(base_url="https://gateway.example.com/v1", api_key="YOUR_API_KEY")
```

## 5. 先测端点，再怀疑工具

```bash
# OpenAI 侧：正常的 API 不带 key 返回 401 JSON，带 key 返回模型列表
curl -sS https://gateway.example.com/v1/models -H "Authorization: Bearer $KEY"

# Anthropic 侧（Claude Code 实际调用的接口）
curl -sS https://gateway.example.com/v1/messages \
  -H "Authorization: Bearer $KEY" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"MODEL_ID","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}'
```

或者用 [llm-endpoint-check](https://github.com/ethan-cur/llm-endpoint-check) 一次跑完所有检查并测延迟。

## 6. 常见问题排查

| 现象 | 可能原因 | 解决 |
|---|---|---|
| `404 Not Found` | 前缀错误 | Claude Code 的 Base URL **不带** `/v1`；Codex / SDK 一般**带** `/v1`。以网关文档为准 |
| 地址里出现 `/v1/v1/` | `/v1` 重复 | 从 Base URL 里去掉 `/v1` |
| `401` / `invalid x-api-key` | Key 错误或请求头类型不对 | 在 `ANTHROPIC_AUTH_TOKEN`（Bearer）和 `ANTHROPIC_API_KEY`（X-Api-Key）之间切换试试；检查 Key 里有没有空格或引号 |
| 返回 200 但内容是 HTML 页面 | 不是 API 路由，或网关在没带 Key 时显示介绍页 | 修正路径；确认当前终端里确实设置了 Key 变量 |
| `301` / `302` | `http`/`https` 或末尾斜杠不对 | 填最终地址；很多客户端遇到跳转会丢掉 POST 请求体 |
| `model not found` / `model not available on this endpoint` | 该模型不走这个协议 | 用 `GET /models` 返回的 ID；很多中转站的 Claude 模型只能走 Anthropic 路径 |
| Codex 报 `wire_api` 或 `/chat/completions` 相关错误 | 旧配置里写了 `wire_api = "chat"` | 改成 `wire_api = "responses"`，并使用支持 Responses 的端点 |
| Claude Code 仍在用订阅账号 | Base URL 没生效 | 检查 `settings.json` 的 `env`，重启 `claude`；Windows 要新开终端 |
| 卡住然后超时 | 网络 / 防火墙 / 地区 | 换网关的其他地区节点；在公司代理后面时设置 `HTTPS_PROXY` |
| `429` / `402` | 限流 / 额度用完 | 稍等、降低并发或充值 |

## 7. 示例：qcode.cc

qcode.cc（本页维护方）一个 Key 同时支持两种协议，用不同路径前缀区分，有三个接入域名（`api.qcode.cc` 全球智能路由、`asia.qcode.cc` 亚洲、`us.qcode.cc` 北美 / 欧洲）。以下取自[官方文档](https://docs.qcode.cc/docs/getting-started/endpoints-and-api-paths)：

| 客户端 | 填写值 |
|---|---|
| Claude Code `ANTHROPIC_BASE_URL` | `https://api.qcode.cc/api` |
| Codex CLI `base_url` | `https://api.qcode.cc/openai` |
| OpenAI SDK `base_url` | `https://api.qcode.cc/openai/v1` |

Claude 模型只能走 Anthropic 路径，GPT 模型只能走 OpenAI 路径。了解更多：https://qcode.cc

---

本页由 [qcode.cc](https://qcode.cc)（面向 Claude Code 与 Codex CLI 的 API 中转服务）运营团队维护。除第 7 节外，内容适用于任何端点。欢迎在 [GitHub](https://github.com/ethan-cur/claude-code-custom-base-url) 指正。联系：hi@qcode.cc · MIT 许可证
