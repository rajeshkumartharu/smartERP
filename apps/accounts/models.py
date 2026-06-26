from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    email = models.EmailField(unique=True)

    role_choices = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=role_choices)

    must_change_password = models.BooleanField(default=True)

    # Stores the plain-text auto-generated password so admin can
    # look it up if the email bounces. Clear this after the user
    # changes their password (must_change_password → False).
    raw_password = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Auto-generated plain-text password. Cleared after user changes it."
    )

    def __str__(self):
        return self.username