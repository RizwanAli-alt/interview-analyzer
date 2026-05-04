"""
communication.py
Scores communication quality using basic NLP — no heavy ML model needed.
Checks structure, clarity, vocabulary richness, and answer organization.
"""
import re


# Words that signal structure and good communication
STRUCTURE_SIGNALS = [
    r'\bfirst(ly)?\b', r'\bsecond(ly)?\b', r'\bthird(ly)?\b',
    r'\bfinally\b', r'\bin conclusion\b', r'\bto summarize\b',
    r'\bfor example\b', r'\bfor instance\b', r'\bsuch as\b',
    r'\bhowever\b', r'\btherefore\b', r'\bmoreover\b',
    r'\bin addition\b', r'\bfurthermore\b', r'\bon the other hand\b',
    r'\bto begin\b', r'\bin summary\b', r'\boverall\b',
]

# Weak/vague language that hurts clarity
VAGUE_WORDS = [
    'stuff', 'things', 'good', 'bad', 'nice', 'very', 'really',
    'pretty much', 'kind of', 'sort of', 'a lot', 'many things',
]

IDEAL_SENTENCE_LENGTH = (10, 25)   # words per sentence
MIN_WORDS = 30
IDEAL_WORDS = 80


def score_communication(text: str) -> dict:
    """
    Scores clarity and structure of a text answer.

    Returns:
        {
            'score': float,             # 0-100
            'word_count': int,
            'sentence_count': int,
            'avg_sentence_length': float,
            'structure_signals': int,   # transition words found
            'vague_word_count': int,
            'vocabulary_richness': float, # unique words / total words
            'feedback': str,
            'issues': list,
        }
    """
    if not text or not text.strip():
        return _empty_result("No answer text to analyze.")

    text = text.strip()
    text_lower = text.lower()

    # ── 1. Basic metrics ─────────────────────────────────────────────────────
    words = text.split()
    word_count = len(words)

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)

    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    # ── 2. Structure signals ─────────────────────────────────────────────────
    structure_count = 0
    for pattern in STRUCTURE_SIGNALS:
        if re.search(pattern, text_lower):
            structure_count += 1

    # ── 3. Vague language ────────────────────────────────────────────────────
    vague_count = 0
    for vague in VAGUE_WORDS:
        pattern = r'\b' + re.escape(vague) + r'\b'
        vague_count += len(re.findall(pattern, text_lower))

    # ── 4. Vocabulary richness ───────────────────────────────────────────────
    unique_words = set(w.lower().strip('.,!?;:') for w in words)
    vocab_richness = len(unique_words) / word_count if word_count > 0 else 0

    # ── 5. Score calculation ─────────────────────────────────────────────────
    score = 100.0
    issues = []

    # Length check
    if word_count < MIN_WORDS:
        penalty = min(35, (MIN_WORDS - word_count) * 1.2)
        score -= penalty
        issues.append(f"Answer is too brief ({word_count} words). Aim for at least {IDEAL_WORDS} words.")
    elif word_count < IDEAL_WORDS:
        score -= 10
        issues.append(f"Answer could be more detailed ({word_count} words).")

    # Structure
    if structure_count == 0:
        score -= 20
        issues.append("No structural language detected. Use 'first', 'for example', 'however' to organize thoughts.")
    elif structure_count == 1:
        score -= 10
        issues.append("Limited structure. Add more transition words to improve flow.")

    # Sentence length
    if avg_sentence_length > 35:
        score -= 15
        issues.append("Sentences are very long — break them up for clarity.")
    elif avg_sentence_length < 5 and sentence_count > 2:
        score -= 10
        issues.append("Sentences are very short — add more detail and explanation.")

    # Vague language
    vague_ratio = vague_count / word_count if word_count > 0 else 0
    if vague_ratio > 0.08:
        score -= 15
        issues.append(f"Too much vague language ('{', '.join(VAGUE_WORDS[:3])}...'). Be more specific.")
    elif vague_ratio > 0.04:
        score -= 7
        issues.append("Some vague wording. Try to be more precise and specific.")

    # Vocabulary richness
    if vocab_richness < 0.4:
        score -= 10
        issues.append("Repetitive vocabulary — vary your word choice.")

    score = max(0, min(100, score))

    # ── 6. Feedback ──────────────────────────────────────────────────────────
    if score >= 80:
        feedback = "Well-structured, clear answer with good use of examples and transitions."
    elif score >= 60:
        feedback = "Reasonably clear answer but could use more structure or detail."
    elif score >= 40:
        feedback = "Communication needs improvement — focus on structure and clarity."
    else:
        feedback = "Answer is difficult to follow. Practice organizing your thoughts before speaking."

    return {
        'score': round(score, 1),
        'word_count': word_count,
        'sentence_count': sentence_count,
        'avg_sentence_length': round(avg_sentence_length, 1),
        'structure_signals': structure_count,
        'vague_word_count': vague_count,
        'vocabulary_richness': round(vocab_richness, 2),
        'feedback': feedback,
        'issues': issues,
    }


def _empty_result(reason: str):
    return {
        'score': 0.0,
        'word_count': 0,
        'sentence_count': 0,
        'avg_sentence_length': 0.0,
        'structure_signals': 0,
        'vague_word_count': 0,
        'vocabulary_richness': 0.0,
        'feedback': reason,
        'issues': [reason],
    }