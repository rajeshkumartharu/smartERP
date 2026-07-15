import json
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
from django.utils import timezone
from apps.attendances.models import AttendanceRecord, AttendanceSession



@role_required("admin")
def admin_dashboard(request):
    active_year = (
        AcademicYear.objects.filter(is_current=True).first()
        or AcademicYear.objects.order_by("-start_date").first()
    )

    today = timezone.localdate()

    # ---------------- Attendance ---------------- #

    today_records = AttendanceRecord.objects.filter(
        attendance_session__date=today
    )

    today_present = today_records.filter(status="present").count()
    today_absent = today_records.filter(status="absent").count()
    today_late = today_records.filter(status="late").count()
    today_leave = today_records.filter(status="leave").count()

    total_today = today_records.count()

    attendance_percentage = (
        round(((today_present + today_late) / total_today) * 100, 1)
        if total_today
        else 0
    )

    pending_attendance = (
        SchoolClass.objects.count()
        - AttendanceSession.objects.filter(date=today)
        .values("school_class")
        .distinct()
        .count()
    )

    # ---------------- Teacher Statistics ---------------- #

    active_teachers = Teacher.objects.filter(status="active").count()
    teachers_on_leave = Teacher.objects.filter(status="on_leave").count()

    # ---------------- Student Evaluation ---------------- #

    excellent_students = StudentEvaluation.objects.none()
    good_students = StudentEvaluation.objects.none()
    average_students = StudentEvaluation.objects.none()
    at_risk_students = StudentEvaluation.objects.none()
    critical_students = StudentEvaluation.objects.none()
    below_attendance = StudentEvaluation.objects.none()
    declining_performance = StudentEvaluation.objects.none()
    requiring_counselling = StudentEvaluation.objects.none()

    if active_year:
        evaluations = StudentEvaluation.objects.filter(
            academic_year=active_year
        )

        excellent_students = evaluations.filter(status="excellent")
        good_students = evaluations.filter(status="good")
        average_students = evaluations.filter(status="average")
        at_risk_students = evaluations.filter(status="at_risk")
        critical_students = evaluations.filter(status="critical")

        below_attendance = evaluations.filter(
            attendance_percentage__lt=75
        )

        declining_performance = evaluations.filter(
            performance_trend="declining"
        )

        requiring_counselling = evaluations.filter(
            status__in=["at_risk", "critical"]
        )

    attendance_pending_alerts = pending_attendance
    low_performance_alerts = at_risk_students.count()

    upcoming_exams = Exam.objects.filter(
        start_date__gte=today,
        start_date__lte=today + timezone.timedelta(days=7),
    )

    highest_performing_student = None

    if active_year:
        highest_performing_student = (
            StudentEvaluation.objects.filter(
                academic_year=active_year
            )
            .select_related("student", "student__user")
            .order_by("-average_marks")
            .first()
        )

    recent_students = (
        Student.objects.select_related(
            "user",
            "school_class",
            "section",
        )
        .order_by("-admission_date")[:5]
    )

    hour = timezone.localtime().hour

    if hour < 12:
        greeting = "Morning"
    elif hour < 18:
        greeting = "Afternoon"
    else:
        greeting = "Evening"

    context = {
        "page_title": "Admin Dashboard",

        # Totals
        "total_students": Student.objects.count(),
        "total_teachers": Teacher.objects.count(),
        "total_parents": Parent.objects.count(),
        "total_users": User.objects.count(),

        "recent_users": User.objects.order_by("-date_joined")[:5],

        # Academic
        "active_year": active_year,

        # Empty chart data (until analytics module is implemented)
        "class_performance": [],
        "class_performance_json": json.dumps([]),
        "grade_distribution": json.dumps({}),
        "attendance_trend": json.dumps([]),
        "admission_trend": json.dumps([]),

        # Student Status
        "excellent_students": excellent_students,
        "good_students": good_students,
        "average_students": average_students,
        "at_risk_students": at_risk_students,
        "critical_students": critical_students,
        "below_attendance": below_attendance,
        "declining_performance": declining_performance,
        "requiring_counselling": requiring_counselling,

        # Attendance
        "today_present": today_present,
        "today_absent": today_absent,
        "today_late": today_late,
        "today_leave": today_leave,
        "attendance_percentage": attendance_percentage,
        "pending_attendance": pending_attendance,

        # Teachers
        "active_teachers": active_teachers,
        "teachers_on_leave": teachers_on_leave,

        # Alerts
        "attendance_pending_alerts": attendance_pending_alerts,
        "low_performance_alerts": low_performance_alerts,

        # Exams
        "upcoming_exams": upcoming_exams,

        # Analytics
        "top_attendance_class": None,
        "lowest_attendance_class": None,
        "highest_performing_student": highest_performing_student,

        # Recent
        "recent_students": recent_students,

        # System
        "greeting": greeting,
        "school_name": "SmartSchool ERP",
        "current_session": active_year.name if active_year else "N/A",
        "current_academic_year": active_year.name if active_year else "N/A",
        "current_semester": "First Term",
        "current_date": timezone.now(),
        "current_time": timezone.now(),
        "system_version": "v1.2.0",
    }

    return render(request, "dashboard/admin_dashboard.html", context)


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