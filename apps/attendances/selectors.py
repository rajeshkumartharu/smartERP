from django.db.models import Count, Q

from .models import ClassTeacherAssignment, AttendanceSession, AttendanceRecord


def get_active_class_teacher_assignment_for_teacher(teacher):
    return (
        ClassTeacherAssignment.objects
        .select_related('teacher', 'academic_year', 'school_class', 'section')
        .filter(teacher=teacher, is_active=True)
        .first()
    )


def get_attendance_sessions_for_assignment(assignment):
    return (
        AttendanceSession.objects
        .filter(
            academic_year=assignment.academic_year,
            school_class=assignment.school_class,
            section=assignment.section
        )
        .select_related('academic_year', 'school_class', 'section', 'marked_by')
        .prefetch_related('records__student')
        .order_by('-date')
    )


def get_student_attendance_summary(student):
    qs = AttendanceRecord.objects.filter(student=student)

    return qs.aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status=AttendanceRecord.STATUS_PRESENT)),
        absent=Count('id', filter=Q(status=AttendanceRecord.STATUS_ABSENT)),
        late=Count('id', filter=Q(status=AttendanceRecord.STATUS_LATE)),
        leave=Count('id', filter=Q(status=AttendanceRecord.STATUS_LEAVE)),
    )