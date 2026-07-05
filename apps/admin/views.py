from apps.core.decorators import role_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import render
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.parents.models import Parent
from apps.accounts.models import User

@role_required('admin')
def admin_dashboard(request):
    
    context = {
        'page_title': 'Admin Dashboard',
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_parents':  Parent.objects.count(),
        'total_users':    User.objects.count(),
        'recent_users':   User.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'dashboard/admin_dashboard.html', context)