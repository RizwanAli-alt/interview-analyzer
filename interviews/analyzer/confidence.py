"""
confidence.py
Scores confidence from audio timing data (Whisper segments) and text analysis.
No extra ML model needed — uses Whisper's word timestamps.
"""
import re


FILLER_WORDS = {
    'um', 'uh', 'er', 'ah', 'like', 'you know', 'basically', 'literally',
    'actually', 'sort of', 'kind of', 'i mean', 'right', 'so yeah', 'hmm'
}

# Ideal speech: 120-160 words per minute
IDEAL_WPM_MIN = 110
IDEAL_WPM_MAX = 170

# Acceptable pause ratio (pauses / total duration)
MAX_PAUSE_RATIO = 0.35


def score_confidence(segments: list, text: str, duration: float) -> dict:
    """
    Analyzes confidence from Whisper segments + text.

    Args:
        segments: Whisper segment list with 'start', 'end', 'text'
        text: Full transcript text
        duration: Total audio duration in seconds

    Returns:
        {
            'score': float,         # 0-100
            'wpm': float,           # words per minute
            'filler_count': int,
            'filler_ratio': float,  # fillers per 100 words
            'pause_ratio': float,   # silence / total time
            'feedback': str,
            'issues': list,
        }
    """
    if not text or not text.strip():
        return _empty_result("No speech detected.")

    words = text.split()
    word_count = len(words)

    # ── 1. Words per minute ──────────────────────────────────────────────────
    wpm = 0.0
    if duration and duration > 0:
        wpm = (word_count / duration) * 60

    # ── 2. Pause analysis from segments ─────────────────────────────────────
    pause_ratio = 0.0
    if segments and duration > 0:
        speaking_time = sum(
            seg.get('end', 0) - seg.get('start', 0)
            for seg in segments
        )
        silence_time = max(0, duration - speaking_time)
        pause_ratio = silence_time / duration

    # ── 3. Filler word count ─────────────────────────────────────────────────
    text_lower = text.lower()
    filler_count = 0
    for filler in FILLER_WORDS:
        # Match whole word/phrase
        pattern = r'\b' + re.escape(filler) + r'\b'
        filler_count += len(re.findall(pattern, text_lower))

    filler_ratio = (filler_count / word_count * 100) if word_count > 0 else 0

    # ── 4. Score calculation ─────────────────────────────────────────────────
    score = 100.0
    issues = []

    # WPM penalty
    if wpm > 0:
        if wpm < IDEAL_WPM_MIN:
            penalty = min(25, (IDEAL_WPM_MIN - wpm) * 0.5)
            score -= penalty
            issues.append(f"Speaking too slowly ({wpm:.0f} wpm). Aim for {IDEAL_WPM_MIN}-{IDEAL_WPM_MAX} wpm.")
        elif wpm > IDEAL_WPM_MAX:
            penalty = min(25, (wpm - IDEAL_WPM_MAX) * 0.4)
            score -= penalty
            issues.append(f"Speaking too fast ({wpm:.0f} wpm). Slow down slightly.")
    else:
        # Text-only input, skip WPM
        score -= 10

    # Pause penalty
    if pause_ratio > MAX_PAUSE_RATIO:
        penalty = min(30, (pause_ratio - MAX_PAUSE_RATIO) * 80)
        score -= penalty
        issues.append(f"Too many/long pauses ({pause_ratio:.0%} silence). Work on fluency.")

    # Filler word penalty
    if filler_ratio > 5:
        penalty = min(30, filler_ratio * 1.5)
        score -= penalty
        issues.append(f"High filler word usage ({filler_count} fillers). Practice reducing 'um', 'uh', 'like'.")
    elif filler_ratio > 2:
        score -= 10
        issues.append(f"Some filler words detected ({filler_count}). Minor issue.")

    score = max(0, min(100, score))

    # ── 5. Feedback summary ──────────────────────────────────────────────────
    if score >= 80:
        feedback = "Strong delivery — confident, clear pace, minimal fillers."
    elif score >= 60:
        feedback = "Decent delivery with some areas to improve."
    elif score >= 40:
        feedback = "Noticeable issues with pace, pauses, or filler words."
    else:
        feedback = "Delivery needs significant work — practice out loud regularly."

    return {
        'score': round(score, 1),
        'wpm': round(wpm, 1),
        'filler_count': filler_count,
        'filler_ratio': round(filler_ratio, 1),
        'pause_ratio': round(pause_ratio, 3),
        'feedback': feedback,
        'issues': issues,
    }


def _empty_result(reason: str):
    return {
        'score': 0.0,
        'wpm': 0.0,
        'filler_count': 0,
        'filler_ratio': 0.0,
        'pause_ratio': 0.0,
        'feedback': reason,
        'issues': [reason],
    }