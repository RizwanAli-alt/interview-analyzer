from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('start/', views.start_session, name='start_session'),
    path('session/<int:pk>/', views.session_detail, name='session_detail'),
    path('session/<int:session_pk>/submit/<int:question_pk>/',
         views.submit_answer, name='submit_answer'),
    path('session/<int:session_pk>/finish/',
         views.finalize_session, name='finalize_session'),
    path('report/<int:pk>/', views.report, name='report'),
    path('api/session/<int:pk>/status/', views.session_status, name='session_status'),
    path('history/', views.history, name='history'),
]