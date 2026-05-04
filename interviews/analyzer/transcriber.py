"""
transcriber.py
Converts audio files to text using OpenAI Whisper (runs locally, no API key needed).
"""
import os
import whisper
from django.conf import settings

_model = None


def get_model():
    """Load Whisper model once and reuse."""
    global _model
    if _model is None:
        model_name = getattr(settings, 'WHISPER_MODEL', 'base')
        _model = whisper.load_model(model_name)
    return _model


def transcribe(audio_path: str) -> dict:
    """
    Transcribe an audio file.
    Returns:
        {
            'text': str,            # full transcript
            'segments': list,       # word/segment level timing
            'language': str,        # detected language
            'duration': float,      # audio duration in seconds
            'word_count': int,
        }
    """
    if not audio_path or not os.path.exists(audio_path):
        return _empty_result()

    try:
        model = get_model()
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            verbose=False
        )

        text = result.get('text', '').strip()
        segments = result.get('segments', [])

        # Calculate duration from last segment
        duration = 0.0
        if segments:
            duration = segments[-1].get('end', 0.0)

        return {
            'text': text,
            'segments': segments,
            'language': result.get('language', 'en'),
            'duration': duration,
            'word_count': len(text.split()) if text else 0,
        }

    except Exception as e:
        print(f"[Whisper] Transcription error: {e}")
        return _empty_result()


def _empty_result():
    return {
        'text': '',
        'segments': [],
        'language': 'en',
        'duration': 0.0,
        'word_count': 0,
    }