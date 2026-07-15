from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError

from .models import (
    ClassTeacherAssignment,
    AttendanceSession,
    AttendanceRecord,
)

# Adjust import path to your project
from apps.students.models import Student


def get_active_class_teacher_assignment(teacher):
    return (
        ClassTeacherAssignment.objects
        .select_related('academic_year', 'school_class', 'section')
        .filter(teacher=teacher, is_active=True)
        .first()
    )


def get_students_for_class_section(school_class, section):
    """
    Adjust field names if your Student model uses another structure.
    """
    return (
        Student.objects
        .filter(
            school_class=school_class,
            section=section,
            is_active=True
        )
        .select_related('user', 'school_class', 'section')
        .order_by('roll_no', 'user__first_name')
    )


def attendance_session_exists(academic_year, school_class, section, date):
    return AttendanceSession.objects.filter(
        academic_year=academic_year,
        school_class=school_class,
        section=section,
        date=date
    ).exists()


def parse_attendance_data_from_post(request_post, students):
    """
    Reads:
      status_<student_id>
      remark_<student_id>
    from POST and returns a normalized list.
    """
    attendance_data = []

    for student in students:
        status = request_post.get(f'status_{student.pk}', AttendanceRecord.STATUS_PRESENT)
        remark = request_post.get(f'remark_{student.pk}', '').strip()

        if status not in {
            AttendanceRecord.STATUS_PRESENT,
            AttendanceRecord.STATUS_ABSENT,
            AttendanceRecord.STATUS_LATE,
            AttendanceRecord.STATUS_LEAVE
        }:
            raise ValidationError(f"Invalid attendance status for student {student}.")

        attendance_data.append({
            'student': student,
            'status': status,
            'remark': remark,
        })

    return attendance_data


def notify_parent_for_absent_student(student, attendance_record):
    """
    Placeholder for future email/SMS/notification queue integration.
    You can later integrate:
      - send_mail(...)
      - notification model
      - SMS gateway
    """
    parent = getattr(student, 'parent', None)  # adjust if relation differs
    if not parent:
        return False

    # Example future logic:
    # send_mail(
    #     subject="Student Absence Alert",
    #     message=f"{student} was marked absent on {attendance_record.attendance_session.date}",
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[parent.user.email],
    # )

    attendance_record.notified_parent = True
    attendance_record.save(update_fields=['notified_parent'])
    return True


@transaction.atomic
def create_daily_attendance_session(*, teacher, assignment, date, remarks, attendance_data):
    """
    Creates AttendanceSession + AttendanceRecord rows in one transaction.
    """
    if not assignment:
        raise PermissionDenied("No active class teacher assignment found.")

    if assignment.teacher != teacher:
        raise PermissionDenied("You are not allowed to mark attendance for this class.")

    if attendance_session_exists(
        assignment.academic_year,
        assignment.school_class,
        assignment.section,
        date
    ):
        raise ValidationError("Attendance for this class has already been marked for this date.")

    session = AttendanceSession.objects.create(
        academic_year=assignment.academic_year,
        school_class=assignment.school_class,
        section=assignment.section,
        date=date,
        marked_by=teacher,
        taken_in_period=AttendanceSession.PERIOD_FIRST,
        remarks=remarks or ''
    )

    records = []
    for row in attendance_data:
        student = row['student']

        # Validate student belongs to same class-section
        if student.school_class != assignment.school_class or student.section != assignment.section:
            raise ValidationError(
                f"Student {student} does not belong to {assignment.school_class} {assignment.section}."
            )

        records.append(
            AttendanceRecord(
                attendance_session=session,
                student=student,
                status=row['status'],
                remark=row['remark']
            )
        )

    AttendanceRecord.objects.bulk_create(records)

    # Re-fetch for absent notifications if needed
    created_records = AttendanceRecord.objects.filter(attendance_session=session).select_related('student')

    for record in created_records:
        if record.status == AttendanceRecord.STATUS_ABSENT:
            notify_parent_for_absent_student(record.student, record)

    return session