from django.shortcuts import render
from apps.core.decorators import role_required
from django.core.exceptions import ObjectDoesNotExist
from apps.academics.models import TeacherSubjectAssignment, Assessment, AcademicYear


@role_required('teacher')
def teacher_dashboard(request):
    try:
        profile = request.user.teacher_profile
    except ObjectDoesNotExist:
        profile = None

    assigned_classes = []
    created_assessments = []
    active_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()

    if profile and active_year:
        assigned_classes = TeacherSubjectAssignment.objects.filter(
            teacher=profile,
            academic_year=active_year
        ).select_related('school_class', 'section', 'subject')
        
        created_assessments = Assessment.objects.filter(
            created_by=profile,
            academic_year=active_year
        ).select_related('school_class', 'section', 'subject', 'term')

    context = {
        'page_title': 'Teacher Dashboard',
        'profile': profile,
        'assigned_classes': assigned_classes,
        'created_assessments': created_assessments,
        'active_year': active_year,
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)