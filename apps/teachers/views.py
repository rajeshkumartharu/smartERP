from django.shortcuts import render
from apps.core.decorators import role_required
from django.core.exceptions import ObjectDoesNotExist



@role_required('teacher')
def teacher_dashboard(request):
    try:
        profile = request.user.teacher_profile
    except ObjectDoesNotExist:
        profile = None

    context = {
        'page_title': 'Teacher Dashboard',
        'profile': profile,
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)