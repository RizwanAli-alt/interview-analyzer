"""
tasks.py
Celery async task — runs the full analysis pipeline after a session is submitted.
"""
from celery import shared_task
from django.utils import timezone
import traceback


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def run_analysis(self, session_id: int):
    """
    Full AI analysis pipeline:
    1. Transcribe audio answers (Whisper)
    2. Grade technical correctness (Claude API)
    3. Score confidence (timing + filler analysis)
    4. Score communication (NLP structure analysis)
    5. Build report and save to DB
    """
    from interviews.models import InterviewSession, Answer, AnalysisReport
    from interviews.analyzer.transcriber import transcribe
    from interviews.analyzer.technical import grade_technical
    from interviews.analyzer.confidence import score_confidence
    from interviews.analyzer.communication import score_communication

    try:
        session = InterviewSession.objects.get(pk=session_id)
        session.status = 'analyzing'
        session.save()

        answers = Answer.objects.filter(session=session).select_related('question')

        if not answers.exists():
            session.status = 'failed'
            session.save()
            return {'error': 'No answers found for this session.'}

        tech_scores, conf_scores, comm_scores = [], [], []
        per_answer_feedback = []

        for answer in answers:
            # ── Step 1: Transcribe audio ──────────────────────────────────
            transcript_data = {'text': '', 'segments': [], 'duration': 0.0, 'word_count': 0}

            if answer.audio_file:
                try:
                    transcript_data = transcribe(answer.audio_file.path)
                    answer.transcript = transcript_data['text']
                    answer.save()
                except Exception as e:
                    print(f"[Task] Transcription failed for answer {answer.id}: {e}")

            final_text = answer.transcript or answer.text_input

            # ── Step 2: Technical grading ─────────────────────────────────
            tech = grade_technical(
                question_text=answer.question.text,
                rubric=answer.question.rubric,
                candidate_answer=final_text
            )

            # ── Step 3: Confidence scoring ────────────────────────────────
            conf = score_confidence(
                segments=transcript_data.get('segments', []),
                text=final_text,
                duration=transcript_data.get('duration', 0.0)
            )

            # ── Step 4: Communication scoring ─────────────────────────────
            comm = score_communication(final_text)

            tech_scores.append(tech['score'])
            conf_scores.append(conf['score'])
            comm_scores.append(comm['score'])

            per_answer_feedback.append({
                'question': answer.question.text,
                'transcript': final_text[:500],  # truncate for storage
                'tech': tech,
                'confidence': conf,
                'communication': comm,
            })

        # ── Step 5: Aggregate scores ──────────────────────────────────────
        avg_tech = sum(tech_scores) / len(tech_scores)
        avg_conf = sum(conf_scores) / len(conf_scores)
        avg_comm = sum(comm_scores) / len(comm_scores)

        # Weighted overall: technical 50%, confidence 25%, communication 25%
        overall = (avg_tech * 0.50) + (avg_conf * 0.25) + (avg_comm * 0.25)

        # ── Step 6: Build weak areas & suggestions ────────────────────────
        weak_areas = _build_weak_areas(avg_tech, avg_conf, avg_comm, per_answer_feedback)
        suggestions = _build_suggestions(avg_tech, avg_conf, avg_comm)

        # ── Step 7: Save report ───────────────────────────────────────────
        AnalysisReport.objects.update_or_create(
            session=session,
            defaults={
                'tech_score': round(avg_tech, 1),
                'confidence_score': round(avg_conf, 1),
                'comm_score': round(avg_comm, 1),
                'overall_score': round(overall, 1),
                'weak_areas': weak_areas,
                'suggestions': suggestions,
                'per_answer_feedback': per_answer_feedback,
            }
        )

        session.status = 'done'
        session.completed_at = timezone.now()
        session.save()

        return {
            'session_id': session_id,
            'overall': round(overall, 1),
            'tech': round(avg_tech, 1),
            'confidence': round(avg_conf, 1),
            'communication': round(avg_comm, 1),
        }

    except InterviewSession.DoesNotExist:
        return {'error': f'Session {session_id} not found.'}
    except Exception as e:
        print(f"[Task] Analysis failed: {e}\n{traceback.format_exc()}")
        try:
            session = InterviewSession.objects.get(pk=session_id)
            session.status = 'failed'
            session.save()
        except Exception:
            pass
        raise self.retry(exc=e)


def _build_weak_areas(tech, conf, comm, per_answer) -> list:
    areas = []
    if tech < 55:
        areas.append("Technical knowledge gaps — review core concepts and practice explaining solutions.")
    if conf < 55:
        areas.append("Delivery and confidence — reduce filler words, maintain steady pace.")
    if comm < 55:
        areas.append("Communication structure — organize answers with a clear beginning, middle, and end.")

    # Collect per-answer issues
    for item in per_answer:
        for issue in item.get('confidence', {}).get('issues', []):
            if issue not in areas:
                areas.append(issue)
        for issue in item.get('communication', {}).get('issues', []):
            if issue not in areas:
                areas.append(issue)

    return areas[:6]  # cap at 6 items


def _build_suggestions(tech, conf, comm) -> list:
    suggestions = []

    if tech >= 75:
        suggestions.append("Strong technical answers — keep practicing LeetCode and system design to maintain your edge.")
    elif tech >= 50:
        suggestions.append("Review the concepts you missed and practice explaining them out loud in simple terms.")
    else:
        suggestions.append("Focus on fundamentals — go back to basics for the topics you struggled with and build up from there.")

    if conf >= 75:
        suggestions.append("Great delivery — your confidence came through clearly.")
    elif conf >= 50:
        suggestions.append("Record yourself answering questions and listen back — you'll notice filler words and pacing issues faster this way.")
    else:
        suggestions.append("Practice mock interviews daily. The more you speak out loud, the more natural it becomes. Try the 'pause instead of um' technique.")

    if comm >= 75:
        suggestions.append("Excellent structure — your answers were easy to follow.")
    elif comm >= 50:
        suggestions.append("Use the STAR method (Situation, Task, Action, Result) for behavioral questions and the 'clarify → approach → code → test' pattern for technical ones.")
    else:
        suggestions.append("Before answering, take 5 seconds to mentally outline your response: what's the main point, what's my example, and what's my conclusion?")

    suggestions.append("Schedule regular mock interview sessions — even 2 per week will compound into massive improvement over a month.")

    return suggestions