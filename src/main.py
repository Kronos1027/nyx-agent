"""Nyx — main.py (Ponto de Entrada Unificado do Agente Desktop)

Permite executar tanto a interface desktop flutuante em PyQt6 quanto a interface CLI.

Uso:
    python src/main.py               # Inicia com Overlay PyQt6 e avatar pixel art
    python src/main.py --cli         # Inicia no modo terminal (CLI)
    python src/main.py --offline     # Inicia no modo offline (sem modelo pesado)
    python src/main.py --model path  # Especifica modelo GGUF
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
from pathlib import Path

# Adiciona 'src' ao sys.path para imports limpos
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit.logger import AuditLogger
from config import NyxConfig, PermissionMode
from core.agent_loop import AgentLoop
from cli import build_registry
from core.llm_client import create_llm_client
from core.memory import MemoryManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("nyx")


def build_llm_for_app(args: argparse.Namespace, cfg: NyxConfig):
    """Constrói o cliente LLM com fallback inteligente e seguro."""
    client, backend = create_llm_client(model_arg=args.model, offline=args.offline, cfg=cfg)
    log.info(f"Cérebro da Nyx ativo via: {backend}")
    return client


def run_gui(args: argparse.Namespace) -> int:
    """Inicia a aplicação gráfica completa com Overlay PyQt6, áudio e hotkeys."""
    from PyQt6.QtWidgets import QApplication
    from audio.hotkey import HotkeyListener
    from audio.stt import SpeechToText
    from ui.overlay import OverlayWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Nyx Desktop Agent")

    cfg = NyxConfig()
    cfg.ensure_dirs()

    audit = AuditLogger(cfg.log_dir, session_id=args.session or "desktop")
    audit.log_event("session_start", mode="gui")

    registry = build_registry(cfg)
    llm = build_llm_for_app(args, cfg)
    memory = MemoryManager(data_dir=Path("data"), session_id=args.session or "desktop")

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        audit=audit,
        mode=PermissionMode.ASSISTIDA,
        autonomy_timeout_seconds=cfg.autonomy_timeout_seconds,
        memory=memory,
    )

    overlay = OverlayWindow(loop=loop)
    overlay.show()

    # Inicializa STT e Hotkeys se não estiver em modo offline estrito
    stt = SpeechToText(model_name=cfg.whisper_model)

    def on_listen_hotkey():
        def _worker():
            try:
                overlay.voice_state_changed.emit("Ouvindo... Fale agora.", "listening")
                text = stt.record_and_transcribe(duration_seconds=3.5)
                if text:
                    has_wake, prompt = stt.process_wake_word(text)
                    overlay.prompt_submitted.emit(prompt if has_wake else text)
                else:
                    overlay.voice_state_changed.emit("Nenhum áudio detectado.", "idle")
            except Exception as e:
                log.error(f"Erro no reconhecimento de voz: {e}")
                overlay.voice_state_changed.emit("Falha ao capturar áudio.", "error")

        threading.Thread(target=_worker, daemon=True).start()

    def on_autonomous_hotkey():
        # Disparo com fonte de UI legítima 'ui_hotkey'
        if loop.mode is PermissionMode.ASSISTIDA:
            loop.activate_autonomous(source="ui_hotkey")
            overlay.current_mode = "autonoma"
            overlay.say("Modo autônomo ativado via Ctrl+Shift+Space (30min).", emotion="think")
        else:
            loop.deactivate_autonomous(source="ui_hotkey")
            overlay.current_mode = "assistida"
            overlay.say("Modo assistido restaurado.", emotion="idle")
    def on_kill_switch_hotkey():
        from tools.ui_tool import set_kill_switch
        set_kill_switch(True)
        if loop.mode is not PermissionMode.ASSISTIDA:
            loop.deactivate_autonomous(source="ui_hotkey")
            overlay.current_mode = "assistida"
            overlay._update_mode_button_style()
        overlay.say("KILL-SWITCH ACIONADO! Todas as ações da Nyx foram abortadas imediatamente.", emotion="error")
        audit.log_event("kill_switch_triggered", {"source": "hotkey_ctrl_alt_k"})

    hotkey_listener = HotkeyListener(
        on_listen=on_listen_hotkey,
        on_toggle_autonomous=on_autonomous_hotkey,
        on_kill_switch=on_kill_switch_hotkey,
    )
    hotkey_listener.start()

    overlay.voice_toggled.connect(on_listen_hotkey)

    # Mensagem de boas-vindas
    welcome_text = "Nyx online (Windows 11). Viseira verde ativada. Estou pronta."
    overlay.say(welcome_text, emotion="idle")

    try:
        ret = app.exec()
    finally:
        hotkey_listener.stop()
        audit.log_event("session_end")

    return ret


def main() -> int:
    parser = argparse.ArgumentParser(description="Nyx — Agente IA Desktop 100% Local (Windows 11)")
    parser.add_argument("--cli", action="store_true", help="Executa no terminal (modo CLI)")
    parser.add_argument("--offline", action="store_true", help="Usa o OfflineLLM sem carregar modelo GGUF")
    parser.add_argument("--model", help="Caminho para o modelo GGUF")
    parser.add_argument("--session", default="main", help="ID da sessão para auditoria")
    args = parser.parse_args()

    if args.cli:
        import cli

        return cli.main()

    return run_gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
