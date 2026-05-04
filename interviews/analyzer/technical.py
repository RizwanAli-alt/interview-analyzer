"""
technical.py
Grades the technical correctness of an answer using the Claude API.
Compares candidate's answer against the question rubric.
"""
import json
import anthropic
from django.conf import settings


def grade_technical(question_text: str, rubric: str, candidate_answer: str) -> dict:
    """
    Uses Claude to grade the technical quality of an answer.

    Returns:
        {
            'score': float,          # 0-100
            'correct_points': list,  # what they got right
            'missing_points': list,  # what they missed
            'feedback': str,         # 1-2 sentence summary
        }
    """
    if not candidate_answer or len(candidate_answer.strip()) < 10:
        return _empty_result("Answer too short to evaluate.")

    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key or api_key == "your_api_key":
        return _fallback_result(candidate_answer)

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are a strict but fair technical interview evaluator.

INTERVIEW QUESTION:
{question_text}

IDEAL ANSWER RUBRIC (key points a good answer must cover):
{rubric}

CANDIDATE'S ANSWER:
{candidate_answer}

Evaluate the candidate's answer against the rubric. Respond ONLY with a JSON object in this exact format:
{{
    "score": <integer 0-100>,
    "correct_points": ["point 1", "point 2"],
    "missing_points": ["missed point 1", "missed point 2"],
    "feedback": "One or two sentences summarizing the technical quality."
}}

Scoring guide:
- 85-100: Covers all rubric points with clear explanation
- 65-84: Covers most points, minor gaps
- 40-64: Covers some points, notable gaps
- 20-39: Partially understands, significant gaps
- 0-19: Incorrect or completely off-topic

Return ONLY the JSON, no other text."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        result = json.loads(response_text)
        return {
            'score': float(max(0, min(100, result.get('score', 50)))),
            'correct_points': result.get('correct_points', []),
            'missing_points': result.get('missing_points', []),
            'feedback': result.get('feedback', ''),
        }

    except json.JSONDecodeError:
        return _fallback_result(candidate_answer)
    except Exception as e:
        print(f"[Technical] Grading error: {e}")
        return _fallback_result(candidate_answer)


def _fallback_result(answer: str):
    """Simple keyword-based fallback if API is unavailable."""
    word_count = len(answer.split())
    # Rough heuristic: longer, detailed answers score higher
    score = min(60, max(10, word_count * 1.5))
    return {
        'score': score,
        'correct_points': ['Answer provided'],
        'missing_points': ['Could not perform AI evaluation'],
        'feedback': 'AI grading unavailable. Score estimated from answer length.',
    }


def _empty_result(reason: str):
    return {
        'score': 0.0,
        'correct_points': [],
        'missing_points': ['No answer provided'],
        'feedback': reason,
    }