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
    student_id = models.CharField(max_length=20, unique=True)

    gender_choices = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=gender_choices, blank=True, null=True)

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

    class_name = models.CharField(max_length=20)  # Class 1–12
    section = models.CharField(max_length=10, blank=True, null=True)

    faculty = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Only for +2 (Science, Management, Arts)"
    )

    # ---------------- NEW: SHIFT (ONLY +2) ----------------
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

    # ---------------- STRING ----------------
    def __str__(self):
        return f"{self.first_name} {self.last_name or ''} ({self.student_id})"