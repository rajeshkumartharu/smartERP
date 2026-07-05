from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model for SmartSchool.
    Extends AbstractUser with role-based access and password-change enforcement.
    """

    email = models.EmailField(unique=True)

    role_choices = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=role_choices)

    must_change_password = models.BooleanField(
        default=True,
        help_text="Force the user to change their password on next login."
    )

    # Stores the plain-text auto-generated password so admin can look it up
    # if the email bounces. Cleared to empty string after the user changes it.
    raw_password = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Auto-generated plain-text password. Cleared after user changes it."
    )

    # Use email as the unique identifier for authentication
    REQUIRED_FIELDS = ['email', 'role']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    def get_dashboard_url_name(self):
        """Return the URL name for the user's role-specific dashboard."""
        mapping = {
            'student': 'student_dashboard',
            'teacher': 'teacher_dashboard',
            'parent':  'parent_dashboard',
            'admin':   'admin_dashboard',
        }
        return mapping.get(self.role, 'login')
