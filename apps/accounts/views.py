from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from apps.core.decorators import role_required
from apps.accounts.forms import UserRegistrationForm, ChangePasswordForm
from apps.accounts.models import User
from apps.core.utils.password_generator import generate_password

# Import profile forms (lazily resolved so import errors surface clearly)
from apps.students.studentforms import StudentForm
from apps.teachers.teacherforms import TeacherForm
from apps.parents.parentforms import ParentForm
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.parents.models import Parent

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_dashboard_url(role: str) -> str:
    """Return the URL name for the given role's dashboard."""
    return {
        'student': 'student_dashboard',
        'teacher': 'teacher_dashboard',
        'parent':  'parent_dashboard',
        'admin':   'admin_dashboard',
    }.get(role, 'login')


def _registration_context(user_form, profile_form, students=None, errors=None):
    """
    Build shared registration template context for separate role-wise templates.
    """
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }

    if students is not None:
        context['students'] = students

    if errors:
        context['errors'] = errors

    return context

def _create_user_and_profile(request, role, user_form, profile_form):
    """
    Shared function to create user + role profile and send credentials email.
    Used by student / teacher / parent registration views.
    """
    with transaction.atomic():
        raw_password = generate_password()

        user = user_form.save(commit=False)
        user.role = role
        user.email = user_form.cleaned_data['email'].lower()
        user.set_password(raw_password)
        user.raw_password = raw_password
        user.must_change_password = True
        user.save()

        profile = profile_form.save(commit=False)
        profile.user = user
        profile.save()

        # Save many-to-many relations for parent form if needed
        if role == 'parent':
            profile_form.save_m2m()

    # Send email after successful DB save
    try:
        _send_credentials_email(request, user, raw_password, role)
        messages.success(
            request,
            f"{role.capitalize()} account for '{user.get_full_name() or user.username}' created successfully. "
            f"Credentials emailed to {user.email}."
        )
    except Exception as exc:
        messages.warning(
            request,
            f"{role.capitalize()} account created successfully, but email could not be sent: {exc}"
        )

    return user



def _send_credentials_email(request, user, raw_password, role):
    """
    Send login credentials email to newly created user.
    """
    send_mail(
        subject="SmartSchool - Your Login Credentials",
        message=(
            f"Hello {user.get_full_name() or user.username},\n\n"
            f"Your {role.capitalize()} account has been created successfully.\n\n"
            f"Username : {user.username}\n"
            f"Password : {raw_password}\n\n"
            f"Please log in and change your password immediately.\n"
            f"Login URL: {request.build_absolute_uri('/accounts/login/')}\n\n"
            f"Regards,\n"
            f"SmartSchool Team"
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )

# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------

def login_view(request):
    """
    Authenticate a user and redirect to their role dashboard.
    Supports login via username OR email.
    """
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")

        return redirect(_get_dashboard_url(request.user.role))

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        if not identifier or not password:
            messages.error(request, "Username/email and password are required.")
            return render(request, 'auth/login.html', {'identifier': identifier})

        # Allow login by email address
        username = identifier
        if '@' in identifier:
            try:
                username = User.objects.get(email__iexact=identifier).username
            except User.DoesNotExist:
                pass  # Will fail at authenticate() with a clear message

        user = authenticate(request=request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username/email or password.")
            return render(request, 'auth/login.html', {'identifier': identifier})

        if not user.is_active:
            messages.error(request, "Your account has been deactivated. Contact the administrator.")
            return render(request, 'auth/login.html', {'identifier': identifier})

        login(request, user)

        # Session expiry: 30 days if "remember me", else browser-close
        request.session.set_expiry(60 * 60 * 24 * 30 if remember_me else 0)

        if user.must_change_password:
            messages.info(request, "Please change your password before continuing.")
            return redirect('change_password')

        return redirect(_get_dashboard_url(user.role))

    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    """Log out the current user and redirect to login page."""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


# ---------------------------------------------------------------------------
# Registration - Separate Admin Views
# ---------------------------------------------------------------------------

@role_required('admin')
def register_student(request):
    """
    Admin-only: create a student account and send credentials by email.
    """
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = StudentForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                _create_user_and_profile(request, 'student', user_form, profile_form)
                return redirect('register_student')
            except Exception as exc:
                messages.error(request, f"Error creating student account: {exc}")

        return render(
            request,
            'auth/register_student.html',
            _registration_context(user_form, profile_form)
        )

    return render(
        request,
        'auth/register_student.html',
        _registration_context(UserRegistrationForm(), StudentForm())
    )


@role_required('admin')
def register_parent(request):
    """
    Admin-only: create a parent account and send credentials by email.
    """
    students = Student.objects.select_related('user').order_by('user__first_name')

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ParentForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                _create_user_and_profile(request, 'parent', user_form, profile_form)
                return redirect('register_parent')
            except Exception as exc:
                messages.error(request, f"Error creating parent account: {exc}")

        return render(
            request,
            'auth/register_parent.html',
            _registration_context(user_form, profile_form, students)
        )

    return render(
        request,
        'auth/register_parent.html',
        _registration_context(UserRegistrationForm(), ParentForm(), students)
    )


@role_required('admin')
def register_teacher(request):
    """
    Admin-only: create teacher account.
    teacher_id is auto-generated in Teacher model.
    """
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = TeacherForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                _create_user_and_profile(request, 'teacher', user_form, profile_form)
                messages.success(request, "Teacher account created successfully.")
                return redirect('register_teacher')

            except Exception as exc:
                messages.error(request, f"Error creating teacher account: {exc}")

        else:
            # helpful while debugging
            print("USER FORM ERRORS:", user_form.errors)
            print("TEACHER FORM ERRORS:", profile_form.errors)

        return render(
            request,
            'auth/register_teacher.html',
            _registration_context(user_form, profile_form)
        )

    return render(
        request,
        'auth/register_teacher.html',
        _registration_context(UserRegistrationForm(), TeacherForm())
    )

# ---------------------------------------------------------------------------
# Password Change (forced on first login)
# ---------------------------------------------------------------------------

@login_required
def change_password_view(request):
    """
    Force user to set a new password on first login.
    If already changed, redirect to their dashboard.
    """
    if not request.user.must_change_password:
        return redirect(_get_dashboard_url(request.user.role))

    form = ChangePasswordForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        current_password  = form.cleaned_data['current_password']
        new_password      = form.cleaned_data['new_password']

        # Verify current password
        if not request.user.check_password(current_password):
            form.add_error('current_password', "Current password is incorrect.")
            return render(request, 'auth/change_password.html', {'form': form})

        # Run Django's built-in password validators
        try:
            validate_password(new_password, request.user)
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
            return render(request, 'auth/change_password.html', {'form': form})

        # Save new password
        user = request.user
        user.set_password(new_password)
        user.must_change_password = False
        user.raw_password = ''        # Clear the plain-text copy
        user.save(update_fields=['password', 'must_change_password', 'raw_password'])

        messages.success(
            request,
            "Password changed successfully. Please log in with your new password."
        )

        # Log out so the user must sign in with the new password
        logout(request)
        return redirect('login')

    return render(request, 'auth/change_password.html', {'form': form})


# ---------------------------------------------------------------------------
# Dashboard dispatcher
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Redirect authenticated users to their role-specific dashboard."""
    if request.user.must_change_password:
        return redirect('change_password')
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return redirect(request.user.get_dashboard_url_name())




# ---------------------------------------------------------------------------
# User management (admin)
# ---------------------------------------------------------------------------

@role_required('admin')
def user_list_view(request):
    """List all users with optional role filter."""
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('-date_joined')
    if role_filter in dict(User.role_choices):
        users = users.filter(role=role_filter)

    context = {
        'page_title': 'User Management',
        'users': users,
        'role_filter': role_filter,
        'role_choices': User.role_choices,
    }
    return render(request, 'accounts/user_list.html', context)


@role_required('admin')
def toggle_user_status(request, user_id):
    """Toggle a user's is_active status."""
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        if target_user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        else:
            target_user.is_active = not target_user.is_active
            target_user.save(update_fields=['is_active'])
            status_label = "activated" if target_user.is_active else "deactivated"
            messages.success(request, f"User '{target_user.username}' has been {status_label}.")
    return redirect('user_list')


@role_required('admin')
def reset_user_password(request, user_id):
    """Reset a user's password to a new auto-generated one and email it."""
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        new_password = generate_password()
        target_user.set_password(new_password)
        target_user.raw_password = new_password
        target_user.must_change_password = True
        target_user.save(update_fields=['password', 'raw_password', 'must_change_password'])

        try:
            send_mail(
                subject="SmartSchool - Password Reset",
                message=(
                    f"Hello {target_user.get_full_name() or target_user.username},\n\n"
                    f"Your password has been reset by the administrator.\n\n"
                    f"Username : {target_user.username}\n"
                    f"Password : {new_password}\n\n"
                    f"Please log in and change your password immediately.\n\n"
                    f"Regards,\nSmartSchool Team"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[target_user.email],
                fail_silently=False,
            )
            messages.success(request, f"Password reset for '{target_user.username}'. Credentials emailed.")
        except Exception as exc:
            messages.warning(request, f"Password reset but email failed: {exc}")

    return redirect('user_list')
