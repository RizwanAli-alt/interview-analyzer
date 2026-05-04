from django.urls import path
from . import views

urlpatterns = [
    path('', views.question_bank, name='question_bank'),
]