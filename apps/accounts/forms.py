from django import forms
from apps.accounts.models import User


class UserRegistrationForm(forms.ModelForm):
    """
    Form for registering a new User (admin-side).
    Password is auto-generated; email is sent to the user.
    """

    # Expose role so we can validate it in the view
    role = forms.ChoiceField(
        choices=User.role_choices,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'roleSelect',
        })
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Username',
                'autofocus': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Email Address',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter First Name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Last Name',
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise forms.ValidationError("Last name is required.")
        return last_name


class ChangePasswordForm(forms.Form):
    """
    Form for the forced first-login password change.
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current Password',
            'id': 'currentPassword',
        }),
        label='Current Password',
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password',
            'id': 'newPassword',
        }),
        label='New Password',
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm New Password',
            'id': 'confirmPassword',
        }),
        label='Confirm New Password',
    )

    def clean(self):
        cleaned = super().clean()
        new_password = cleaned.get('new_password')
        confirm_password = cleaned.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned
