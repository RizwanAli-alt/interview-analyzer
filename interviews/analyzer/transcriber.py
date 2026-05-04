from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple, Optional

from faster_whisper import WhisperModel


@dataclass
class WordToken:
    word: str
    start: float
    end: float


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    words: List[WordToken]


@lru_cache(maxsize=2)
def get_model(
    model_name: str = "base",
    device: str = "cpu",
    compute_type: str = "int8",
) -> WhisperModel:
    """
    Lazy-load + cache WhisperModel.
    compute_type=int8 is a good CPU default.
    """
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def transcribe_audio(
    audio_path: str,
    model_name: str = "base",
    language: Optional[str] = None,
) -> Tuple[str, List[TranscriptSegment], dict]:
    """
    Returns:
      full_text: concatenated transcript
      segments: list of TranscriptSegment including word timestamps (if available)
      meta: info dict (language, duration, etc.)
    """
    model = get_model(model_name=model_name)

    segments_iter, info = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        vad_filter=True,  # helps on noisy recordings
    )

    segments: List[TranscriptSegment] = []
    texts: List[str] = []

    for seg in segments_iter:
        seg_text = (seg.text or "").strip()
        if seg_text:
            texts.append(seg_text)

        words: List[WordToken] = []
        if getattr(seg, "words", None):
            for w in seg.words:
                if not w:
                    continue
                words.append(WordToken(word=w.word, start=float(w.start), end=float(w.end)))

        segments.append(
            TranscriptSegment(
                start=float(seg.start),
                end=float(seg.end),
                text=seg_text,
                words=words,
            )
        )

    full_text = " ".join(texts).strip()

    meta = {
        "language": getattr(info, "language", None),
        "language_probability": getattr(info, "language_probability", None),
        "duration": getattr(info, "duration", None),
    }
    return full_text, segments, meta