from django.db import models
from apps.accounts.models import User


class Teacher(models.Model):

    # ---------------- USER ----------------
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )

    # ---------------- BASIC INFO ----------------
    teacher_id = models.CharField(max_length=20, unique=True)

    gender_choices = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=gender_choices, blank=True, null=True)

    date_of_birth = models.DateField(blank=True, null=True)

    # ---------------- CONTACT INFO ----------------
    address = models.TextField(blank=True, null=True)
    contact_no = models.CharField(max_length=15, blank=True, null=True)
   
    profile_image = models.ImageField(upload_to='teachers/', blank=True, null=True)

    # ---------------- ACADEMIC INFO ----------------
    QUALIFICATION_CHOICES = (
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
        ('others', 'Others'),
    )

    qualification = models.CharField(
        max_length=20,
        choices=QUALIFICATION_CHOICES
    )

    subject = models.CharField(max_length=100)

    experience_years = models.PositiveIntegerField(default=0)

    # ---------------- TEACHING LEVEL ----------------
    LEVEL_CHOICES = (
        ('primary', 'Primary (1–5)'),
        ('lower_secondary', 'Lower Secondary (6–8)'),
        ('secondary', 'Secondary (9–10)'),
        ('plus2', '+2 College (11–12)'),
        ('all', 'All Levels'),
    )

    teaching_level = models.CharField(
        max_length=30,
        choices=LEVEL_CHOICES,
        default='secondary'
    )

    # ---------------- +2 SPECIFIC ----------------
    faculty = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Only for +2 (Science / Management / Arts)"
    )

    shift_choices = (
        ('morning', 'Morning'),
        ('day', 'Day'),
        ('both', 'Both'),
    )

    shift = models.CharField(
        max_length=10,
        choices=shift_choices,
        default='day'
    )

    # ---------------- WORK INFO ----------------
    joining_date = models.DateField()

    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    status_choices = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('resigned', 'Resigned'),
        ('on_leave', 'On Leave'),
    )

    status = models.CharField(
        max_length=20,
        choices=status_choices,
        default='active'
    )

    # ---------------- TIMESTAMPS ----------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------- STRING ----------------
    def __str__(self):
        return f"{self.first_name} {self.last_name or ''} ({self.teacher_id})"