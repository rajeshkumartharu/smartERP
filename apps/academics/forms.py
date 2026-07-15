"""
apps/academics/forms.py

ModelForms for the Academic Structure section (Academic Years, Levels,
Classes, Sections, Faculties, Shifts, Subjects, Subject-Class Mapping,
Teacher Subject Assignment).

All forms share a Tailwind input style via TailwindFormMixin so templates
can just render {{ form.field }} and get consistent styling for free —
including on ForeignKey fields, which become <select> dropdowns
automatically populated from the DB (Level.objects.all(), etc.) via
Django's ModelChoiceField.
"""

from django import forms

from .models import (
    AcademicYear,
    Level,
    SchoolClass,
    Section,
    Faculty,
    Shift,
    Subject,
    SubjectClassMapping,
    TeacherSubjectAssignment,
)

INPUT_CLASS = (
    "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm "
    "focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
)
CHECKBOX_CLASS = "w-4 h-4 text-brand-500 border-slate-300 rounded focus:ring-brand-500"


class TailwindFormMixin:
    """Applies consistent Tailwind classes to every field's widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', CHECKBOX_CLASS)
            else:
                existing = widget.attrs.get('class', '')
                widget.attrs['class'] = f"{existing} {INPUT_CLASS}".strip()


# ---------------------------------------------------------------------------

class AcademicYearForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class LevelForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Level
        fields = ['name', 'code', 'order', 'uses_faculty', 'uses_shift']


class SchoolClassForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['level', 'name', 'order']


class SectionForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Section
        fields = ['school_class', 'name', 'capacity']


class FacultyForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['level', 'name', 'code']


class ShiftForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['name', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class SubjectForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'level', 'full_marks', 'pass_marks', 'is_elective', 'status']


class SubjectClassMappingForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = SubjectClassMapping
        fields = ['academic_year', 'school_class', 'subject', 'is_compulsory']


class TeacherSubjectAssignmentForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = TeacherSubjectAssignment
        fields = ['teacher', 'subject', 'school_class', 'section', 'academic_year']