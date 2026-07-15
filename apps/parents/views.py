from apps.core.decorators import role_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import render

@role_required('parent')
def parent_dashboard(request):
    try:
        profile = request.user.parent_profile
        children = profile.students.select_related('user', 'school_class', 'section', 'level').all()
    except ObjectDoesNotExist:
        profile = None
        children = []

    context = {
        'page_title': 'Parent Dashboard',
        'profile': profile,
        'children': children,
    }
    return render(request, 'dashboard/parent_dashboard.html', context)