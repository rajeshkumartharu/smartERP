from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

from apps.accounts.forms import UserRegistrationForm
from apps.students.studentforms import StudentForm
from apps.teachers.teacherforms import TeacherForm
from apps.parents.parentforms import ParentForm
from apps.students.models import Student
from apps.core.utils.password_generator import generate_password


def register_view(request):

    # Pre-load student list for parent form dropdown
    students = Student.objects.select_related('user').all()

    if request.method == "POST":

        role = request.POST.get("role")
        user_form = UserRegistrationForm(request.POST)

        # ---------------- ROLE VALIDATION ----------------
        if role not in ["student", "teacher", "parent"]:
            return render(request, "auth/register.html", {
                "user_form": UserRegistrationForm(request.POST),
                "students": students,
                "error": {"role": ["Invalid role selected."]},
                "selected_role": role,
            })

        # ---------------- USER FORM VALIDATION ----------------
        if not user_form.is_valid():
            return render(request, "auth/register.html", {
                "user_form": user_form,
                "students": students,
                "error": dict(user_form.errors),
                "selected_role": role,
            })

        # ---------------- PROFILE FORM VALIDATION (before saving user) ----------------
        if role == "student":
            profile_form = StudentForm(request.POST, request.FILES)
        elif role == "teacher":
            profile_form = TeacherForm(request.POST, request.FILES)
        else:
            profile_form = ParentForm(request.POST, request.FILES)

        if not profile_form.is_valid():
            # Convert ErrorDict → plain dict so template can iterate .items
            return render(request, "auth/register.html", {
                "user_form": user_form,
                "students": students,
                "error": dict(profile_form.errors),
                "selected_role": role,
            })

        # ---------------- SAVE (atomic) ----------------
        try:
            with transaction.atomic():

                # Generate password
                raw_password = generate_password()

                # Create user
                user = user_form.save(commit=False)
                user.role = role
                user.set_password(raw_password)
                user.raw_password = raw_password
                user.must_change_password = True
                user.save()

                # Save profile
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()

                # ManyToMany (Parent → Student links)
                if role == "parent":
                    profile_form.save_m2m()

                # Send email
                send_mail(
                    subject="SmartSchool Login Credentials",
                    message=(
                        f"Hello {user.get_full_name() or user.username},\n\n"
                        f"Your {role.capitalize()} account has been created successfully.\n\n"
                        f"Username : {user.username}\n"
                        f"Password : {raw_password}\n\n"
                        f"Please log in and change your password immediately.\n\n"
                        f"Regards,\nSmartSchool Team"
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                messages.success(
                    request,
                    f"{role.capitalize()} account created successfully! "
                    f"Credentials have been sent to {user.email}."
                )
                return redirect("login")

        except Exception as e:
            return render(request, "auth/register.html", {
                "user_form": UserRegistrationForm(request.POST),
                "students": students,
                "error": {"Server error": [str(e)]},
                "selected_role": role,
            })

    # ---------------- GET ----------------
    return render(request, "auth/register.html", {
        "user_form": UserRegistrationForm(),
        "students": students,
        "selected_role": "student",
    })


