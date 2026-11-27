# Claude Code e Codex CLI com uma Base URL própria

Como apontar o **Claude Code** e o **Codex CLI** (e qualquer SDK da OpenAI) para um relay de API, gateway de LLM, proxy corporativo ou roteador próprio, com uma tabela dos erros mais comuns. Neutro em relação a fornecedores; conferido com a documentação oficial em novembro de 2026.

Ferramentas: [gerador de configuração](https://ethan-cur.github.io/claude-code-config-generator/) · [verificador de endpoint](https://ethan-cur.github.io/llm-endpoint-check/)

## 1. Qual URL vai onde

Cada cliente acrescenta o próprio caminho à Base URL. A maioria dos problemas é prefixo errado.

| Cliente | Configuração | O cliente acrescenta | Valor típico |
|---|---|---|---|
| Claude Code | `ANTHROPIC_BASE_URL` | `/v1/messages` | `https://gateway.example.com` (sem `/v1`) |
| Codex CLI | `base_url` em `[model_providers.<id>]` | `/responses` | `https://gateway.example.com/v1` |
| SDKs OpenAI, Cursor, Cline (modo OpenAI) | `base_url` / `baseURL` / `OPENAI_BASE_URL` | `/chat/completions`, `/models` | `https://gateway.example.com/v1` |

A documentação do seu gateway vale mais que a coluna "típico": alguns usam prefixos próprios (por exemplo `/api` ou `/openai`).

## 2. Claude Code

O Claude Code lê estas variáveis de ambiente ([lista oficial](https://code.claude.com/docs/en/env-vars)):

| Variável | Função |
|---|---|
| `ANTHROPIC_BASE_URL` | Endpoint para onde as requisições vão, em vez de `api.anthropic.com` |
| `ANTHROPIC_AUTH_TOKEN` | Enviado como `Authorization: Bearer <valor>`; é o que a maioria dos relays espera |
| `ANTHROPIC_API_KEY` | Enviado como `X-Api-Key`; use se o gateway pedir esse cabeçalho |
| `ANTHROPIC_MODEL` | Opcional: modelo inicial |

macOS / Linux:

```bash
export ANTHROPIC_BASE_URL="https://gateway.example.com"
export ANTHROPIC_AUTH_TOKEN="YOUR_API_KEY"
claude -p "Reply with: pong"
```

Windows PowerShell (permanente; depois abra um terminal novo):

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://gateway.example.com", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "YOUR_API_KEY", "User")
```

Ou em `~/.claude/settings.json`, que vale para qualquer forma de abrir o Claude Code (terminal, VS Code, JetBrains):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://gateway.example.com",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_API_KEY"
  }
}
```

Bom saber:
- Na maioria das sessões, o valor do `env` no `settings.json` sobrescreve a mesma variável do shell. Se a mudança "não faz nada", confira os dois lugares.
- Defina só uma entre `ANTHROPIC_AUTH_TOKEN` e `ANTHROPIC_API_KEY`, a menos que o gateway exija as duas.
- Segundo a documentação oficial, o Remote Control fica desativado quando `ANTHROPIC_BASE_URL` aponta para um host diferente de `api.anthropic.com`.

## 3. Codex CLI

Adicione um provedor personalizado em `~/.codex/config.toml` ([documentação oficial](https://developers.openai.com/codex/config-advanced)):

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

Observações:
- O Codex envia `POST {base_url}/responses`. O Codex atual só aceita `wire_api = "responses"`, então o endpoint precisa implementar a **Responses** API da OpenAI; gateways só com Chat Completions não funcionam.
- Em vez de `env_key`, alguns serviços documentam `requires_openai_auth = true` com `~/.codex/auth.json` contendo `{"OPENAI_API_KEY": "YOUR_API_KEY"}`. Use um método só.
- Os IDs `openai`, `ollama` e `lmstudio` são reservados. Para só mandar o provedor OpenAI embutido por um proxy, a documentação oficial oferece `openai_base_url = "..."`.

## 4. SDKs OpenAI e outros clientes

```bash
export OPENAI_BASE_URL="https://gateway.example.com/v1"
export OPENAI_API_KEY="YOUR_API_KEY"
```

```python
from openai import OpenAI
client = OpenAI(base_url="https://gateway.example.com/v1", api_key="YOUR_API_KEY")
```

## 5. Teste o endpoint antes de culpar a ferramenta

```bash
# Lado OpenAI: sem chave, uma API saudável responde 401 em JSON; com chave, a lista de modelos
curl -sS https://gateway.example.com/v1/models -H "Authorization: Bearer $KEY"

# Lado Anthropic (o que o Claude Code chama)
curl -sS https://gateway.example.com/v1/messages \
  -H "Authorization: Bearer $KEY" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"MODEL_ID","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}'
```

Ou rode tudo de uma vez, com latência: [llm-endpoint-check](https://github.com/ethan-cur/llm-endpoint-check).

## 6. Solução de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| `404 Not Found` | Prefixo errado | Claude Code: Base URL **sem** `/v1`. Codex / SDKs: geralmente **com** `/v1`. Siga a documentação do gateway |
| A URL tem `/v1/v1/` | `/v1` duplicado | Tire o `/v1` da Base URL |
| `401` / `invalid x-api-key` | Chave ou cabeçalho errado | Alterne entre `ANTHROPIC_AUTH_TOKEN` (Bearer) e `ANTHROPIC_API_KEY` (X-Api-Key); confira espaços ou aspas na chave |
| HTTP 200 com página HTML | Não é rota de API, ou o gateway mostra uma landing page sem chave | Corrija o caminho; confirme que a variável da chave está definida *neste* terminal |
| `301` / `302` | `http` vs `https`, barra final | Use a URL final; muitos clientes perdem o corpo do POST em redirecionamentos |
| `model not found` / `model not available on this endpoint` | O modelo não é servido nesse protocolo | Use um ID de `GET /models`; em muitos relays o Claude só sai pelo caminho Anthropic |
| Codex: erros sobre `wire_api` ou `/chat/completions` | Config antiga com `wire_api = "chat"` | Use `wire_api = "responses"` e um endpoint com Responses |
| O Claude Code continua usando a assinatura | A Base URL não foi lida | Confira o `env` do `settings.json`, reinicie o `claude`; no Windows abra um terminal novo |
| Trava e dá timeout | Rede / firewall / região | Outro endpoint regional do gateway; atrás de proxy corporativo, defina `HTTPS_PROXY` |
| `429` / `402` | Limite de taxa / cota | Espere, reduza a concorrência ou recarregue |

## 7. Exemplo: qcode.cc

O qcode.cc (mantenedor desta página) usa uma chave para os dois protocolos, com prefixos separados e três hosts (`api.qcode.cc` roteamento global, `asia.qcode.cc`, `us.qcode.cc`). Valores da [documentação oficial](https://docs.qcode.cc/docs/getting-started/endpoints-and-api-paths):

| Cliente | Valor |
|---|---|
| Claude Code `ANTHROPIC_BASE_URL` | `https://api.qcode.cc/api` |
| Codex CLI `base_url` | `https://api.qcode.cc/openai` |
| SDK OpenAI `base_url` | `https://api.qcode.cc/openai/v1` |

Modelos Claude só pelo caminho Anthropic; modelos GPT só pelo caminho OpenAI. Mais: https://qcode.cc

---

Mantido pela equipe que opera o [qcode.cc](https://qcode.cc), um relay de API para Claude Code e Codex CLI. Tudo, exceto a seção 7, vale para qualquer endpoint. Correções pelo [GitHub](https://github.com/ethan-cur/claude-code-custom-base-url). Contato: hi@qcode.cc · Licença MIT
