"""Nyx — audio/tts.py (Síntese de Voz Local e Assíncrona com Windows SAPI5)

Utiliza a voz nativa em português brasileiro (Microsoft Maria Desktop)
com execução em thread desacoplada para não bloquear a interface PyQt6.
"""

from __future__ import annotations

import logging
import re
import sys
import threading

log = logging.getLogger(__name__)


class TextToSpeech:
    """Motor de síntese de voz nativo do Windows (SAPI5)."""

    def __init__(self, enabled: bool = True, voice_name: str | None = None, rate: int = 1) -> None:
        self.enabled = enabled
        self.rate = rate
        self._voice_name = voice_name
        self._lock = threading.Lock()
        self._current_thread: threading.Thread | None = None

    def _clean_text_for_speech(self, text: str) -> str:
        """Remove código, links, emojis e símbolos para pronúncia natural."""
        # Remove blocos de código
        t = re.sub(r"```[\s\S]*?```", "", text)
        # Transforma links markdown [texto](url) apenas no texto legível
        t = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", t)
        # Remove código inline
        t = re.sub(r"`[^`]*`", "", t)
        # Remove URLs e URIs
        t = re.sub(r"(https?://\S+|file:///\S+)", "", t)
        # Remove emojis (intervalo unicode suplementar)
        t = re.sub(r"[\U00010000-\U0010ffff]", "", t)
        # Remove pontuação markdown e delimitadores
        t = re.sub(r"[\*\_#\(\)\{\}\<\>\|\\]", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def speak(self, text: str, wait: bool = False) -> None:
        """Sintetiza a fala do texto de forma assíncrona por padrão."""
        if not self.enabled or not text or sys.platform != "win32":
            return

        clean = self._clean_text_for_speech(text)
        if not clean:
            return

        def _worker():
            with self._lock:
                try:
                    import pythoncom
                    import win32com.client

                    pythoncom.CoInitialize()
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Rate = self.rate

                    # Seleciona voz em português (Maria) se disponível
                    voices = speaker.GetVoices()
                    for i in range(voices.Count):
                        desc = voices.Item(i).GetDescription()
                        if "Portuguese" in desc or "Maria" in desc or "Brazil" in desc:
                            speaker.Voice = voices.Item(i)
                            break

                    speaker.Speak(clean)
                except Exception as exc:
                    log.warning(f"Erro no TTS (SAPI5): {exc}")
                finally:
                    try:
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        th = threading.Thread(target=_worker, daemon=True)
        th.start()
        if wait:
            th.join()
