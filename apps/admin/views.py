from apps.core.decorators import role_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.parents.models import Parent
from apps.accounts.models import User
from apps.students.studentforms import StudentForm
from apps.academics.models import AcademicYear, StudentEvaluation, SchoolClass, Section, Subject, Exam, Assessment

@role_required('admin')
def admin_dashboard(request):
    import json
    from django.utils import timezone
    from django.db.models import Count
    from apps.academics.models import AcademicYear, StudentEvaluation, SchoolClass, Section, Subject, Exam, Assessment
    from apps.students.models import Student
    from apps.teachers.models import Teacher
    from apps.parents.models import Parent
    from apps.accounts.models import User
    from apps.attendances.models import AttendanceRecord, AttendanceSession
    from apps.core.utils import get_class_performance, get_grade_distribution, get_attendance_trend, get_admission_trend, get_dashboard_alerts

    active_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()

    class_perf = []
    grade_dist = {}
    att_trend = []
    adm_trend = []
    alerts = {}
    
    excellent_students = []
    good_students = []
    average_students = []
    at_risk_students = []
    critical_students = []
    below_attendance = []
    declining_performance = []
    requiring_counselling = []
    
    today = timezone.localdate()
    today_records = AttendanceRecord.objects.filter(attendance_session__date=today)
    today_present = today_records.filter(status='present').count()
    today_absent = today_records.filter(status='absent').count()
    today_late = today_records.filter(status='late').count()
    today_leave = today_records.filter(status='leave').count()
    
    total_today = today_records.count()
    attendance_percentage = round((today_present + today_late) / total_today * 100, 1) if total_today > 0 else 100.0
    pending_attendance = SchoolClass.objects.count() - AttendanceSession.objects.filter(date=today).values('school_class').distinct().count()
    
    active_teachers = Teacher.objects.filter(status='active').count()
    teachers_on_leave = Teacher.objects.filter(status='on_leave').count()
    

    if active_year:
        class_perf = get_class_performance(active_year)
        grade_dist = get_grade_distribution(active_year)
        att_trend = get_attendance_trend(active_year)
        adm_trend = get_admission_trend()
        alerts = get_dashboard_alerts(active_year)
        
        evals = StudentEvaluation.objects.filter(academic_year=active_year)
        excellent_students = evals.filter(status='excellent')
        good_students = evals.filter(status='good')
        average_students = evals.filter(status='average')
        at_risk_students = evals.filter(status='at_risk')
        critical_students = evals.filter(status='critical')
        below_attendance = evals.filter(attendance_percentage__lt=75.0)
        declining_performance = evals.filter(performance_trend='declining')
        requiring_counselling = evals.filter(status__in=['at_risk', 'critical'])

    attendance_pending_alerts = alerts.get('attendance_pending', 0)
    low_performance_alerts = alerts.get('at_risk_count', 0)
    upcoming_exams = Exam.objects.filter(start_date__gte=today, start_date__lte=today + timezone.timedelta(days=7))
    teachers_not_assigned = Teacher.objects.filter(assignments__isnull=True).distinct().count()
    missing_results = Assessment.objects.filter(marks_entries__isnull=True).distinct().count()
    
    class_att_list = []
    for cls in class_perf:
        class_att_list.append({
            'name': cls['name'],
            'att_pct': cls['att_pct']
        })
    class_att_list.sort(key=lambda x: x['att_pct'], reverse=True)
    top_attendance_class = class_att_list[0] if class_att_list else None
    lowest_attendance_class = class_att_list[-1] if class_att_list else None
    
    highest_performing_student = StudentEvaluation.objects.filter(academic_year=active_year).select_related('student', 'student__user').order_by('-average_marks').first()
    recent_students = Student.objects.select_related('user', 'school_class', 'section').order_by('-admission_date')[:5]
    # recent_notices = Notice.objects.select_related('published_by').order_by('-published_date')[:5]
    # recent_activities = ActivityLog.objects.select_related('user').order_by('-timestamp')[:5]

    hour = timezone.localtime().hour
    if hour < 12:
        greeting = "Morning"
    elif hour < 18:
        greeting = "Afternoon"
    else:
        greeting = "Evening"

    context = {
        'page_title': 'Admin Dashboard',
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_parents': Parent.objects.count(),
        'total_users': User.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        
        'active_year': active_year,
        'class_performance': class_perf,
        'class_performance_json': json.dumps(class_perf),
        'grade_distribution': json.dumps(grade_dist),
        'attendance_trend': json.dumps(att_trend),
        'admission_trend': json.dumps(adm_trend),
        
        'excellent_students': excellent_students,
        'good_students': good_students,
        'average_students': average_students,
        'at_risk_students': at_risk_students,
        'critical_students': critical_students,
        'below_attendance': below_attendance,
        'declining_performance': declining_performance,
        'requiring_counselling': requiring_counselling,
        
        'today_present': today_present,
        'today_absent': today_absent,
        'today_late': today_late,
        'today_leave': today_leave,
        'pending_attendance': pending_attendance,
        'attendance_percentage': attendance_percentage,
        'active_teachers': active_teachers,
        'teachers_on_leave': teachers_on_leave,
        
        'attendance_pending_alerts': attendance_pending_alerts,
        'low_performance_alerts': low_performance_alerts,
        'upcoming_exams': upcoming_exams,
        'teachers_not_assigned': teachers_not_assigned,
        'missing_results': missing_results,
        
        'top_attendance_class': top_attendance_class,
        'lowest_attendance_class': lowest_attendance_class,
        'highest_performing_student': highest_performing_student,
        'recent_students': recent_students,
        # 'recent_notices': recent_notices,
        # 'recent_activities': recent_activities,
        
        'greeting': greeting,
        'school_name': 'SmartSchool ERP',
        'current_session': active_year.name if active_year else 'N/A',
        'current_date': timezone.now(),
        'current_time': timezone.now(),
        'current_academic_year': active_year.name if active_year else 'N/A',
        'current_semester': 'First Term',
        'system_version': 'v1.2.0',
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@role_required('admin')
def student_list(request):
    query = request.GET.get('q', '').strip()

    students = Student.objects.select_related('user').all().order_by('-id')

    if query:
        students = students.filter(
            Q(student_id__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query)
        )

    context = {
        'page_title': 'All Students',
        'students': students,
        'query': query,
    }
    return render(request, 'accounts/student_list.html', context)


@role_required('admin')
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related('user'), pk=pk)
    return render(request, 'accounts/student_detail.html', {
        'student': student,
        'page_title': f'Student - {student.student_id}'
    })


@role_required('admin')
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f'Student {student.student_id} updated successfully.')
            return redirect('student_detail', pk=student.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(instance=student)

    return render(request, 'accounts/student_update.html', {
        'form': form,
        'student': student,
        'page_title': f'Update Student - {student.student_id}',
    })


@role_required('admin')
def student_toggle_active(request, pk):
    student = get_object_or_404(Student, pk=pk)

    current = student.status

    if current == 'active':
        student.status = 'inactive'
        message = f'Student {student.student_id} has been deactivated.'
    elif current == 'inactive':
        student.status = 'active'
        message = f'Student {student.student_id} has been activated.'
    elif current in ['passed_out', 'transferred']:
        messages.warning(
            request,
            f'Cannot activate a student with status "{current}". Please update status manually if needed.'
        )
        return redirect('student_detail', pk=student.pk)
    else:
        student.status = 'active'
        message = f'Student {student.student_id} status set to active.'

    student.save()
    messages.success(request, message)
    return redirect('student_detail', pk=student.pk)