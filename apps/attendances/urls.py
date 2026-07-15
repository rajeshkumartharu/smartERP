from django.urls import path
from . import views

urlpatterns = [
    path('teacher/take/', views.teacher_take_attendance, name='teacher_take_attendance'),
    path('teacher/history/', views.teacher_attendance_history, name='teacher_attendance_history'),

    path('admin/list/', views.admin_attendance_list, name='admin_attendance_list'),

    path('student/report/', views.student_attendance_report, name='student_attendance_report'),
    path('parent/report/', views.parent_child_attendance_report, name='parent_child_attendance_report'),
]