from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from apps.core.decorators import role_required
from apps.teachers.models import Teacher
from apps.students.models import Student
from apps.parents.models import Parent

from .forms import AttendanceTakeForm, AttendanceHistoryFilterForm
from .models import AttendanceSession, AttendanceRecord
from .selectors import (
    get_active_class_teacher_assignment_for_teacher,
    get_attendance_sessions_for_assignment,
    get_student_attendance_summary,
)
from .services import (
    get_students_for_class_section,
    parse_attendance_data_from_post,
    create_daily_attendance_session,
)


@login_required
@role_required('teacher')
def teacher_take_attendance(request):
    """
    Teacher marks daily attendance for assigned class-section.
    """
    teacher = get_object_or_404(Teacher, user=request.user)
    assignment = get_active_class_teacher_assignment_for_teacher(teacher)

    if not assignment:
        messages.error(request, "No active class teacher assignment found.")
        return redirect('teacher_dashboard')

    students = get_students_for_class_section(
        assignment.school_class,
        assignment.section
    )

    if not students.exists():
        messages.warning(request, "No active students found in your assigned class/section.")
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        form = AttendanceTakeForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            remarks = form.cleaned_data.get('remarks', '')

            try:
                attendance_data = parse_attendance_data_from_post(request.POST, students)
                session = create_daily_attendance_session(
                    teacher=teacher,
                    assignment=assignment,
                    date=date,
                    remarks=remarks,
                    attendance_data=attendance_data
                )
                messages.success(request, f"Attendance saved successfully for {session.date}.")
                return redirect('teacher_attendance_history')

            except ValidationError as e:
                messages.error(request, str(e))
            except PermissionDenied as e:
                messages.error(request, str(e))
    else:
        form = AttendanceTakeForm(initial={'date': timezone.localdate()})

    # Optional info: whether today's attendance already exists
    today = timezone.localdate()
    already_marked_today = AttendanceSession.objects.filter(
        academic_year=assignment.academic_year,
        school_class=assignment.school_class,
        section=assignment.section,
        date=today
    ).exists()

    context = {
        'form': form,
        'assignment': assignment,
        'students': students,
        'already_marked_today': already_marked_today,
    }
    return render(request, 'attendance/teacher_take_attendance.html', context)


@login_required
@role_required('teacher')
def teacher_attendance_history(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    assignment = get_active_class_teacher_assignment_for_teacher(teacher)

    if not assignment:
        messages.error(request, "No active class teacher assignment found.")
        return redirect('teacher_dashboard')

    sessions = get_attendance_sessions_for_assignment(assignment)
    filter_form = AttendanceHistoryFilterForm(request.GET or None)

    if filter_form.is_valid():
        date = filter_form.cleaned_data.get('date')
        month = filter_form.cleaned_data.get('month')
        year = filter_form.cleaned_data.get('year')

        if date:
            sessions = sessions.filter(date=date)
        if month:
            sessions = sessions.filter(date__month=month)
        if year:
            sessions = sessions.filter(date__year=year)

    context = {
        'assignment': assignment,
        'sessions': sessions,
        'filter_form': filter_form,
    }
    return render(request, 'attendance/teacher_attendance_history.html', context)


@login_required
@role_required('admin')
def admin_attendance_list(request):
    sessions = (
        AttendanceSession.objects
        .select_related('academic_year', 'school_class', 'section', 'marked_by')
        .prefetch_related('records__student')
        .order_by('-date')
    )

    # simple GET filters
    academic_year = request.GET.get('academic_year')
    school_class = request.GET.get('school_class')
    section = request.GET.get('section')
    date = request.GET.get('date')

    if academic_year:
        sessions = sessions.filter(academic_year_id=academic_year)
    if school_class:
        sessions = sessions.filter(school_class_id=school_class)
    if section:
        sessions = sessions.filter(section_id=section)
    if date:
        sessions = sessions.filter(date=date)

    context = {
        'sessions': sessions,
    }
    return render(request, 'attendance/admin_attendance_list.html', context)


@login_required
@role_required('student')
def student_attendance_report(request):
    student = get_object_or_404(Student, user=request.user)

    records = (
        AttendanceRecord.objects
        .filter(student=student)
        .select_related('attendance_session', 'attendance_session__school_class', 'attendance_session__section')
        .order_by('-attendance_session__date')
    )

    summary = get_student_attendance_summary(student)
    total = summary.get('total', 0) or 0
    present = summary.get('present', 0) or 0
    attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

    context = {
        'student': student,
        'records': records,
        'summary': summary,
        'attendance_percentage': attendance_percentage,
    }
    return render(request, 'attendance/student_attendance_report.html', context)


@login_required
@role_required('parent')
def parent_child_attendance_report(request):
    parent = get_object_or_404(Parent, user=request.user)

    # Adjust relation according to your project:
    # Example assumes Parent has related students via parent.students.all()
    children = getattr(parent, 'students', None)
    if children is None:
        children = Student.objects.filter(parent=parent)

    children = children.all() if hasattr(children, 'all') else children

    selected_child_id = request.GET.get('child')
    selected_child = None

    if selected_child_id:
        selected_child = get_object_or_404(Student, pk=selected_child_id)
        # Security check: ensure selected child belongs to parent
        if hasattr(children, 'filter'):
            if not children.filter(pk=selected_child.pk).exists():
                messages.error(request, "You are not allowed to view this student.")
                return redirect('parent_dashboard')
        else:
            if selected_child not in children:
                messages.error(request, "You are not allowed to view this student.")
                return redirect('parent_dashboard')
    else:
        if hasattr(children, 'first'):
            selected_child = children.first()
        else:
            selected_child = children[0] if children else None

    records = []
    summary = {}
    attendance_percentage = 0

    if selected_child:
        records = (
            AttendanceRecord.objects
            .filter(student=selected_child)
            .select_related('attendance_session', 'attendance_session__school_class', 'attendance_session__section')
            .order_by('-attendance_session__date')
        )
        summary = get_student_attendance_summary(selected_child)
        total = summary.get('total', 0) or 0
        present = summary.get('present', 0) or 0
        attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

    context = {
        'parent': parent,
        'children': children,
        'selected_child': selected_child,
        'records': records,
        'summary': summary,
        'attendance_percentage': attendance_percentage,
    }
    return render(request, 'attendance/parent_child_attendance_report.html', context)