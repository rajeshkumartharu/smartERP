from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/teacher', views.teacher_dashboard, name='teacher_dashboard'),
]
