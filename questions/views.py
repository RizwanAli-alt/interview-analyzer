from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Domain, Question


@login_required
def question_bank(request):
    domains = Domain.objects.prefetch_related('questions').all()
    return render(request, 'questions/bank.html', {'domains': domains})