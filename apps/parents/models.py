from django.db import models
from apps.accounts.models import User
from apps.students.models import Student


class Parent(models.Model):

    # ---------------- USER ----------------
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile'
    )

    # ---------------- BASIC INFO ----------------
    parent_id = models.CharField(max_length=20, unique=True)


    gender_choices = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=gender_choices, blank=True, null=True)

    # ---------------- CONTACT INFO ----------------
    address = models.TextField(blank=True, null=True)
    contact_no = models.CharField(max_length=15)

    profile_image = models.ImageField(upload_to='parents/', blank=True, null=True)

    # ---------------- RELATION TO STUDENT ----------------
    RELATION_CHOICES = (
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
    )

    relation = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES
    )

    # ---------------- LINKED STUDENTS ----------------
    students = models.ManyToManyField(
        Student,
        related_name='parents',
        blank=True
    )

    # ---------------- OCCUPATION ----------------
    occupation = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # ---------------- STATUS ----------------
    status_choices = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
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
        return f"{self.user.first_name} {self.user.last_name or ''} ({self.parent_id})"