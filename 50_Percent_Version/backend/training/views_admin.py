"""
Admin er shob view: dashboard, HR/Trainer management, employee approval, category CRUD.
Prottek view er upor @admin_required ache - tai onno role dhukte parbe na.
"""
from django.contrib import messages
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required
from accounts.forms import StaffCreateForm
from accounts.models import User

from .forms import CategoryForm
from .models import ModuleAssignment, Submission, TrainingCategory, TrainingModule


@admin_required
def admin_dashboard(request):
    employees = User.objects.filter(role=User.Role.EMPLOYEE)
    assignments = ModuleAssignment.objects.all()
    status_counts = {row["status"]: row["n"] for row in assignments.values("status").annotate(n=Count("id"))}

    stats = {
        "employees": employees.filter(is_approved=True).count(),
        "pending": employees.filter(is_approved=False).count(),
        "trainers": User.objects.filter(role=User.Role.TRAINER).count(),
        "hr": User.objects.filter(role=User.Role.HR).count(),
        "categories": TrainingCategory.objects.count(),
        "modules": TrainingModule.objects.count(),
        "assignments": assignments.count(),
        "submissions": Submission.objects.count(),
        "evaluated": Submission.objects.filter(status=Submission.Status.EVALUATED).count(),
    }
    completed = status_counts.get("completed", 0)
    stats["completion_rate"] = round(completed * 100 / stats["assignments"]) if stats["assignments"] else 0

    categories = TrainingCategory.objects.annotate(n=Count("modules"))
    charts = {
        "status": {
            "labels": ["Not Started", "In Progress", "Completed"],
            "values": [
                status_counts.get("not_started", 0),
                status_counts.get("in_progress", 0),
                status_counts.get("completed", 0),
            ],
            "colors": ["#94a3b8", "#f59e0b", "#10b981"],
        },
        "categories": {
            "labels": [c.name for c in categories],
            "datasets": [{"label": "Modules", "values": [c.n for c in categories]}],
        },
    }
    context = {
        "stats": stats,
        "charts": charts,
        "pending_employees": employees.filter(is_approved=False).order_by("-date_joined")[:5],
        "recent_submissions": Submission.objects.select_related("employee", "task__module")[:6],
    }
    return render(request, "admin_panel/dashboard.html", context)


# ---------------- HR Manager & Trainer management ----------------
@admin_required
def staff_list(request):
    role = request.GET.get("role", "")
    staff = User.objects.filter(role__in=[User.Role.HR, User.Role.TRAINER]).order_by("role", "first_name", "username")
    if role in (User.Role.HR, User.Role.TRAINER):
        staff = staff.filter(role=role)
    return render(request, "admin_panel/staff_list.html", {"staff": staff, "role": role})


@admin_required
def staff_add(request):
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            messages.success(request, f"{user.get_role_display()} '{user.display_name}' was created successfully.")
            return redirect("training:staff_list")
        messages.error(request, "Please correct the errors below.")
    return render(
        request,
        "shared/form.html",
        {
            "form": form,
            "title": "Add HR Manager / Trainer",
            "subtitle": "Create a staff account. They can log in immediately with these credentials.",
            "cancel_url": "training:staff_list",
            "submit_label": "Create account",
        },
    )


@admin_required
@require_POST
def staff_delete(request, pk):
    user = get_object_or_404(User, pk=pk, role__in=[User.Role.HR, User.Role.TRAINER])
    name = user.display_name
    user.delete()
    messages.success(request, f"'{name}' was removed.")
    return redirect("training:staff_list")


# ---------------- Employee approval ----------------
@admin_required
def admin_employees(request):
    status = request.GET.get("status", "pending")
    q = request.GET.get("q", "").strip()
    employees = User.objects.filter(role=User.Role.EMPLOYEE).select_related("employee_profile__trainer")
    if status == "pending":
        employees = employees.filter(is_approved=False)
    elif status == "approved":
        employees = employees.filter(is_approved=True)
    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(email__icontains=q)
        )
    pending_count = User.objects.filter(role=User.Role.EMPLOYEE, is_approved=False).count()
    return render(
        request,
        "admin_panel/employee_list.html",
        {"employees": employees.order_by("-date_joined"), "status": status, "q": q, "pending_count": pending_count},
    )


@admin_required
@require_POST
def employee_approve(request, pk):
    employee = get_object_or_404(User, pk=pk, role=User.Role.EMPLOYEE)
    employee.is_approved = True
    employee.save(update_fields=["is_approved"])
    messages.success(request, f"{employee.display_name}'s account has been approved.")
    return redirect(request.POST.get("next") or "training:admin_employees")


@admin_required
@require_POST
def employee_delete(request, pk):
    employee = get_object_or_404(User, pk=pk, role=User.Role.EMPLOYEE)
    name = employee.display_name
    employee.delete()
    messages.success(request, f"Employee account '{name}' was removed.")
    return redirect("training:admin_employees")


# ---------------- Category CRUD ----------------
@admin_required
def category_list(request):
    categories = TrainingCategory.objects.annotate(module_count=Count("modules"))
    return render(request, "admin_panel/category_list.html", {"categories": categories})


@admin_required
def category_add(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect("training:category_list")
        messages.error(request, "Please correct the errors below.")
    return render(
        request,
        "shared/form.html",
        {"form": form, "title": "Add Training Category", "cancel_url": "training:category_list", "submit_label": "Save category"},
    )


@admin_required
def category_edit(request, pk):
    category = get_object_or_404(TrainingCategory, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("training:category_list")
        messages.error(request, "Please correct the errors below.")
    return render(
        request,
        "shared/form.html",
        {"form": form, "title": f"Edit Category: {category.name}", "cancel_url": "training:category_list", "submit_label": "Update category"},
    )


@admin_required
@require_POST
def category_delete(request, pk):
    category = get_object_or_404(TrainingCategory, pk=pk)
    try:
        category.delete()
        messages.success(request, f"Category '{category.name}' was deleted.")
    except ProtectedError:
        messages.error(request, "This category has training modules, so it cannot be deleted. Remove or move the modules first.")
    return redirect("training:category_list")
