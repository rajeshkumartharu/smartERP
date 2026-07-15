from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# Adjust these imports to your project structure
from apps.teachers.models import Teacher
from apps.students.models import Student
from apps.parents.models import Parent
from apps.academics.models import AcademicYear, SchoolClass, Section


class ClassTeacherAssignment(models.Model):
    """
    Assign one teacher as class teacher for a class-section in an academic year.
    """

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments'
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='class_teacher_assignments'
    )
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['school_class', 'section']
        verbose_name = 'Class Teacher Assignment'
        verbose_name_plural = 'Class Teacher Assignments'
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'school_class', 'section'],
                condition=models.Q(is_active=True),
                name='unique_active_class_teacher_assignment'
            )
        ]

    def __str__(self):
        return f"{self.teacher} → {self.school_class} {self.section} ({self.academic_year})"


class AttendanceSession(models.Model):
    """
    One daily attendance sheet for one class-section on one date.
    """

    PERIOD_FIRST = 'first_period'
    PERIOD_CHOICES = [
        (PERIOD_FIRST, 'First Period'),
    ]

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    date = models.DateField(default=timezone.localdate)
    marked_by = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendance_sessions'
    )
    taken_in_period = models.CharField(
        max_length=30,
        choices=PERIOD_CHOICES,
        default=PERIOD_FIRST
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'school_class', 'section']
        verbose_name = 'Attendance Session'
        verbose_name_plural = 'Attendance Sessions'
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'school_class', 'section', 'date'],
                name='unique_daily_attendance_session'
            )
        ]

    def __str__(self):
        return f"{self.school_class} {self.section} - {self.date}"

    @property
    def total_students(self):
        return self.records.count()

    @property
    def present_count(self):
        return self.records.filter(status=AttendanceRecord.STATUS_PRESENT).count()

    @property
    def absent_count(self):
        return self.records.filter(status=AttendanceRecord.STATUS_ABSENT).count()

    @property
    def late_count(self):
        return self.records.filter(status=AttendanceRecord.STATUS_LATE).count()

    @property
    def leave_count(self):
        return self.records.filter(status=AttendanceRecord.STATUS_LEAVE).count()


class AttendanceRecord(models.Model):
    """
    Attendance status for a single student in one attendance session.
    """

    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_LATE = 'late'
    STATUS_LEAVE = 'leave'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_LEAVE, 'Leave'),
    ]

    attendance_session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PRESENT
    )
    remark = models.CharField(max_length=255, blank=True)
    notified_parent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        constraints = [
            models.UniqueConstraint(
                fields=['attendance_session', 'student'],
                name='unique_student_attendance_per_session'
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.status} - {self.attendance_session}"

    def clean(self):
        """
        Ensure the student belongs to the same class-section as the session.
        Adjust these field names if your Student model differs.
        """
        student_class = getattr(self.student, 'school_class', None)
        student_section = getattr(self.student, 'section', None)

        if student_class != self.attendance_session.school_class:
            raise ValidationError("Student does not belong to the session class.")

        if student_section != self.attendance_session.section:
            raise ValidationError("Student does not belong to the session section.")