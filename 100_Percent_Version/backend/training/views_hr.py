"""HR Manager er view: employee profile, skill level, skill gap, trainer assign, progress monitor."""
from django.contrib import messages
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import hr_required
from accounts.models import User
from core.utils import paginate

from .forms import AssignTrainerForm
from .models import EmployeeSkill, ModuleAssignment, Submission, TrainingCategory
from .services import (
    employee_avg_progress,
    employee_avg_skill,
    employee_skill_rows,
    skill_gap_list,
)


def _approved_employees():
    return User.objects.filter(role=User.Role.EMPLOYEE, is_approved=True).select_related("employee_profile__trainer")


@hr_required
def hr_dashboard(request):
    employees = list(_approved_employees())
    categories = list(TrainingCategory.objects.all())
    gaps = skill_gap_list(employees, categories)
    assigned = [e for e in employees if e.employee_profile.trainer_id]

    skill_counts = {level: 0 for level in range(1, 6)}
    for skill in EmployeeSkill.objects.filter(employee__in=employees):
        skill_counts[skill.level] += 1

    progress_rows = []
    for e in employees:
        progress_rows.append((e.display_name, employee_avg_progress(e)))
    stats = {
        "employees": len(employees),
        "with_trainer": len(assigned),
        "without_trainer": len(employees) - len(assigned),
        "gaps": len(gaps),
        "avg_progress": ModuleAssignment.objects.aggregate(a=Avg("progress_percent"))["a"] or 0,
        "completed": ModuleAssignment.objects.filter(status="completed").count(),
    }
    stats["avg_progress"] = round(stats["avg_progress"])
    charts = {
        "skills": {
            "labels": ["Beginner", "Basic", "Intermediate", "Advanced", "Expert"],
            "datasets": [{"label": "Employees x categories", "values": [skill_counts[i] for i in range(1, 6)]}],
        },
        "progress": {
            "labels": [name for name, _ in progress_rows],
            "datasets": [{"label": "Avg progress %", "values": [p for _, p in progress_rows]}],
            "max": 100,
        },
    }
    return render(
        request,
        "hr_panel/dashboard.html",
        {"stats": stats, "charts": charts, "top_gaps": gaps[:6], "unassigned": [e for e in employees if not e.employee_profile.trainer_id][:5]},
    )


@hr_required
def hr_employees(request):
    q = request.GET.get("q", "").strip()
    department = request.GET.get("department", "").strip()
    employees = _approved_employees()
    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q) | Q(email__icontains=q)
        )
    if department:
        employees = employees.filter(employee_profile__department=department)
    employees = paginate(request, employees.order_by("first_name", "username"), 10)
    employees.object_list = list(employees.object_list)
    for e in employees:
        e.avg_skill = employee_avg_skill(e)
        e.avg_progress = employee_avg_progress(e)
    departments = (
        User.objects.filter(role=User.Role.EMPLOYEE, is_approved=True)
        .exclude(employee_profile__department="")
        .values_list("employee_profile__department", flat=True)
        .distinct()
        .order_by("employee_profile__department")
    )
    trainer_form = AssignTrainerForm()
    return render(
        request,
        "hr_panel/employee_list.html",
        {"employees": employees, "q": q, "department": department, "departments": departments, "trainer_form": trainer_form},
    )


@hr_required
def hr_employee_detail(request, pk):
    employee = get_object_or_404(_approved_employees(), pk=pk)
    assignments = ModuleAssignment.objects.filter(employee=employee).select_related("module__category")
    submissions = Submission.objects.filter(employee=employee).select_related("task__module", "feedback")
    form = AssignTrainerForm(initial={"trainer": employee.employee_profile.trainer})
    return render(
        request,
        "hr_panel/employee_detail.html",
        {
            "emp": employee,
            "skills": employee_skill_rows(employee),
            "assignments": assignments,
            "submissions": submissions,
            "trainer_form": form,
            "avg_skill": employee_avg_skill(employee),
            "avg_progress": employee_avg_progress(employee),
        },
    )


@hr_required
@require_POST
def hr_assign_trainer(request, pk):
    employee = get_object_or_404(_approved_employees(), pk=pk)
    form = AssignTrainerForm(request.POST)
    if form.is_valid():
        trainer = form.cleaned_data["trainer"]
        profile = employee.employee_profile
        profile.trainer = trainer
        profile.save(update_fields=["trainer"])
        from core.utils import audit, notify

        audit(request.user, "trainer_assigned", f"{employee.username} -> {trainer.username if trainer else 'none'}")
        if trainer:
            notify(employee, f"{trainer.display_name} is now your trainer.", "/employee/")
            notify(trainer, f"{employee.display_name} was assigned to you.", "/trainer/employees/")
        if trainer:
            messages.success(request, f"{employee.display_name} is now assigned to trainer {trainer.display_name}.")
        else:
            messages.info(request, f"Trainer removed from {employee.display_name}.")
    else:
        messages.error(request, "Invalid trainer selected.")
    return redirect(request.POST.get("next") or "training:hr_employees")


@hr_required
def hr_skill_gaps(request):
    categories = list(TrainingCategory.objects.all())
    try:
        category_id = int(request.GET.get("category") or 0)
    except ValueError:
        category_id = 0
    gaps = skill_gap_list(list(_approved_employees()), categories, category_id or None)
    return render(
        request,
        "hr_panel/skill_gaps.html",
        {"gaps": gaps, "categories": categories, "category_id": category_id},
    )


@hr_required
def hr_progress(request):
    status = request.GET.get("status", "")
    assignments = ModuleAssignment.objects.select_related(
        "employee__employee_profile__trainer", "module__category"
    ).filter(employee__is_approved=True)
    if status in ("not_started", "in_progress", "completed"):
        assignments = assignments.filter(status=status)
    return render(request, "hr_panel/progress.html", {"assignments": paginate(request, assignments, 12), "status": status})
