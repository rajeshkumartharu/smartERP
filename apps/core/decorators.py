from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    """
    Decorator that allows access only to authenticated users with one of the
    specified roles. Also forces a password change if must_change_password=True.

    Usage:
        @role_required('admin')
        @role_required('admin', 'teacher')   # multiple roles allowed
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Force first-login password change
            if request.user.must_change_password:
                messages.warning(
                    request,
                    "Please change your temporary password before continuing."
                )
                return redirect('change_password')

            # Role check (superusers may access admin-only views)
            allowed = request.user.role in roles
            if not allowed and 'admin' in roles and request.user.is_superuser:
                allowed = True

            if not allowed:
                messages.error(
                    request,
                    "You are not authorised to access this page."
                )
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator