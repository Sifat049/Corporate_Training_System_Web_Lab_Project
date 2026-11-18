"""
accounts/views.py - login, logout, register, dashboard redirect, profile.

Banglish note:
View = Python function (ba class) je browser er request ney, kichu kaj kore (database query, form check)
ar shesh e HTML response (template render) ba redirect return kore.
"""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from .decorators import role_required
from .models import User
from .forms import (
    EmployeeProfileForm,
    EmployeeRegistrationForm,
    LoginForm,
    ProfileForm,
    StyledFormMixin,
)

# Kon role login korle kon dashboard e jabe
ROLE_HOME = {
    "admin": "training:admin_dashboard",
    "hr": "training:hr_dashboard",
    "trainer": "training:trainer_dashboard",
    "employee": "training:employee_dashboard",
}


class RoleLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse("accounts:dashboard")

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().display_name}!")
        return super().form_valid(form)


def home(request):
    return redirect("accounts:dashboard")


@login_required
def dashboard_redirect(request):
    """Login er por user er role dekhe sothik dashboard e pathay."""
    if not request.user.is_approved:
        from django.contrib.auth import logout

        logout(request)
        messages.warning(request, "Your account is waiting for admin approval.")
        return redirect("accounts:login")
    return redirect(ROLE_HOME.get(request.user.role, "accounts:login"))


def register(request):
    """Employee self-registration. Account Admin approve na kora porjonto login kora jabe na."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = EmployeeRegistrationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            new_user = form.save()
            from core.utils import notify_many

            notify_many(
                User.objects.filter(role=User.Role.ADMIN),
                f"New employee registration waiting for approval: {new_user.display_name}",
                "/admin-panel/employees/",
            )
            messages.success(
                request,
                "Registration successful! Your account will be activated after Admin approval.",
            )
            return redirect("accounts:login")
        messages.error(request, "Please correct the errors below.")
    return render(request, "accounts/register.html", {"form": form})


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    pass


@role_required("admin", "hr", "trainer", "employee")
def profile(request):
    user = request.user
    user_form = ProfileForm(request.POST or None, instance=user, prefix="user")
    profile_form = None
    if user.is_employee:
        profile_form = EmployeeProfileForm(request.POST or None, instance=user.employee_profile, prefix="emp")

    if request.method == "POST":
        valid = user_form.is_valid() and (profile_form is None or profile_form.is_valid())
        if valid:
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the errors below.")
    return render(request, "accounts/profile.html", {"user_form": user_form, "profile_form": profile_form})


@role_required("admin", "hr", "trainer", "employee")
def password_change(request):
    form = StyledPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # password bodlale logout hoye na jay
            messages.success(request, "Password changed successfully.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the errors below.")
    return render(request, "accounts/password_change.html", {"form": form})


# ---------- Custom error pages ----------
def permission_denied_view(request, exception=None):
    return render(request, "403.html", status=403)


def not_found_view(request, exception=None):
    return render(request, "404.html", status=404)
