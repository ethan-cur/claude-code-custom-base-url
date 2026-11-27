# Claude Code와 Codex CLI에 커스텀 Base URL 설정하기

**Claude Code**와 **Codex CLI**(그리고 모든 OpenAI SDK)를 API 릴레이, LLM 게이트웨이, 사내 프록시, 자체 라우터에 연결하는 방법과 실제로 자주 만나는 오류 해결표입니다. 특정 업체에 종속되지 않으며, 2026년 11월 공식 문서 기준으로 확인했습니다.

도구: [설정 생성기](https://ethan-cur.github.io/claude-code-config-generator/) · [엔드포인트 점검 스크립트](https://ethan-cur.github.io/llm-endpoint-check/)

## 1. 어떤 URL을 어디에

각 클라이언트는 Base URL 뒤에 자기 경로를 자동으로 붙입니다. "안 된다"는 문제의 대부분은 접두사 오류입니다.

| 클라이언트 | 설정 | 클라이언트가 붙이는 경로 | 일반적인 값 |
|---|---|---|---|
| Claude Code | `ANTHROPIC_BASE_URL` | `/v1/messages` | `https://gateway.example.com` (`/v1` 없이) |
| Codex CLI | `[model_providers.<id>]`의 `base_url` | `/responses` | `https://gateway.example.com/v1` |
| OpenAI SDK, Cursor, Cline (OpenAI 모드) | `base_url` / `baseURL` / `OPENAI_BASE_URL` | `/chat/completions`, `/models` | `https://gateway.example.com/v1` |

게이트웨이 문서가 "일반적인 값"보다 우선입니다. 일부 서비스는 자체 접두사(예: `/api`, `/openai`)를 씁니다.

## 2. Claude Code

Claude Code는 다음 환경 변수를 읽습니다([공식 목록](https://code.claude.com/docs/en/env-vars)):

| 변수 | 의미 |
|---|---|
| `ANTHROPIC_BASE_URL` | `api.anthropic.com` 대신 요청을 보낼 엔드포인트 |
| `ANTHROPIC_AUTH_TOKEN` | `Authorization: Bearer <값>`으로 전송. 대부분의 릴레이가 이 방식 |
| `ANTHROPIC_API_KEY` | `X-Api-Key`로 전송. 게이트웨이가 이 헤더를 요구할 때 |
| `ANTHROPIC_MODEL` | 선택: 시작 모델 |

macOS / Linux:

```bash
export ANTHROPIC_BASE_URL="https://gateway.example.com"
export ANTHROPIC_AUTH_TOKEN="YOUR_API_KEY"
claude -p "Reply with: pong"
```

Windows PowerShell (영구 설정, 이후 새 터미널 열기):

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://gateway.example.com", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "YOUR_API_KEY", "User")
```

또는 `~/.claude/settings.json`에 넣으면 터미널, VS Code, JetBrains 어디서 실행해도 적용됩니다:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://gateway.example.com",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_API_KEY"
  }
}
```

알아둘 점:
- 대부분의 세션에서 `settings.json`의 `env` 값이 셸의 같은 변수보다 우선합니다. 변경이 "적용되지 않으면" 두 곳을 모두 확인하세요.
- 게이트웨이가 둘 다 요구하지 않는 한 `ANTHROPIC_AUTH_TOKEN`과 `ANTHROPIC_API_KEY` 중 하나만 설정하세요.
- 공식 문서에 따르면 `ANTHROPIC_BASE_URL`이 `api.anthropic.com` 이외의 호스트를 가리키면 Remote Control이 비활성화됩니다.

## 3. Codex CLI

`~/.codex/config.toml`에 커스텀 provider를 추가합니다([공식 문서](https://developers.openai.com/codex/config-advanced)):

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

참고:
- Codex는 `POST {base_url}/responses`를 보냅니다. 현재 Codex는 `wire_api = "responses"`만 지원하므로 엔드포인트가 OpenAI **Responses** API를 구현해야 합니다. Chat Completions만 지원하는 게이트웨이는 안 됩니다.
- 일부 서비스는 `env_key` 대신 `requires_openai_auth = true`와 `{"OPENAI_API_KEY": "YOUR_API_KEY"}`가 담긴 `~/.codex/auth.json`을 안내합니다. 한 가지 방법만 쓰세요.
- `openai`, `ollama`, `lmstudio`는 예약된 provider ID입니다. 내장 OpenAI provider만 프록시로 돌리려면 공식 문서의 `openai_base_url = "..."`을 쓰면 됩니다.

## 4. OpenAI SDK와 기타 클라이언트

```bash
export OPENAI_BASE_URL="https://gateway.example.com/v1"
export OPENAI_API_KEY="YOUR_API_KEY"
```

```python
from openai import OpenAI
client = OpenAI(base_url="https://gateway.example.com/v1", api_key="YOUR_API_KEY")
```

## 5. 도구를 의심하기 전에 엔드포인트부터 테스트

```bash
# OpenAI 측: 정상 API는 키 없이 401 JSON, 키가 있으면 모델 목록을 반환
curl -sS https://gateway.example.com/v1/models -H "Authorization: Bearer $KEY"

# Anthropic 측 (Claude Code가 호출하는 경로)
curl -sS https://gateway.example.com/v1/messages \
  -H "Authorization: Bearer $KEY" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"MODEL_ID","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}'
```

또는 [llm-endpoint-check](https://github.com/ethan-cur/llm-endpoint-check)로 모든 점검과 지연 시간 측정을 한 번에.

## 6. 문제 해결

| 증상 | 가능한 원인 | 해결 |
|---|---|---|
| `404 Not Found` | 접두사 오류 | Claude Code: Base URL에 `/v1` **없이**. Codex / SDK: 보통 `/v1` **포함**. 게이트웨이 문서를 따르세요 |
| URL에 `/v1/v1/` | `/v1` 중복 | Base URL에서 `/v1` 제거 |
| `401` / `invalid x-api-key` | 키 또는 헤더 종류 오류 | `ANTHROPIC_AUTH_TOKEN`(Bearer)과 `ANTHROPIC_API_KEY`(X-Api-Key)를 바꿔 보기; 키에 공백이나 따옴표가 없는지 확인 |
| HTTP 200인데 HTML 페이지 | API 경로가 아니거나, 키가 없을 때 게이트웨이가 안내 페이지를 보여줌 | 경로 수정; *현재* 터미널에 키 변수가 설정됐는지 확인 |
| `301` / `302` | `http`/`https`, 끝 슬래시 | 최종 URL 사용. 많은 클라이언트가 리디렉션 시 POST 본문을 버립니다 |
| `model not found` / `model not available on this endpoint` | 해당 프로토콜에서 제공하지 않는 모델 | `GET /models`의 ID 사용. 많은 릴레이에서 Claude는 Anthropic 경로로만 제공 |
| Codex: `wire_api` 또는 `/chat/completions` 관련 오류 | `wire_api = "chat"`이 든 옛 설정 | `wire_api = "responses"`와 Responses 지원 엔드포인트 사용 |
| Claude Code가 계속 구독 계정을 사용 | Base URL이 적용되지 않음 | `settings.json`의 `env` 확인, `claude` 재시작, Windows는 새 터미널 |
| 멈췄다가 타임아웃 | 네트워크 / 방화벽 / 지역 | 게이트웨이의 다른 지역 엔드포인트 사용; 사내 프록시 뒤라면 `HTTPS_PROXY` 설정 |
| `429` / `402` | 속도 제한 / 할당량 | 기다리거나 동시성을 낮추거나 충전 |

## 7. 예시: qcode.cc

qcode.cc(이 페이지 관리자)는 키 하나로 두 프로토콜을 모두 지원하며, 경로 접두사로 구분하고 호스트가 세 개입니다(`api.qcode.cc` 글로벌 라우팅, `asia.qcode.cc`, `us.qcode.cc`). [공식 문서](https://docs.qcode.cc/docs/getting-started/endpoints-and-api-paths) 기준 값:

| 클라이언트 | 값 |
|---|---|
| Claude Code `ANTHROPIC_BASE_URL` | `https://api.qcode.cc/api` |
| Codex CLI `base_url` | `https://api.qcode.cc/openai` |
| OpenAI SDK `base_url` | `https://api.qcode.cc/openai/v1` |

Claude 모델은 Anthropic 경로로만, GPT 모델은 OpenAI 경로로만 제공됩니다. 자세히: https://qcode.cc

---

이 페이지는 Claude Code와 Codex CLI용 API 릴레이인 [qcode.cc](https://qcode.cc) 운영팀이 관리합니다. 7절을 제외한 모든 내용은 어떤 엔드포인트에도 적용됩니다. 수정 제안은 [GitHub](https://github.com/ethan-cur/claude-code-custom-base-url)로. 연락처: hi@qcode.cc · MIT 라이선스
