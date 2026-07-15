from django import forms
from apps.students.models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = [
            'user',
            'student_id',   # auto-generated in model
            'created_at',
            'updated_at',
        ]

        widgets = {
            # ---------------- BASIC INFO ----------------
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),

            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            # ---------------- CONTACT ----------------
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Address'
            }),

            'contact_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Contact Number'
            }),

            'profile_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),

            # ---------------- ACADEMIC STRUCTURE ----------------
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),

            'school_class': forms.Select(attrs={
                'class': 'form-select'
            }),

            'section': forms.Select(attrs={
                'class': 'form-select'
            }),

            'faculty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Science / Management / Arts'
            }),

            'shift': forms.Select(attrs={
                'class': 'form-select'
            }),

            'roll_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Roll Number'
            }),

            # ---------------- ACADEMIC INFO ----------------
            'admission_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'academic_year': forms.Select(attrs={
                'class': 'form-select'
            }),

            # ---------------- STATUS ----------------
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    # ---------------- CUSTOM VALIDATION ----------------
    def clean_contact_no(self):
        contact = self.cleaned_data.get('contact_no')

        if contact:
            if not contact.isdigit():
                raise forms.ValidationError(
                    "Contact number must contain only digits."
                )

            if len(contact) < 10:
                raise forms.ValidationError(
                    "Contact number must be at least 10 digits."
                )

        return contact

    # ---------------- LEVEL BASED VALIDATION ----------------
    def clean(self):
        cleaned_data = super().clean()

        level = cleaned_data.get('level')
        faculty = cleaned_data.get('faculty')
        shift = cleaned_data.get('shift')

        # +2 validation (level is now a Level model instance)
        level_code = level.code if level else None
        if level_code == 'plus2':
            if not faculty:
                self.add_error(
                    'faculty',
                    'Faculty is required for +2 students.'
                )

            if not shift:
                self.add_error(
                    'shift',
                    'Shift is required for +2 students.'
                )
        else:
            # for non +2 students, clear faculty and shift
            cleaned_data['faculty'] = None
            cleaned_data['shift'] = None

        return cleaned_data