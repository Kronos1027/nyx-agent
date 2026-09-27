# Nyx 🦉

```text
   ╱╲    ▗▄▄▖ ▐     ▗▄▖ ▗▄▄▖
  ╱  ╲   ▐   ▌▐     ▐ ▌▐
 ╱ ╱╲ ╲  ▐▄▄▌ ▐ ▗▄▖ ▐ ▌ ▝▀▚▖
╱_╱  ╲_╲ ▐      ▝▘  ▟▙▘▙▄▟▘
agente IA desktop 100% local — Windows 11
```

**Nyx** (deusa grega da noite) é uma IA companheira desktop para Windows 11,
rodando 100% local (RTX 3060 12GB, 16GB RAM). Ativação por voz ("Ei, Nyx") e
hotkey (Ctrl+Space), avatar em pixel art numa janela overlay flutuante, e
execução REAL de ações no sistema — sempre atrás de camadas de segurança
explícitas (allowlist de comandos, sandbox de arquivos, auditoria JSONL e
confirmação por UI para tudo que é sensível).

> Personalidade: calma, perspicaz, proativa — nunca uma executora passiva.
> Analisa criticamente pedidos ineficientes e sugere alternativas melhores
> ANTES de agir.

## Status real (sem fantasia)

| Fase | Escopo | Status |
|---|---|---|
| **1 — Núcleo sem UI/voz** | LLM+GBNF, allowlist, sandbox, auditoria, CLI | **parcial** — ver [STATUS.md](STATUS.md) |
| 2 — Overlay + sprites | PyQt6 + pixel art (7 estados) | não iniciado |
| 3 — Voz | faster-whisper + hotkey | não iniciado |
| 4 — Automação de UI | pywinauto / pyautogui fallback | não iniciado |
| 5 — Modo autônomo | toggle UI + timeout + trava destrutivos | núcleo já travado por testes |
| 6 — Produtividade | clipboard, project_watch, macros | store de macros funcional |
| 7 — Empacotamento | freeze + README testado + CI | CI de lint+testes já ativo |

O [STATUS.md](STATUS.md) reflete o estado REAL do código (testado com output
colado), não o desejado. O [LIMITACOES.md](LIMITACOES.md) lista limitações
reais encontradas — nada é contornado silenciosamente.

## Arquitetura

```text
src/
├── core/
│   ├── agent_loop.py        # ciclo de decisão: LLM -> validação -> política -> ação
│   ├── llm_client.py        # wrapper llama.cpp + gramática GBNF + validação em 2 camadas
│   └── schema.gbnf          # gramática que FORÇA o JSON do schema (seção 3.3)
├── tools/
│   ├── shell_tool.py        # PowerShell/posix com allowlist de TEMPLATES parametrizados
│   ├── file_tool.py         # leitura/escrita SANDBOXED (raízes permitidas em config)
│   ├── registry.py          # única porta de execução + specs de segurança
│   ├── macro_tool.py        # store de skills gravadas (save/list/replay)
│   ├── ui_tool.py           # (Fase 4) stub
│   ├── clipboard_tool.py    # (Fase 6) stub
│   └── project_watch_tool.py# (Fase 6) stub
├── ui/                      # (Fases 2/5) overlay + permission_dialog — stubs
├── audio/                   # (Fase 3) stt + hotkey — stubs
├── audit/logger.py          # JSONL append-only de TODO ciclo de decisão
├── config.py                # paths, VRAM, allowlists, modos de permissão
└── cli.py                   # loop via terminal (sessão real da Fase 1)
```

## Modelo de segurança (não-negociável)

1. **Schema GBNF em 2 camadas** — o modelo 7B é fisicamente forçado (gramática
   llama.cpp) a emitir o JSON da seção 3.3; se MESMO assim o parse falhar, a
   ação vira `none` automaticamente e o erro vai pro log de auditoria.
2. **Allowlist de templates** — o LLM nunca manda string livre pro subprocess.
   Só templates parametrizados (`LIST_DIR`, `DELETE_FILE`,
   `KILL_PROCESS_BY_NAME`...) com validação anti-injection de cada parâmetro.
3. **Destrutivo confirma SEMPRE** — DELETE_FILE/KILL_PROCESS pedem confirmação
   por UI mesmo em modo autônomo (coberto por teste).
4. **Sandbox de arquivos** — file_tool só opera em raízes declaradas em
   `config.py`; traversal (`../`), paths absolutos externos e symlinks de
   fuga são bloqueados (coberto por testes).
5. **Autônomo só por UI** — ativação aceita apenas fonte `ui_toggle`/
   `ui_hotkey`; texto reconhecido (voz/chat) é ILEGAL por definição
   (`SecurityError` + auditoria). Timeout automático de 30 min.
6. **Auditoria total** — todo ciclo (input → LLM → ação → resultado) vira
   linha JSONL append-only em `logs/`.
7. **Privacidade visível** — mic off = estado `sleep` no overlay (Fase 2),
   nunca escondido em system tray.

## Rodar (dev, sem modelo)

```bash
git clone https://github.com/Kronos1027/nyx-agent.git
cd nyx-agent
python -m venv venv && venv\Scripts\activate   # Windows (Linux: source venv/bin/activate)
pip install -r requirements.txt
pytest tests/ -v
python src/cli.py --offline                    # loop com OfflineLLM (sem GPU/modelo)
```

## Rodar (Windows alvo, com modelo)

```bash
pip install -r requirements.txt -r requirements-windows.txt
# baixar Qwen2.5-7B-Instruct Q5_K_M para models/ (ver STATUS.md)
python src/cli.py --model models/qwen2.5-7b-instruct-q5_k_m.gguf
```

## CI

O GitHub Actions roda `ruff check` + `pytest` em Python 3.11 a cada push —
badge no topo do STATUS.md. O núcleo é multiplataforma por design (imports
lazy das dependências Windows), então o CI Linux valida a lógica de segurança
de verdade.
