from django.contrib import admin
from .models import InterviewSession, Answer, AnalysisReport


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'domain', 'level', 'status', 'created_at']
    list_filter = ['status', 'domain', 'level']
    search_fields = ['user__username']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'order', 'submitted_at']


@admin.register(AnalysisReport)
class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ['session', 'overall_score', 'tech_score', 'confidence_score', 'comm_score', 'generated_at']
    readonly_fields = ['weak_areas', 'suggestions', 'per_answer_feedback']