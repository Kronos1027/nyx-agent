# STATUS.md — estado REAL do projeto

> Regra do prompt mestre (seção 1): este arquivo reflete o estado REAL do
> código, não o desejado. Feature pela metade = "parcial". Nada é "completo"
> sem output de execução colado aqui.

[![CI](https://github.com/Kronos1027/nyx-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Kronos1027/nyx-agent/actions/workflows/ci.yml)

Última atualização: 2026-09-02

## Fase 1 — Núcleo sem UI/voz

**Status: PARCIAL** — todo o núcleo multiplataforma está implementado e
testado (Linux/CI); os itens que exigem a máquina Windows alvo (GPU, modelo
GGUF real) estão pendentes e marcados abaixo.

### Implementado e TESTADO (com prova)

| Item | Prova |
|---|---|
| `llm_client.py` — validação de schema em 2 camadas (GBNF + `validate_payload`), fallback seguro `action=none` | `pytest tests/test_llm_schema.py` — 39 testes, incluindo 20+ payloads válidos parametrizados |
| `schema.gbnf` — gramática cobrindo as 7 emoções, 9 action.types e todas as chaves da seção 3.3 | `test_grammar_covers_all_enums`, `test_grammar_has_required_keys` |
| `shell_tool.py` — allowlist de templates, bloqueio fora da lista, anti-injection (`;|&$` traversal, aspas, newline, argument injection), flag destrutivo | `pytest tests/test_shell_tool.py` — 26 testes, incl. execução REAL posix (`ls`, `df`) sem `shell=True` |
| `file_tool.py` — sandbox por raízes, bloqueio de `../`, path absoluto externo e symlink de fuga | `pytest tests/test_file_tool.py` — 10 testes com IO real |
| `audit/logger.py` — JSONL append-only thread-safe | `test_audit_log_is_jsonl_append_only` + sessão real abaixo |
| `agent_loop.py` — ciclo completo, política de confirmação, modo autônomo (só fonte UI), timeout, destrutivo sempre confirma | `pytest tests/test_agent_loop.py` — 22 testes (relógio fake para timeout) |
| `macro_tool.py` — save/list/replay com bloqueio de destrutivos no replay | `pytest tests/test_macro_tool.py` — 16 testes |
| CLI com loop real de terminal | sessão real abaixo |

**Output real do pytest (comando + resultado):**

```text
$ python3 -m pytest tests/ -v
tests/test_agent_loop.py ....................                            [ 18%]
tests/test_file_tool.py ..........                                       [ 27%]
tests/test_llm_schema.py .......................................         [ 62%]
tests/test_macro_tool.py ................                                [ 76%]
tests/test_shell_tool.py ..........................                      [100%]

============================= 111 passed in 0.26s ==============================
```

**Output real do lint:**

```text
$ python3 -m ruff check src tests
All checks passed!
```

**Log real de sessão de terminal rodando o loop via CLI (definition of done):**

```text
$ python3 src/cli.py --offline --session demo
[modo offline — OfflineLLM determinístico, NÃO é o modelo real]
════════ Nyx — agente desktop (Fase 1) ════════
modo: assistida (viseira verde) | sessão: demo
você> liste o diretório
[confirmação necessária] Confirmar 'shell' (modo assistida)? params: {'template': 'LIST_DIR', 'path': '.'}
você> sim
nyx> total 64 ... (listagem real executada)

você> anote isso num arquivo
[confirmação necessária] Confirmar 'write_file' (modo assistida)? ...
você> sim
nyx> escrito: /tmp/nyx_dev_sandbox/nota-demo.txt (16 bytes)

você> apaga a nota
[sugestão melhor] Mover para uma pasta _trash na sandbox seria reversível.
[confirmação necessária] ⚠️ AÇÃO DESTRUTIVA 'shell' — params: {'template': 'DELETE_FILE', 'path': '/tmp/nyx_dev_sandbox/nota-demo.txt'}
você> sim
nyx> (arquivo deletado)
```

**Auditoria JSONL real gerada por essa sessão** (`logs/nyx_audit_demo.jsonl`):

```json
{"ts": "2026-09-02T13:48:15.623+00:00", "event": "session_start"}
{"event": "decision", "action_type": "shell", "executed": false, "mode": "assistida", "parse_ok": true}
{"event": "confirmed_execution", "action_type": "shell", "result_ok": true, "params": {"template": "LIST_DIR", "path": "."}}
{"event": "confirmed_execution", "action_type": "write_file", "result_ok": true, "params": {"path": "nota-demo.txt", "content": "Nyx esteve aqui."}}
{"event": "confirmed_execution", "action_type": "shell", "result_ok": true, "params": {"template": "DELETE_FILE", "path": "/tmp/nyx_dev_sandbox/nota-demo.txt"}}
{"event": "session_end"}
```

### Pendente nesta fase (exige máquina Windows alvo)

- [ ] **Validação do modelo real**: rodar 20 prompts variados contra o
  Qwen2.5-7B-Instruct Q5_K_M com `n_gpu_layers=-1` e colar aqui 0 falhas de
  parse. A gramática GBNF e o validador estão prontos e testados; o
  comportamento do modelo de verdade NÃO foi observado ainda.
- [ ] Teste do dialeto powershell real (templates montam o script PS, mas só
  rodam de fato no Windows).
- [ ] Instalação do `llama-cpp-python` no Windows com CUDA (RTX 3060).

## Fases 2–7

- **Fase 2 (overlay + sprites)**: não iniciado. Stubs em `src/ui/` e spec em
  `assets/README.md`.
- **Fase 3 (voz)**: não iniciado. Stubs em `src/audio/`.
- **Fase 4 (automação de UI)**: não iniciado. Stub em `src/tools/ui_tool.py`.
- **Fase 5 (modo autônomo + confirmação de UI)**: PARCIAL — as regras de
  segurança do núcleo já existem e são testadas (ativação só por fonte UI,
  timeout automático, destrutivo sempre confirma mesmo em autônomo:
  `test_destructive_still_requires_confirmation_in_autonomous`). Falta o
  permission_dialog PyQt6 real e o toggle na overlay.
- **Fase 6 (produtividade)**: PARCIAL — macro store funcional e testado;
  clipboard_tool e project_watch_tool são stubs.
- **Fase 7 (empacotamento)**: PARCIAL — CI de lint+testes ativo; falta
  freeze final de requirements e README testado do zero em venv limpo no
  Windows.

## Decisões de arquitetura tomadas (documentadas pra auditoria)

1. **Schema da seção 3.3 não tem `delete_file` como action.type** — deleção é
   expressa via `shell` + template `DELETE_FILE` (destructive). Assim o LLM
   nem consegue pedir deleção fora da allowlist. Teste
   `test_llm_cannot_express_actions_outside_schema` trava isso.
2. **`destructive_probe` no ToolSpec** — a ferramenta `shell` agrupa templates
   destrutivos e não-destrutivos; o probe avalia o parâmetro `template` do
   pedido concreto. Fail-safe: exceção no probe = tratado como destrutivo.
3. **Dialetos posix/powershell** no shell_tool — permitem que a lógica de
   allowlist seja testada de verdade no CI Linux. O dialeto Windows é o mesmo
   código, pendente de validação real.
4. **Paths relativos no file_tool resolvem contra a sandbox primária**
   (nunca contra o CWD do processo).
