"""Nyx — ui/overlay.py (Fase 2: Overlay Flutuante & Avatar Pixel Art)

Janela desktop flutuante em PyQt6:
- Frameless + TranslucentBackground + WindowStaysOnTopHint
- Avatar animado em pixel art renderizado via SpriteRenderer (7 estados emocionais)
- Balão de fala cyberpunk com animação e expansão
- Campo de entrada de prompt integrado e botão de microfone
- Toggle seguro de modo de permissão (assistida <-> autônoma)
- Arrastável livremente pela tela
- Conexão direta com o ciclo de decisão do AgentLoop e PermissionDialog
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.permission_dialog import PermissionDialog
from ui.sprite_renderer import SpriteRenderer

if TYPE_CHECKING:
    from core.agent_loop import AgentLoop

log = logging.getLogger(__name__)


class SpeechBubble(QFrame):
    """Balão de fala cyberpunk para exibição das falas e pensamentos do Nyx."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            """
            QFrame {
                background-color: rgba(15, 23, 42, 235);
                border: 1px solid #334155;
                border-radius: 10px;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.lbl_speaker = QLabel("Nyx", self)
        self.lbl_speaker.setStyleSheet(
            "color: #A78BFA; font-weight: bold; font-size: 11px; border: none;"
        )
        layout.addWidget(self.lbl_speaker)

        self.lbl_text = QLabel("Olá. Como posso ajudar você hoje?", self)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet(
            "color: #F1F5F9; font-size: 12px; border: none; font-family: 'Segoe UI', sans-serif;"
        )
        layout.addWidget(self.lbl_text)

        self.lbl_suggestion = QLabel("", self)
        self.lbl_suggestion.setWordWrap(True)
        self.lbl_suggestion.setStyleSheet(
            "color: #FDE047; font-size: 11px; font-style: italic; border: none;"
        )
        self.lbl_suggestion.setVisible(False)
        layout.addWidget(self.lbl_suggestion)

    def set_message(self, text: str, suggestion: str | None = None) -> None:
        self.lbl_text.setText(text)
        if suggestion:
            self.lbl_suggestion.setText(f"💡 Sugestão: {suggestion}")
            self.lbl_suggestion.setVisible(True)
        else:
            self.lbl_suggestion.setVisible(False)


class OverlayWindow(QWidget):
    """Overlay flutuante do agente Nyx com avatar pixel art interativo."""

    # Sinais para integração assíncrona
    prompt_submitted = pyqtSignal(str)
    voice_toggled = pyqtSignal()
    voice_state_changed = pyqtSignal(str, str)  # (texto, emoção)

    def __init__(self, loop: AgentLoop | None = None) -> None:
        super().__init__()
        self.loop = loop
        self.current_emotion = "idle"
        self.current_mode = loop.mode_name if loop else "assistida"
        self.anim_frame = 0
        self._drag_pos = QPoint()
        self._is_dragging = False

        from audio.tts import TextToSpeech
        self.tts = TextToSpeech()

        self.renderer = SpriteRenderer(scale=5)  # 180x180 px

        # Configurações da Janela
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(360)

        # Conexão de sinais assíncronos
        self.prompt_submitted.connect(self.process_prompt)
        self.voice_state_changed.connect(self._on_voice_state_changed)

        self._init_ui()
        self._init_timer()
        self._center_on_screen_bottom_right()

    def _init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(6)

        # 1. Balão de fala
        self.bubble = SpeechBubble(self)
        self.main_layout.addWidget(self.bubble)

        # 2. Linha do Avatar e Controles
        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(10)

        # Label onde o sprite pixel art é renderizado
        self.avatar_label = QLabel(self)
        self.avatar_label.setFixedSize(180, 180)
        self.avatar_label.setCursor(Qt.CursorShape.OpenHandCursor)
        self._update_avatar_pixmap()
        avatar_row.addWidget(self.avatar_label)

        # Painel lateral de status e ações rápidas
        side_panel = QVBoxLayout()
        side_panel.setSpacing(6)
        side_panel.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Botão indicador do modo (Assistida / Autônoma)
        self.btn_mode = QPushButton(self)
        self.btn_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode.clicked.connect(self._toggle_mode_clicked)
        self._update_mode_button_style()
        side_panel.addWidget(self.btn_mode)

        # Botão de voz (Push-to-talk / Toggle)
        self.btn_mic = QPushButton("🎙️ Ouvir", self)
        self.btn_mic.setStyleSheet(
            """
            QPushButton {
                background-color: #1E293B;
                color: #38BDF8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0284C7;
                color: #FFFFFF;
            }
            """
        )
        self.btn_mic.clicked.connect(self._on_mic_clicked)
        side_panel.addWidget(self.btn_mic)

        # Botão Grande Sábio (Workspace Sub-Window)
        self.btn_sage = QPushButton("🧙 Sábio", self)
        self.btn_sage.setStyleSheet(
            """
            QPushButton {
                background-color: #1E293B;
                color: #10B981;
                border: 1px solid #059669;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #059669;
                color: #FFFFFF;
            }
            """
        )
        self.btn_sage.clicked.connect(self._toggle_workspace)
        side_panel.addWidget(self.btn_sage)

        # Botão Minimizar/Fechar overlay
        self.btn_close = QPushButton("✕ Sair", self)
        self.btn_close.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                color: #64748B;
                border: none;
                font-size: 10px;
                padding: 4px;
            }
            QPushButton:hover {
                color: #EF4444;
            }
            """
        )
        self.btn_close.clicked.connect(self.close)
        side_panel.addWidget(self.btn_close)

        avatar_row.addLayout(side_panel)
        avatar_row.addStretch()
        self.main_layout.addLayout(avatar_row)

        # 3. Barra de entrada de texto
        input_container = QFrame(self)
        input_container.setStyleSheet(
            """
            QFrame {
                background-color: rgba(30, 41, 59, 230);
                border: 1px solid #475569;
                border-radius: 8px;
            }
            """
        )
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.setSpacing(6)

        self.txt_input = QLineEdit(input_container)
        self.txt_input.setPlaceholderText("Comando ou mensagem para Nyx...")
        self.txt_input.setStyleSheet(
            """
            QLineEdit {
                background: transparent;
                border: none;
                color: #F8FAFC;
                font-size: 12px;
                padding: 4px;
            }
            QLineEdit:focus {
                outline: none;
            }
            """
        )
        self.txt_input.returnPressed.connect(self._on_send_prompt)
        input_layout.addWidget(self.txt_input)

        btn_send = QPushButton("➔", input_container)
        btn_send.setFixedSize(28, 28)
        btn_send.setStyleSheet(
            """
            QPushButton {
                background-color: #7C3AED;
                color: #FFFFFF;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #8B5CF6;
            }
            """
        )
        btn_send.clicked.connect(self._on_send_prompt)
        input_layout.addWidget(btn_send)

        self.main_layout.addWidget(input_container)

    def _init_timer(self) -> None:
        """Timer de animação periódica para respiração e micro-movimentos."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick_animation)
        self.timer.start(550)

    def _tick_animation(self) -> None:
        self.anim_frame = (self.anim_frame + 1) % 4
        self._update_avatar_pixmap()

    def _update_avatar_pixmap(self) -> None:
        pix = self.renderer.get_pixmap(
            emotion=self.current_emotion,
            mode=self.current_mode,
            frame=self.anim_frame,
        )
        self.avatar_label.setPixmap(pix)

    def _update_mode_button_style(self) -> None:
        if self.current_mode == "autonoma":
            self.btn_mode.setText("⚡ Autônoma")
            self.btn_mode.setStyleSheet(
                """
                QPushButton {
                    background-color: #78350F;
                    color: #FBBF24;
                    border: 1px solid #D97706;
                    border-radius: 6px;
                    padding: 6px 8px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #92400E;
                }
                """
            )
        else:
            self.btn_mode.setText("🛡️ Assistida")
            self.btn_mode.setStyleSheet(
                """
                QPushButton {
                    background-color: #064E3B;
                    color: #34D399;
                    border: 1px solid #059669;
                    border-radius: 6px;
                    padding: 6px 8px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #065F46;
                }
                """
            )

    def _toggle_mode_clicked(self) -> None:
        if not self.loop:
            return
        if self.current_mode == "assistida":
            # Ativação autônoma legítima por fonte UI
            self.loop.activate_autonomous(source="ui_toggle")
            self.current_mode = "autonoma"
            self.say("Modo autônomo ativado (30min). Viseira âmbar ligada.", emotion="think")
        else:
            self.loop.deactivate_autonomous(source="ui_toggle")
            self.current_mode = "assistida"
            self.say("Modo assistido ativo. Pedirei confirmação para ações sensíveis.", emotion="idle")
        self._update_mode_button_style()
        self._update_avatar_pixmap()

    def _center_on_screen_bottom_right(self) -> None:
        from PyQt6.QtGui import QGuiApplication

        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.width() - self.width() - 30
            y = geo.height() - self.height() - 40
            self.move(x, y)

    # ----------------------------------------------------------------------
    # Eventos de Arrastar Janela
    # ----------------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.avatar_label.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._is_dragging = False
        self.avatar_label.setCursor(Qt.CursorShape.OpenHandCursor)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Encerra TTS de forma limpa ao fechar a janela."""
        if hasattr(self, "tts") and self.tts:
            self.tts.shutdown()
        super().closeEvent(event)

    # ----------------------------------------------------------------------
    # API de Estados e Fala
    # ----------------------------------------------------------------------
    def set_emotion(self, emotion: str) -> None:
        self.current_emotion = emotion
        self._update_avatar_pixmap()

    def say(self, text: str, emotion: str = "talk", suggestion: str | None = None) -> None:
        self.set_emotion(emotion)
        self.bubble.set_message(text, suggestion)
        if hasattr(self, "tts") and self.tts:
            self.tts.speak(text)

    def _on_voice_state_changed(self, text: str, emotion: str) -> None:
        self.set_emotion(emotion)
        self.bubble.set_message(text, None)

    def listen(self) -> None:
        self.set_emotion("listening")
        self.bubble.set_message("Ouvindo... Fale agora.", None)

    def think(self) -> None:
        self.set_emotion("think")
        self.bubble.set_message("Pensando e analisando melhor plano...", None)

    def show_error(self, err: str) -> None:
        self.set_emotion("error")
        self.bubble.set_message(f"Erro: {err}", None)

    # ----------------------------------------------------------------------
    # Ciclo de Execução do AgentLoop
    # ----------------------------------------------------------------------
    def _on_send_prompt(self) -> None:
        text = self.txt_input.text().strip()
        if not text:
            return
        self.txt_input.clear()
        # Interrompe fala atual antes de processar novo prompt
        if hasattr(self, "tts") and self.tts:
            self.tts.stop_current()
        self.process_prompt(text)

    def _on_mic_clicked(self) -> None:
        self.voice_toggled.emit()

    def process_prompt(self, user_prompt: str) -> None:
        """Executa um prompt pelo loop do Nyx com diálogo de segurança."""
        if not self.loop:
            self.say(f"Recebido: {user_prompt} (sem loop ativo)")
            return

        self.think()
        from PyQt6.QtWidgets import QApplication

        QApplication.processEvents()

        try:
            result = self.loop.process(user_prompt)
        except Exception as exc:
            self.show_error(str(exc))
            return

        resp = result.response
        self.current_mode = self.loop.mode_name
        self._update_mode_button_style()

        if result.needs_confirmation and result.pending_action:
            # Dispara diálogo modal de confirmação
            spec = self.loop.registry.spec(result.pending_action.get("type", ""))
            is_destructive = spec.is_destructive_for(result.pending_action.get("params", {})) if spec else False

            self.set_emotion("surprised" if is_destructive else "think")
            approved = PermissionDialog.ask_confirmation(
                result.pending_action,
                prompt=result.confirmation_prompt,
                is_destructive=is_destructive,
                parent=self,
            )
            # Confirma no loop
            conf_result = self.loop.confirm_pending(result.pending_action, approved)
            act_type = conf_result.response.action.type if (conf_result and conf_result.response.action) else ""
            if act_type == "workspace":
                self._open_workspace_if_needed()
            self.say(
                conf_result.response.speech_output,
                emotion=conf_result.response.emotion or "talk",
                suggestion=resp.alternative_suggestion,
            )
            return

        # Resposta normal
        act_type = resp.action.type if (resp and resp.action) else ""
        if act_type == "workspace":
            self._open_workspace_if_needed()

        self.say(
            resp.speech_output,
            emotion=resp.emotion or "talk",
            suggestion=resp.alternative_suggestion,
        )

    def _open_workspace_if_needed(self) -> None:
        """Abre e traz para o primeiro plano a sub-janela O Grande Sábio."""
        try:
            from ui.workspace_window import WorkspaceWindow
            ws = WorkspaceWindow.get_instance()
            ws.show()
            ws.raise_()
            ws.activateWindow()
        except Exception as exc:
            log.warning(f"Não foi possível abrir sub-janela Workspace: {exc}")

    def _toggle_workspace(self) -> None:
        """Alterna visibilidade da sub-janela O Grande Sábio."""
        try:
            from ui.workspace_window import WorkspaceWindow
            ws = WorkspaceWindow.get_instance()
            if ws.isVisible():
                ws.hide()
            else:
                ws.show()
                ws.raise_()
                ws.activateWindow()
        except Exception as exc:
            log.warning(f"Erro ao alternar Workspace: {exc}")
