"""
100% version extra views: Certificate, Discussion (comments).
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import employee_required, role_required
from accounts.models import User
from core.utils import notify

from .forms import CommentForm
from .models import Certificate, Comment, ModuleAssignment, TrainingModule


# ---------------- Certificates ----------------
@employee_required
def employee_certificates(request):
    certs = Certificate.objects.filter(assignment__employee=request.user).select_related("assignment__module__category")
    return render(request, "employee_panel/certificates.html", {"certificates": certs})


def _can_view_certificate(user, cert):
    if user.role in (User.Role.ADMIN, User.Role.HR):
        return True
    employee = cert.assignment.employee
    if user.role == User.Role.EMPLOYEE:
        return employee_id_equal(user, employee)
    if user.role == User.Role.TRAINER:
        profile = getattr(employee, "employee_profile", None)
        return bool(profile and profile.trainer_id == user.id)
    return False


def employee_id_equal(user, employee):
    return user.id == employee.id


@role_required("admin", "hr", "trainer", "employee")
def certificate_view(request, pk):
    cert = get_object_or_404(Certificate.objects.select_related("assignment__employee", "assignment__module__category"), pk=pk)
    if not _can_view_certificate(request.user, cert):
        raise PermissionDenied
    return render(request, "shared/certificate.html", {"cert": cert, "assignment": cert.assignment, "public": False})


def certificate_verify(request, code):
    """Login chhara-i certificate code diye verify kora jay (public page)."""
    cert = Certificate.objects.select_related("assignment__employee", "assignment__module__category").filter(code=code.upper()).first()
    return render(request, "shared/certificate_verify.html", {"cert": cert, "code": code}, status=200 if cert else 404)


# ---------------- Discussion ----------------
def can_discuss(user, module):
    """Kara module discussion e likhte pare: Admin, module er Trainer, assigned Employee."""
    if user.role == User.Role.ADMIN:
        return True
    if user.role == User.Role.TRAINER:
        return module.created_by_id == user.id
    if user.role == User.Role.EMPLOYEE:
        return ModuleAssignment.objects.filter(employee=user, module=module).exists()
    return False


@role_required("admin", "trainer", "employee")
@require_POST
def comment_add(request, module_id):
    module = get_object_or_404(TrainingModule, pk=module_id)
    if not can_discuss(request.user, module):
        raise PermissionDenied
    form = CommentForm(request.POST)
    redirect_to = request.POST.get("next", "")
    if not form.is_valid():
        messages.error(request, "Please write a message (max 1000 characters).")
    else:
        parent = None
        parent_id = request.POST.get("parent", "")
        if parent_id.isdigit():
            parent = Comment.objects.filter(pk=int(parent_id), module=module, parent__isnull=True).first()
        comment = Comment.objects.create(module=module, author=request.user, parent=parent, body=form.cleaned_data["body"])
        if request.user.role == User.Role.EMPLOYEE:
            if module.created_by_id:
                notify(module.created_by, f"{request.user.display_name} posted in '{module.title}' discussion.", f"/modules/{module.pk}/")
        elif parent is not None and parent.author_id != request.user.id:
            employee_assignment = ModuleAssignment.objects.filter(employee=parent.author, module=module).first()
            url = f"/employee/trainings/{employee_assignment.pk}/" if employee_assignment else ""
            notify(parent.author, f"{request.user.display_name} replied to your question in '{module.title}'.", url)
        messages.success(request, "Posted.")
    if redirect_to.startswith("/") and not redirect_to.startswith("//"):
        return redirect(redirect_to)
    return redirect("accounts:dashboard")


@role_required("admin", "trainer", "employee")
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment.objects.select_related("module"), pk=pk)
    if not (request.user.role == User.Role.ADMIN or comment.author_id == request.user.id):
        raise PermissionDenied
    comment.delete()
    messages.success(request, "Comment deleted.")
    nxt = request.POST.get("next", "")
    if nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    return redirect("accounts:dashboard")
