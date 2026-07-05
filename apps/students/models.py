from django.db import models
from apps.accounts.models import User


class Student(models.Model):
    # ---------------- USER ----------------
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    # ---------------- BASIC INFO ----------------
    student_id = models.CharField(max_length=20, unique=True, blank=True)

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # ---------------- CONTACT ----------------
    address = models.TextField(blank=True, null=True)
    contact_no = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='students/', blank=True, null=True)

    # ---------------- ACADEMIC STRUCTURE ----------------
    LEVEL_CHOICES = (
        ('primary', 'Primary (1–5)'),
        ('lower_secondary', 'Lower Secondary (6–8)'),
        ('secondary', 'Secondary (9–10)'),
        ('plus2', '+2 College (11–12)'),
    )
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES)

    class_name = models.CharField(max_length=20)
    section = models.CharField(max_length=10, blank=True, null=True)

    faculty = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Only for +2 (Science, Management, Arts)"
    )

    SHIFT_CHOICES = (
        ('morning', 'Morning Shift'),
        ('day', 'Day Shift'),
    )
    shift = models.CharField(
        max_length=10,
        choices=SHIFT_CHOICES,
        blank=True,
        null=True,
        help_text="Only applicable for +2 students"
    )

    roll_number = models.CharField(max_length=20, blank=True, null=True)

    # ---------------- ACADEMIC INFO ----------------
    admission_date = models.DateField()
    academic_year = models.CharField(max_length=20)

    # ---------------- STATUS ----------------
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('passed_out', 'Passed Out'),
        ('transferred', 'Transferred'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # ---------------- TIMESTAMPS ----------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------- AUTO ID GENERATION ----------------
    def save(self, *args, **kwargs):
        if not self.student_id:
            last_student = Student.objects.order_by('-id').first()

            if last_student and last_student.student_id:
                last_number = int(last_student.student_id.replace('STD', ''))
                new_number = last_number + 1
            else:
                new_number = 1

            self.student_id = f"STD{new_number:04d}"

        super().save(*args, **kwargs)

    # ---------------- STRING ----------------
    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.student_id})"