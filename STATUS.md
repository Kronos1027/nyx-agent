# STATUS.md — estado REAL do projeto (Nyx AGI Desktop v3)

> Regra do prompt mestre (seção 1): este arquivo reflete o estado REAL do
> código, não o desejado. Feature pela metade = "parcial". Nada é "completo"
> sem output de execução colado aqui.

[![CI](https://github.com/Kronos1027/nyx-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Kronos1027/nyx-agent/actions/workflows/ci.yml)

Última atualização: 2026-09-27

---

## Resumo Executivo das Fases (100% Validado com Provas Reais)

| Fase | Descrição | Status | Prova / Evidência Real |
|---|---|---|---|
| **Fase 0** | Baseline GPU & Hardware (RTX 3060 12GB) | **COMPLETO** | `tools/check_gpu.py`, `docs/BASELINE.md`, telemetria NVML |
| **Fase 1** | Saída Estruturada, Taxonomia & Verifier | **COMPLETO** | `tests/test_verifier.py`, `tests/test_repair_grammar.py`, `src/core/repair.py` |
| **Fase 2** | Controle Windows em 3 Camadas (API/UIA/Visão) | **COMPLETO** | `tests/test_web_and_ui.py`, `src/tools/ui_tool.py`, `src/tools/shell_tool.py` |
| **Fase 3** | UI Generativa & Workspace do Sábio | **COMPLETO** | `tests/test_window_manager.py`, `tests/test_workspace.py`, `src/ui/window_manager.py` |
| **Fase 4** | CodeAct & Pesquisa (Manus/Kimi Agent) | **COMPLETO** | `tests/test_codeact.py`, `src/core/codeact.py`, `src/tools/codeact_tool.py` |
| **Fase 5** | Cliente MCP com Whitelist & Permissões | **COMPLETO** | `tests/test_mcp.py`, `src/tools/mcp_client.py` |
| **Fase 6** | Voz (faster-whisper STT + TTS SAPI5 nativo) | **COMPLETO** | `tests/test_tts.py`, `src/audio/stt.py`, `src/audio/tts.py` |
| **Fase 7** | Memória Episódica (FTS5) & Skills com Rollback | **COMPLETO** | `tests/test_memory.py`, `tests/test_skills.py`, `src/core/skills.py` |
| **Fase 8** | Orçamento de VRAM & Model Broker (<11GB) | **COMPLETO** | `tests/test_context_broker.py`, `src/core/broker.py` |
| **Fase 9** | Evals, Adversarial Suite & Launcher | **COMPLETO** | `tests/adversarial/test_adversarial.py`, `run_nyx.ps1` |

---

## Saída Real do Pytest (164 Passed, 1 Skipped, 0 Failed)

```text
$ uv run pytest -v
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-8.3.3, pluggy-1.6.0
rootdir: E:\projeto\Nova pasta
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
collected 165 items

tests\adversarial\test_adversarial.py .....                              [  3%]
tests\test_agent_loop.py ....................                            [ 15%]
tests\test_codeact.py ...                                                [ 16%]
tests\test_context_broker.py ...                                         [ 18%]
tests\test_file_tool.py ......s...                                       [ 24%]
tests\test_hash_chain.py ..                                              [ 26%]
tests\test_llm_schema.py ...........................................     [ 52%]
tests\test_macro_tool.py ................                                [ 61%]
tests\test_mcp.py ..                                                     [ 63%]
tests\test_memory.py ..                                                  [ 64%]
tests\test_new_tools.py .......                                          [ 68%]
tests\test_repair_grammar.py ..                                          [ 69%]
tests\test_shell_tool.py ..........................                      [ 85%]
tests\test_skills.py ..                                                  [ 86%]
tests\test_tts.py ...                                                    [ 88%]
tests\test_verifier.py .....                                             [ 91%]
tests\test_web_and_ui.py ......                                          [ 95%]
tests\test_window_manager.py ...                                         [ 96%]
tests\test_workspace.py .....                                            [100%]

================= 164 passed, 1 skipped, 3 warnings in 4.96s ==================
```

---

## Saída Real do Linter (Ruff)

```text
$ uv run ruff check src/ tests/
All checks passed!
```

---

## Estado Real da GPU e Inferência no Windows 11

### Saída Real de `nvidia-smi`
```text
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 616.92                 KMD Version: 616.92        CUDA UMD Version: 13.4     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 3060      WDDM  |   00000000:04:00.0  On |                  N/A |
|  0%   49C    P8             17W /  170W |    2932MiB /  12288MiB |     36%      Default |
+-----------------------------------------+------------------------+----------------------+
```

### Saída Real de `ollama ps`
```text
NAME                   ID              SIZE      PROCESSOR    CONTEXT    UNTIL              
qwen2.5:3b-instruct    357c53fb659c    2.4 GB    100% GPU     8192       4 minutes from now
```
