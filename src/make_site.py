"""Render src/*.md to static pages via the GitHub Markdown API (gh CLI). Run from repo root."""
import html, json, os, subprocess
BASE = "https://ethan-cur.github.io/claude-code-custom-base-url/"
LANGS = {
  "en": ("English", "", "Use Claude Code & Codex CLI with a custom Base URL (ANTHROPIC_BASE_URL, config.toml) + troubleshooting",
         "Set ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN for Claude Code and model_providers in Codex CLI config.toml to use any API relay, LLM gateway or proxy. Fix 404, 401, /v1/v1, HTML responses and wire_api errors."),
  "zh": ("中文", "zh/", "Claude Code 与 Codex CLI 自定义 Base URL 配置指南（ANTHROPIC_BASE_URL、config.toml）及报错排查",
         "Claude Code 设置 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN，Codex CLI 在 config.toml 配置 model_providers，接入任意 API 中转站、LLM 网关或代理；排查 404、401、/v1/v1、返回 HTML、wire_api 报错。"),
  "ru": ("Русский", "ru/", "Claude Code и Codex CLI со своим Base URL (ANTHROPIC_BASE_URL, config.toml): настройка и ошибки",
         "Как задать ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN для Claude Code и model_providers в config.toml Codex CLI для любого API-релея, LLM-шлюза или прокси. Ошибки 404, 401, /v1/v1, HTML вместо JSON, wire_api."),
  "pt": ("Português", "pt/", "Claude Code e Codex CLI com Base URL própria (ANTHROPIC_BASE_URL, config.toml) + solução de problemas",
         "Configure ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN no Claude Code e model_providers no config.toml do Codex CLI para usar qualquer relay de API, gateway de LLM ou proxy. Corrija 404, 401, /v1/v1, respostas HTML e erros de wire_api."),
  "ko": ("한국어", "ko/", "Claude Code·Codex CLI 커스텀 Base URL 설정 가이드 (ANTHROPIC_BASE_URL, config.toml) 및 문제 해결",
         "Claude Code의 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN, Codex CLI config.toml의 model_providers를 설정해 API 릴레이, LLM 게이트웨이, 프록시에 연결하는 방법. 404, 401, /v1/v1, HTML 응답, wire_api 오류 해결."),
}
def gfm(text):
    out = subprocess.run(["gh", "api", "-X", "POST", "/markdown", "--input", "-"], input=json.dumps({"text": text, "mode": "gfm"}),
                         capture_output=True, text=True, check=True)
    return out.stdout
alt = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{BASE}{v[1]}">' for l, v in LANGS.items()) + f'\n<link rel="alternate" hreflang="x-default" href="{BASE}">'
for lang, (name, path, title, desc) in LANGS.items():
    body = gfm(open(f"src/{lang}.md", encoding="utf-8").read())
    nav = " · ".join(f'<b>{n}</b>' if l == lang else f'<a href="{BASE}{p}" hreflang="{l}">{n}</a>' for l, (n, p, _, _) in LANGS.items())
    page = f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{BASE}{path}">
{alt}
<style>body{{margin:0;font:16px/1.65 system-ui,-apple-system,Segoe UI,Roboto,"Noto Sans",sans-serif;color:#1f2328}}main{{max-width:920px;margin:0 auto;padding:22px 18px 60px}}
a{{color:#0969da}}nav{{font-size:14px;padding:8px 0;border-bottom:1px solid #d8dee4;margin-bottom:8px}}pre{{background:#f6f8fa;padding:12px;border-radius:6px;overflow:auto;font:13px/1.45 ui-monospace,Menlo,Consolas,monospace}}
code{{background:#f6f8fa;padding:1px 4px;border-radius:4px;font-size:90%}}pre code{{background:none;padding:0}}table{{border-collapse:collapse;display:block;overflow:auto}}
td,th{{border:1px solid #d0d7de;padding:6px 10px;vertical-align:top}}th{{background:#f6f8fa}}h1,h2{{border-bottom:1px solid #d8dee4;padding-bottom:.3em}}</style></head>
<body><main><nav>{nav} · <a href="https://github.com/ethan-cur/claude-code-custom-base-url">GitHub</a></nav>
{body}
</main></body></html>'''
    os.makedirs(path or ".", exist_ok=True)
    open(os.path.join(path or ".", "index.html"), "w", encoding="utf-8").write(page)
    print("wrote", (path or "") + "index.html")
