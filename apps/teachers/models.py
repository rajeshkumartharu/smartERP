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
    teacher_id = models.CharField(max_length=20, unique=True, blank=True)

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)

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
    qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES)

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

    SHIFT_CHOICES = (
        ('morning', 'Morning'),
        ('day', 'Day'),
        ('both', 'Both'),
    )
    shift = models.CharField(
        max_length=10,
        choices=SHIFT_CHOICES,
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

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('resigned', 'Resigned'),
        ('on_leave', 'On Leave'),
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
        if not self.teacher_id:
            last_teacher = Teacher.objects.order_by('-id').first()

            if last_teacher and last_teacher.teacher_id:
                # Example existing ID: TCH0001
                last_number = int(last_teacher.teacher_id.replace('TCH', ''))
                new_number = last_number + 1
            else:
                new_number = 1

            self.teacher_id = f"TCH{new_number:04d}"

        super().save(*args, **kwargs)

    # ---------------- STRING ----------------
    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.teacher_id})"