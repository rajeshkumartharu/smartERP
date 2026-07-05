from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/parent', views.parent_dashboard, name='parent_dashboard'),
]
