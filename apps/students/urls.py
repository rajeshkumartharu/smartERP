from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/student', views.student_dashboard, name='student_dashboard'),
]