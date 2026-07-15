from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    path('students/', views.student_list, name='student_list'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/update/', views.student_update, name='student_update'),
    path('students/<int:pk>/toggle-active/', views.student_toggle_active, name='student_toggle_active'),
]