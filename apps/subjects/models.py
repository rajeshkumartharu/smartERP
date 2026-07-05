from django.db import models


class ClassRoom(models.Model):
    """
    Example:
    Grade 1, Grade 2, Grade 10, Nursery, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    numeric_level = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['numeric_level', 'name']

    def __str__(self):
        return self.name


class Subject(models.Model):
    SUBJECT_TYPE_CHOICES = (
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('both', 'Theory + Practical'),
    )

    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    class_room = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    subject_type = models.CharField(
        max_length=20,
        choices=SUBJECT_TYPE_CHOICES,
        default='theory'
    )

    full_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=40)
    credit_hours = models.PositiveIntegerField(default=1)

    description = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_room__name', 'name']
        unique_together = ('class_room', 'name')
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"{self.name} ({self.class_room.name})"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.pass_marks > self.full_marks:
            raise ValidationError("Pass marks cannot be greater than full marks.")