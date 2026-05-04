from django.contrib import admin
from .models import Domain, Question


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['domain', 'level', 'text', 'is_active']
    list_filter = ['domain', 'level', 'is_active']
    search_fields = ['text']