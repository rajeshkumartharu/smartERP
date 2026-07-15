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


def _create_user_and_profile(request, role, user_form, profile_form, notify=True):
    """
    Shared function to create user + role profile and send credentials email.
    Used by student / teacher / parent registration views.

    Returns (user, profile).

    `notify=False` skips the "account created" flash message (useful when the
    caller — e.g. combined student+guardian registration — wants to show one
    consolidated success message instead of one per account). Email is always
    sent regardless of `notify`.
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
        profile.save()  # student_id / parent_id auto-generated inside model.save()

        # Save many-to-many relations for parent form if needed
        if role == 'parent':
            profile_form.save_m2m()

    # Send email after successful DB save
    try:
        _send_credentials_email(request, user, raw_password, role)
        if notify:
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

    return user, profile


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
# Registration - Combined Student + Guardian (admin)
# ---------------------------------------------------------------------------

@role_required('admin')
def register_student(request):
    """
    Admin-only: create a student account together with a guardian.

    One submit either:
      - creates BOTH a student account and a brand-new guardian account, or
      - creates the student account and links it to an EXISTING guardian.

    Two independent (User, UserRegistrationForm) + (Profile, ProfileForm)
    pairs are bound from one POST, disambiguated via Django's form `prefix`:
    'student-first_name', 'parent-first_name', etc.
    """
    from apps.academics.models import Level, SchoolClass, Section, AcademicYear

    existing_parents = Parent.objects.select_related('user').order_by(
        'user__first_name', 'user__last_name'
    )
    levels = Level.objects.all()
    classes = SchoolClass.objects.select_related('level').all()
    sections = Section.objects.select_related('school_class').all()
    academic_years = AcademicYear.objects.all()

    def _blank_context(guardian_mode='new', **overrides):
        context = {
            'user_form': UserRegistrationForm(prefix='student'),
            'profile_form': StudentForm(prefix='student'),
            'parent_user_form': UserRegistrationForm(prefix='parent'),
            'parent_profile_form': ParentForm(prefix='parent'),
            'parents': existing_parents,
            'guardian_mode': guardian_mode,
            'levels': levels,
            'classes': classes,
            'sections': sections,
            'academic_years': academic_years,
        }
        context.update(overrides)
        return context

    if request.method != 'POST':
        return render(request, 'auth/register_student.html', _blank_context())

    guardian_mode = request.POST.get('guardian_mode', 'new')

    student_user_form = UserRegistrationForm(request.POST, prefix='student')
    student_profile_form = StudentForm(request.POST, request.FILES, prefix='student')

    parent = None
    parent_user_form = None
    parent_profile_form = None

    if guardian_mode == 'existing':
        parent_id = request.POST.get('existing_parent')
        if not parent_id:
            messages.error(
                request,
                "Please select a guardian to link, or switch to 'Create new guardian'."
            )
            return render(request, 'auth/register_student.html', _blank_context(
                guardian_mode=guardian_mode,
                user_form=student_user_form,
                profile_form=student_profile_form,
            ))
        parent = get_object_or_404(Parent, pk=parent_id)
    else:
        parent_user_form = UserRegistrationForm(request.POST, prefix='parent')
        parent_profile_form = ParentForm(request.POST, request.FILES, prefix='parent')

    forms_valid = (
        student_user_form.is_valid()
        and student_profile_form.is_valid()
        and (parent is not None or (parent_user_form.is_valid() and parent_profile_form.is_valid()))
    )

    if not forms_valid:
        # Still print for the console, but ALSO surface errors in the browser —
        # print() alone is invisible to the person filling the form.
        print("STUDENT USER FORM ERRORS:", student_user_form.errors)
        print("STUDENT PROFILE FORM ERRORS:", student_profile_form.errors)
        if parent_user_form is not None:
            print("PARENT USER FORM ERRORS:", parent_user_form.errors)
            print("PARENT PROFILE FORM ERRORS:", parent_profile_form.errors)

        combined_errors = {}
        for prefix_label, form in (
            ("Student", student_user_form),
            ("Student profile", student_profile_form),
            ("Guardian", parent_user_form),
            ("Guardian profile", parent_profile_form),
        ):
            if form is None:
                continue
            for field, errs in form.errors.items():
                label = field if field != "__all__" else "General"
                combined_errors[f"{prefix_label} — {label}"] = errs

        messages.error(
            request,
            "Please fix the errors highlighted below before submitting."
        )

        return render(request, 'auth/register_student.html', _blank_context(
            guardian_mode=guardian_mode,
            user_form=student_user_form,
            profile_form=student_profile_form,
            parent_user_form=parent_user_form or UserRegistrationForm(prefix='parent'),
            parent_profile_form=parent_profile_form or ParentForm(prefix='parent'),
            error=combined_errors,
        ))

    try:
        with transaction.atomic():
            # 1) Student account + profile (student_id auto-generated)
            student_user, student = _create_user_and_profile(
                request, 'student', student_user_form, student_profile_form, notify=False
            )

            # 2) Guardian: create new, or reuse existing
            if guardian_mode == 'new':
                parent_user, parent = _create_user_and_profile(
                    request, 'parent', parent_user_form, parent_profile_form, notify=False
                )

            # 3) Link them explicitly — safe even if the parent form's own
            #    'students' selection was empty/stale (the new student won't
            #    have existed yet when that form was rendered).
            parent.students.add(student)

        messages.success(
            request,
            f"Student '{student.student_id}' created"
            + (f" with new guardian '{parent.parent_id}'"
               if guardian_mode == 'new'
               else f" and linked to existing guardian '{parent.parent_id}'")
            + ". Login credentials have been emailed to each person."
        )
        return redirect('register_student')

    except Exception as exc:
        messages.error(request, f"Error creating accounts: {exc}")
        return render(request, 'auth/register_student.html', _blank_context(
            guardian_mode=guardian_mode,
            user_form=student_user_form,
            profile_form=student_profile_form,
            parent_user_form=parent_user_form or UserRegistrationForm(prefix='parent'),
            parent_profile_form=parent_profile_form or ParentForm(prefix='parent'),
        ))


@role_required('admin')
def register_parent(request):
    """
    Admin-only: register an additional guardian later and link them to one
    or more existing students. (The combined `register_student` view above
    is the primary path for new admissions; this stays for adding a second
    guardian to a student who already exists.)
    """
    students = Student.objects.select_related('user').all()

    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ParentForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                user, parent = _create_user_and_profile(
                    request,
                    role='parent',
                    user_form=user_form,
                    profile_form=profile_form
                )

                messages.success(request, "Parent registered successfully!")
                return redirect('register_parent')

            except Exception as exc:
                messages.error(request, f"Error: {exc}")

    else:
        user_form = UserRegistrationForm()
        profile_form = ParentForm()

    return render(
        request,
        'auth/register_parent.html',
        _registration_context(user_form, profile_form, students)
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