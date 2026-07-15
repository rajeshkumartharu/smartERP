from django.shortcuts import render
from apps.core.decorators import role_required
from django.core.exceptions import ObjectDoesNotExist


@role_required('student')
def student_dashboard(request):
    try:
        profile = request.user.student_profile
    except ObjectDoesNotExist:
        profile = None

    context = {
        'page_title': 'Student Dashboard',
        'profile': profile,
    }
    return render(request, 'dashboard/student_dashboard.html', context)

