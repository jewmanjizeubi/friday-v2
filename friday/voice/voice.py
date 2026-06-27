"""
Friday — Voix
TTS via Piper local, STT via Whisper local
"""

import os
import io
import subprocess
import tempfile
import whisper
from config.settings import settings

# Chargement Whisper une seule fois au démarrage
_whisper_model = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model(settings.WHISPER_MODEL)
    return _whisper_model


def text_to_speech(text: str) -> bytes:
    """Génère l'audio via Piper TTS local"""
    try:
        process = subprocess.run(
            [
                "piper",
                "--model", settings.PIPER_MODEL,
                "--output-raw"
            ],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30
        )
        if process.returncode != 0:
            raise RuntimeError(f"Piper error: {process.stderr.decode()}")

        # Conversion raw PCM → WAV
        raw_audio = process.stdout
        import wave
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(raw_audio)
        return wav_buffer.getvalue()

    except Exception as e:
        print(f"[TTS] Erreur Piper: {e}")
        raise


def speech_to_text(audio_bytes: bytes) -> str:
    """Transcrit l'audio via Whisper local"""
    try:
        model = _get_whisper()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        result = model.transcribe(tmp_path, language="fr")
        os.unlink(tmp_path)
        return result.get("text", "").strip()
    except Exception as e:
        print(f"[STT] Erreur Whisper: {e}")
        return ""
