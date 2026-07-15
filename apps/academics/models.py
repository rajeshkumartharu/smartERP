from django.db import models


from django.db import models
from django.core.exceptions import ValidationError

from apps.teachers.models import Teacher


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class TimeStampedModel(models.Model):
    """Abstract base adding created_at / updated_at to every lookup table."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Academic Year
# ---------------------------------------------------------------------------

class AcademicYear(TimeStampedModel):
    """
    e.g. "2025/2026". Only one year should be marked current at a time.
    """
    # ---------------- BASIC INFO ----------------
    name = models.CharField(
        max_length=20,
        unique=True,
        help_text="e.g. 2025/2026"
    )
    start_date = models.DateField()
    end_date = models.DateField()

    # ---------------- STATUS ----------------
    is_current = models.BooleanField(
        default=False,
        help_text="Only one academic year should be marked current."
    )

    STATUS_CHOICES = (
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')

    class Meta:
        ordering = ['-start_date']

    def clean(self):
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

    def save(self, *args, **kwargs):
        # Enforce a single "current" academic year.
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------

class Level(TimeStampedModel):
    """
    Schooling level, e.g. Primary, Lower Secondary, Secondary, +2 College.
    `code` mirrors Student.LEVEL_CHOICES values for a clean future FK swap.
    """
    CODE_CHOICES = (
        ('primary', 'Primary (1–5)'),
        ('lower_secondary', 'Lower Secondary (6–8)'),
        ('secondary', 'Secondary (9–10)'),
        ('plus2', '+2 College (11–12)'),
    )

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=30, choices=CODE_CHOICES, unique=True)
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Controls display order (lowest first)."
    )
    uses_faculty = models.BooleanField(
        default=False,
        help_text="Tick for levels where students pick a faculty (e.g. +2)."
    )
    uses_shift = models.BooleanField(
        default=False,
        help_text="Tick for levels that run shifts (e.g. +2)."
    )

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------

class SchoolClass(TimeStampedModel):
    """
    A single grade/class within a Level, e.g. "Class 10" under Secondary.
    Named SchoolClass (not Class) to avoid confusion with the Python keyword.
    """
    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='classes'
    )
    name = models.CharField(max_length=20, help_text="e.g. 10, 11, Nursery")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['level__order', 'order', 'name']
        unique_together = ('level', 'name')
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return f"{self.name} ({self.level.name})"


# ---------------------------------------------------------------------------
# Section
# ---------------------------------------------------------------------------

class Section(TimeStampedModel):
    """A section within a class, e.g. Class 10 - Section A."""
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='sections'
    )
    name = models.CharField(max_length=10, help_text="e.g. A, B, C")
    capacity = models.PositiveSmallIntegerField(
        blank=True, null=True, help_text="Optional max number of students."
    )

    class Meta:
        ordering = ['school_class', 'name']
        unique_together = ('school_class', 'name')

    def __str__(self):
        return f"{self.school_class} - {self.name}"


# ---------------------------------------------------------------------------
# Faculty
# ---------------------------------------------------------------------------

class Faculty(TimeStampedModel):
    """
    e.g. Science, Management, Arts, Law — only meaningful for levels where
    `Level.uses_faculty` is True (typically +2).
    """
    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='faculties'
    )
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ['level__order', 'name']
        unique_together = ('level', 'name')
        verbose_name_plural = "Faculties"

    def __str__(self):
        return f"{self.name} ({self.level.name})"


# ---------------------------------------------------------------------------
# Shift
# ---------------------------------------------------------------------------

class Shift(TimeStampedModel):
    """e.g. Morning Shift, Day Shift."""
    name = models.CharField(max_length=30, unique=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    class Meta:
        ordering = ['start_time', 'name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

class Subject(TimeStampedModel):
    """
    A subject taught at one or more levels, e.g. Mathematics, Physics.
    Which classes it's actually taught in is handled by SubjectClassMapping
    below (a subject can be compulsory in one class and elective in another).
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, help_text="e.g. MATH101")
    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, related_name='subjects'
    )
    full_marks = models.PositiveSmallIntegerField(default=100)
    pass_marks = models.PositiveSmallIntegerField(default=40)
    is_elective = models.BooleanField(default=False)

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        ordering = ['level__order', 'name']
        unique_together = ('level', 'name')

    def clean(self):
        if self.pass_marks and self.full_marks and self.pass_marks > self.full_marks:
            raise ValidationError("Pass marks cannot exceed full marks.")

    def __str__(self):
        return f"{self.name} ({self.code})"


# ---------------------------------------------------------------------------
# Subject–Class Mapping
# ---------------------------------------------------------------------------

class SubjectClassMapping(TimeStampedModel):
    """
    Which subjects are taught in which class, for a given academic year.
    e.g. "Mathematics is compulsory in Class 10 for 2025/2026".
    """
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='subject_mappings'
    )
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='subject_mappings'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='class_mappings'
    )
    is_compulsory = models.BooleanField(default=True)

    class Meta:
        ordering = ['academic_year', 'school_class', 'subject']
        unique_together = ('academic_year', 'school_class', 'subject')
        verbose_name = "Subject-Class Mapping"
        verbose_name_plural = "Subject-Class Mappings"

    def clean(self):
        # Guard against mapping a subject to a class in a different level.
        if self.subject_id and self.school_class_id:
            if self.subject.level_id != self.school_class.level_id:
                raise ValidationError(
                    f"'{self.subject}' belongs to {self.subject.level}, "
                    f"but '{self.school_class}' belongs to {self.school_class.level}."
                )

    def __str__(self):
        return f"{self.subject} → {self.school_class} ({self.academic_year})"


# ---------------------------------------------------------------------------
# Teacher–Subject Assignment
# ---------------------------------------------------------------------------

class TeacherSubjectAssignment(TimeStampedModel):
    """
    Which teacher teaches a given subject to a given class/section, for a
    given academic year. Only one teacher may hold a given
    (subject, class, section, year) combination — enforced below.
    """
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='subject_assignments'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='teacher_assignments'
    )
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='teacher_assignments'
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name='teacher_assignments',
        blank=True, null=True,
        help_text="Leave blank to assign the teacher to the whole class."
    )
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='teacher_assignments'
    )

    class Meta:
        ordering = ['academic_year', 'school_class', 'subject']
        unique_together = ('subject', 'school_class', 'section', 'academic_year')
        verbose_name = "Teacher Subject Assignment"
        verbose_name_plural = "Teacher Subject Assignments"

    def clean(self):
        if self.section_id and self.section.school_class_id != self.school_class_id:
            raise ValidationError("Selected section does not belong to the selected class.")

    def __str__(self):
        target = f"{self.school_class}{' - ' + self.section.name if self.section else ''}"
        return f"{self.teacher} teaches {self.subject} to {target} ({self.academic_year})"



from django.conf import settings

class Term(TimeStampedModel):
    name = models.CharField(max_length=50) # e.g. "First Term", "Final Term"
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_date']
        unique_together = ('academic_year', 'name')

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"


class Exam(TimeStampedModel):
    name = models.CharField(max_length=100) # e.g. "First Term Examination"
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='exams')
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name} - {self.term}"


class Assessment(TimeStampedModel):
    TYPE_CHOICES = (
        ('exam', 'Exam'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('project', 'Project'),
        ('practical', 'Practical'),
    )
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assessments')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='assessments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='assessments', blank=True, null=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='assessments')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='assessments', blank=True, null=True)
    assessment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='exam')
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    weightage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, help_text="Weightage percentage in final grade, e.g. 10.00 for 10%")
    date = models.DateField()
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='created_assessments')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.name} ({self.get_assessment_type_display()}) - {self.subject.name} - {self.school_class.name}"


class MarksEntry(TimeStampedModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='marks_entries')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='marks_entries')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_marks')
    teacher_feedback = models.TextField(blank=True, null=True)
    student_feedback = models.TextField(blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('assessment', 'student')
        verbose_name = "Marks Entry"
        verbose_name_plural = "Marks Entries"

    def clean(self):
        if self.marks_obtained is not None and self.assessment_id:
            if self.marks_obtained > self.assessment.max_marks:
                raise ValidationError(f"Marks obtained ({self.marks_obtained}) cannot exceed maximum marks ({self.assessment.max_marks})")
            if self.marks_obtained < 0:
                raise ValidationError("Marks obtained cannot be negative.")

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assessment.name}: {self.marks_obtained}/{self.assessment.max_marks}"


class GradeScale(TimeStampedModel):
    name = models.CharField(max_length=10, unique=True) # e.g. "A+", "A"
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2, unique=True)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2, unique=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2) # e.g. 4.00, 3.60
    remarks = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-min_percentage']

    def __str__(self):
        return f"{self.name} ({self.min_percentage}% - {self.max_percentage}%) - GP: {self.grade_point}"


class StudentEvaluation(TimeStampedModel):
    STATUS_CHOICES = (
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('at_risk', 'At Risk'),
    )
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='evaluations')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='student_evaluations')
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    subject_average = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    overall_gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='average')

    class Meta:
        unique_together = ('student', 'academic_year')

    def __str__(self):
        return f"{self.student.student_id} Evaluation - Status: {self.get_status_display()}"