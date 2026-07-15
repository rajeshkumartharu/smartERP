"""
apps/academics/urls.py

Wire this into your project's root urls.py, e.g.:
    path('academics/', include('apps.academics.urls')),
"""

from django.urls import path
from . import views

urlpatterns = [
    path('years/', views.academic_year_list, name='academic_year_list'),
    path('levels/', views.level_list, name='level_list'),
    path('classes/', views.class_list, name='class_list'),
    path('sections/', views.section_list, name='section_list'),
    path('faculties/', views.faculty_list, name='faculty_list'),
    path('shifts/', views.shift_list, name='shift_list'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subject-class-mapping/', views.subject_class_mapping_list, name='subject_class_mapping_list'),
    path('teacher-subject-assignment/', views.teacher_subject_assignment_list, name='teacher_subject_assignment_list'),

    # Shared delete endpoint used by every table's row "Delete" button.
    path('<slug:slug>/<int:pk>/delete/', views.academics_delete, name='academics_delete'),

    # Marks Entry & Verification
    path('marks/entry/', views.marks_entry, name='marks_entry'),
    path('marks/verify/', views.marks_verify, name='marks_verify'),
]