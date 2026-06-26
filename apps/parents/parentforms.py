from django import forms
from apps.parents.models import Parent


class ParentForm(forms.ModelForm):

    class Meta:
        model = Parent

        exclude = [
            'user',
            'created_at',
            'updated_at',
        ]

        widgets = {

            # ---------------- BASIC INFO ----------------
            'parent_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Parent ID'
            }),

            'gender': forms.Select(attrs={
                'class': 'form-select'
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

            # ---------------- RELATION ----------------
            'relation': forms.Select(attrs={
                'class': 'form-select'
            }),

            # ---------------- STUDENTS ----------------
            'students': forms.SelectMultiple(attrs={
                'class': 'form-select'
            }),

            # ---------------- OCCUPATION ----------------
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Occupation'
            }),

            # ---------------- STATUS ----------------
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    # ---------------- CUSTOM VALIDATION ----------------
    def clean_contact_no(self):

        contact = self.cleaned_data.get('contact_no')

        if not contact.isdigit():
            raise forms.ValidationError(
                "Contact number must contain only digits."
            )

        if len(contact) < 10:
            raise forms.ValidationError(
                "Contact number must be at least 10 digits."
            )

        return contact

    def clean_parent_id(self):

        parent_id = self.cleaned_data.get('parent_id')

        if len(parent_id) < 3:
            raise forms.ValidationError(
                "Parent ID is too short."
            )

        return parent_id

    