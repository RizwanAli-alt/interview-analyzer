import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Avg

from .models import InterviewSession, Answer, AnalysisReport
from .forms import StartSessionForm, AnswerForm
from .tasks import run_analysis
from questions.models import Question, Domain


# ── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    sessions = InterviewSession.objects.filter(
        user=request.user
    ).select_related('domain', 'report')

    # Stats for the dashboard cards
    done_sessions = sessions.filter(status='done')
    stats = {
        'total': sessions.count(),
        'done': done_sessions.count(),
        'avg_score': done_sessions.aggregate(
            avg=Avg('report__overall_score')
        )['avg'],
        'best_score': done_sessions.aggregate(
            best=Avg('report__overall_score')
        )['best'],
    }
    if stats['avg_score']:
        stats['avg_score'] = round(stats['avg_score'], 1)

    domains = Domain.objects.all()
    return render(request, 'interviews/dashboard.html', {
        'sessions': sessions[:10],
        'stats': stats,
        'domains': domains,
    })


# ── Start session ────────────────────────────────────────────────────────────

@login_required
def start_session(request):
    if request.method == 'POST':
        form = StartSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.status = 'in_progress'
            session.save()
            return redirect('session_detail', pk=session.pk)
    else:
        form = StartSessionForm()

    domains = Domain.objects.prefetch_related('questions').all()
    return render(request, 'interviews/start.html', {
        'form': form,
        'domains': domains,
    })


# ── Session (answering questions) ────────────────────────────────────────────

@login_required
def session_detail(request, pk):
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)

    if session.status == 'done':
        return redirect('report', pk=pk)

    # Get questions for this domain + level
    questions = list(
        Question.objects.filter(
            domain=session.domain,
            level=session.level,
            is_active=True
        )
    )

    # How many have been answered already?
    answered_ids = set(
        Answer.objects.filter(session=session).values_list('question_id', flat=True)
    )
    remaining = [q for q in questions if q.id not in answered_ids]
    answered_count = len(questions) - len(remaining)

    current_question = remaining[0] if remaining else None

    return render(request, 'interviews/session.html', {
        'session': session,
        'current_question': current_question,
        'answered_count': answered_count,
        'total_questions': len(questions),
        'progress_pct': int(answered_count / len(questions) * 100) if questions else 0,
        'form': AnswerForm(),
    })


# ── Submit answer ────────────────────────────────────────────────────────────

@login_required
@require_POST
def submit_answer(request, session_pk, question_pk):
    session = get_object_or_404(InterviewSession, pk=session_pk, user=request.user)
    question = get_object_or_404(Question, pk=question_pk)

    # Prevent duplicate answers
    if Answer.objects.filter(session=session, question=question).exists():
        return redirect('session_detail', pk=session_pk)

    answered_count = Answer.objects.filter(session=session).count()

    answer = Answer(
        session=session,
        question=question,
        order=answered_count + 1,
    )

    # Audio or text
    if 'audio_file' in request.FILES:
        answer.audio_file = request.FILES['audio_file']
    answer.text_input = request.POST.get('text_input', '').strip()

    if not answer.audio_file and not answer.text_input:
        messages.error(request, 'Please provide an answer — either record audio or type your response.')
        return redirect('session_detail', pk=session_pk)

    answer.save()
    return redirect('session_detail', pk=session_pk)


# ── Finalize session → fire analysis ─────────────────────────────────────────

@login_required
@require_POST
def finalize_session(request, session_pk):
    session = get_object_or_404(InterviewSession, pk=session_pk, user=request.user)

    answer_count = Answer.objects.filter(session=session).count()
    if answer_count == 0:
        messages.error(request, 'Answer at least one question before finishing.')
        return redirect('session_detail', pk=session_pk)

    session.status = 'analyzing'
    session.save()

    # Fire async Celery task
    run_analysis.delay(session.pk)

    messages.success(request, 'Analysis started! Results will appear in a few moments.')
    return redirect('report', pk=session.pk)


# ── Report ────────────────────────────────────────────────────────────────────

@login_required
def report(request, pk):
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
    report_obj = AnalysisReport.objects.filter(session=session).first()

    return render(request, 'interviews/report.html', {
        'session': session,
        'report': report_obj,
    })


# ── Status API (for polling) ──────────────────────────────────────────────────

@login_required
def session_status(request, pk):
    session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
    return JsonResponse({'status': session.status})


# ── History ───────────────────────────────────────────────────────────────────

@login_required
def history(request):
    sessions = InterviewSession.objects.filter(
        user=request.user, status='done'
    ).select_related('domain', 'report')
    return render(request, 'interviews/history.html', {'sessions': sessions})