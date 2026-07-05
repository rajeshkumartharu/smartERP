from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────────────────────
    path('',                  views.login_view,          name='login'),
    path('logout/',           views.logout_view,         name='logout'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),
    path('register/parent/', views.register_parent, name='register_parent'),

    path('change-password/',  views.change_password_view, name='change_password'),

    # ── Dashboard dispatcher ─────────────────────────────────────────────────
    path('dashboard/',        views.dashboard,            name='dashboard'),


    # ── Admin user management ─────────────────────────────────────────────────
    path('users/',                              views.user_list_view,      name='user_list'),
    path('users/<int:user_id>/toggle-status/',  views.toggle_user_status,  name='toggle_user_status'),
    path('users/<int:user_id>/reset-password/', views.reset_user_password, name='reset_user_password'),
]
