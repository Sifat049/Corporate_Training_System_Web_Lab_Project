"""
Role-based access control (RBAC).

Banglish note:
Decorator = ekta function er upor @name likhle oi function e extra kaj jure jay.
@role_required("admin") likhle sudhu admin user oi view khulte parbe,
onno role hole 403 Forbidden page dekhabe. Eta diyei amra "Employee admin page e dhukte parbe na"
requirement ta implement korechi.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not user.is_approved:
                logout(request)
                messages.warning(request, "Your account is not approved yet.")
                return redirect("accounts:login")
            if user.role not in roles:
                raise PermissionDenied  # 403 page
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


admin_required = role_required("admin")
hr_required = role_required("hr")
trainer_required = role_required("trainer")
employee_required = role_required("employee")
module_manager_required = role_required("admin", "trainer")
