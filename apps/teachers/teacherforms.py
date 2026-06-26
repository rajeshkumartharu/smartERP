from django import forms
from apps.teachers.models import Teacher


class TeacherForm(forms.ModelForm):

    class Meta:
        model = Teacher

        exclude = [
            'user',
            'created_at',
            'updated_at',
        ]

        widgets = {

            # ---------------- BASIC INFO ----------------
            'teacher_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Teacher ID'
            }),

            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),

            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            # ---------------- CONTACT INFO ----------------
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

            # ---------------- ACADEMIC INFO ----------------
            'qualification': forms.Select(attrs={
                'class': 'form-select'
            }),

            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Subject'
            }),

            'experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Years of Experience'
            }),

            # ---------------- TEACHING LEVEL ----------------
            'teaching_level': forms.Select(attrs={
                'class': 'form-select'
            }),

            # ---------------- +2 SPECIFIC ----------------
            'faculty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Science / Management / Arts'
            }),

            'shift': forms.Select(attrs={
                'class': 'form-select'
            }),

            # ---------------- WORK INFO ----------------
            'joining_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Salary'
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

    def clean_teacher_id(self):

        teacher_id = self.cleaned_data.get('teacher_id')

        if len(teacher_id) < 3:
            raise forms.ValidationError(
                "Teacher ID is too short."
            )

        return teacher_id



    # ---------------- +2 VALIDATION ----------------

    def clean(self):

        cleaned_data = super().clean()

        teaching_level = cleaned_data.get('teaching_level')
        faculty = cleaned_data.get('faculty')

        if teaching_level == 'plus2':

            if not faculty:
                self.add_error(
                    'faculty',
                    'Faculty is required for +2 teachers.'
                )

        return cleaned_data