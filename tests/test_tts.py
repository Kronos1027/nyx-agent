"""Testes para o subsistema de Text-To-Speech (TTS) da Nyx"""

from audio.tts import TextToSpeech


def test_tts_clean_text():
    tts = TextToSpeech(enabled=False)
    raw = "Olá! [Ação realizada com sucesso](file:///test.txt) **Importante:** teste `código` aqui. 🚀👍"
    cleaned = tts._clean_text_for_speech(raw)
    assert "file:///" not in cleaned
    assert "código" not in cleaned
    assert "Importante:" in cleaned
    assert "teste aqui." in cleaned


def test_tts_speak_disabled():
    tts = TextToSpeech(enabled=False)
    # Não deve gerar exceção mesmo quando desabilitado
    tts.speak("Teste de fala desabilitada.")
    assert tts.enabled is False


def test_tts_init():
    tts = TextToSpeech()
    assert tts.rate == 1
    assert tts.enabled is True
