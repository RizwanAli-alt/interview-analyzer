from django.db import models
from django.contrib.auth.models import User
from questions.models import Domain, Question


class InterviewSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('analyzing', 'Analyzing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, null=True)
    level = models.CharField(max_length=10, choices=[
        ('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')
    ], default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} – {self.domain} – {self.created_at:%Y-%m-%d}"

    def get_overall_score(self):
        try:
            return self.report.overall_score
        except AnalysisReport.DoesNotExist:
            return None

    def score_badge_class(self):
        score = self.get_overall_score()
        if score is None:
            return 'secondary'
        if score >= 75:
            return 'success'
        if score >= 50:
            return 'warning'
        return 'danger'


class Answer(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE,
                                related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='answers/audio/', null=True, blank=True)
    transcript = models.TextField(blank=True)
    text_input = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def get_final_text(self):
        return self.transcript or self.text_input

    def __str__(self):
        return f"Answer #{self.order} – {self.question.text[:40]}"


class AnalysisReport(models.Model):
    session = models.OneToOneField(InterviewSession, on_delete=models.CASCADE,
                                   related_name='report')
    tech_score = models.FloatField(default=0)
    confidence_score = models.FloatField(default=0)
    comm_score = models.FloatField(default=0)
    overall_score = models.FloatField(default=0)
    weak_areas = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    per_answer_feedback = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now_add=True)

    def score_label(self, score):
        if score >= 75:
            return 'Excellent'
        if score >= 55:
            return 'Good'
        if score >= 35:
            return 'Needs Work'
        return 'Poor'

    def tech_label(self):
        return self.score_label(self.tech_score)

    def confidence_label(self):
        return self.score_label(self.confidence_score)

    def comm_label(self):
        return self.score_label(self.comm_score)