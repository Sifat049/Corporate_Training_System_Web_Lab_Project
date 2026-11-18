"""Trainer er view: assigned employee dekha, module assign, submission evaluate + feedback."""
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import trainer_required
from accounts.models import User
from core.utils import notify, paginate

from .forms import AssignModuleForm, FeedbackForm
from .models import Feedback, ModuleAssignment, Submission, TrainingModule
from .services import (
    assignment_trainees,
    employee_avg_progress,
    employee_avg_skill,
    employee_skill_rows,
    update_skill_level,
)


def _my_submissions(trainer):
    return Submission.objects.filter(employee__employee_profile__trainer=trainer).select_related(
        "employee", "task__module__category"
    )


@trainer_required
def trainer_dashboard(request):
    trainees = list(assignment_trainees(request.user))
    submissions = _my_submissions(request.user)
    pending = submissions.filter(status=Submission.Status.SUBMITTED)
    stats = {
        "trainees": len(trainees),
        "modules": TrainingModule.objects.filter(created_by=request.user).count(),
        "pending": pending.count(),
        "evaluated": submissions.filter(status=Submission.Status.EVALUATED).count(),
    }
    rows = [(e.display_name, employee_avg_progress(e)) for e in trainees]
    charts = {
        "evaluation": {
            "labels": ["Pending evaluation", "Evaluated"],
            "values": [stats["pending"], stats["evaluated"]],
            "colors": ["#f59e0b", "#10b981"],
        },
        "progress": {
            "labels": [n for n, _ in rows],
            "datasets": [{"label": "Avg progress %", "values": [p for _, p in rows]}],
            "max": 100,
        },
    }
    return render(
        request,
        "trainer_panel/dashboard.html",
        {"stats": stats, "charts": charts, "pending_list": pending.order_by("submitted_at")[:6]},
    )


@trainer_required
def trainer_employees(request):
    employees = list(assignment_trainees(request.user).order_by("first_name", "username"))
    for e in employees:
        e.avg_skill = employee_avg_skill(e)
        e.avg_progress = employee_avg_progress(e)
        e.module_count = ModuleAssignment.objects.filter(employee=e).count()
    return render(request, "trainer_panel/employees.html", {"employees": employees})


@trainer_required
def trainer_employee_detail(request, pk):
    employee = get_object_or_404(assignment_trainees(request.user), pk=pk)
    return render(
        request,
        "trainer_panel/employee_detail.html",
        {
            "emp": employee,
            "skills": employee_skill_rows(employee),
            "assignments": ModuleAssignment.objects.filter(employee=employee).select_related("module__category"),
            "submissions": Submission.objects.filter(employee=employee).select_related("task__module", "feedback"),
            "avg_skill": employee_avg_skill(employee),
            "avg_progress": employee_avg_progress(employee),
        },
    )


@trainer_required
def trainer_assign(request):
    form = AssignModuleForm(request.POST or None, trainer=request.user)
    if not form.fields["employee"].queryset.exists():
        messages.info(request, "You have no assigned employees yet. Ask the HR Manager to assign employees to you.")
    if request.method == "POST":
        if form.is_valid():
            assignment = ModuleAssignment.objects.create(
                employee=form.cleaned_data["employee"],
                module=form.cleaned_data["module"],
                due_date=form.cleaned_data["due_date"],
                assigned_by=request.user,
            )
            assignment.recalculate()
            notify(
                assignment.employee,
                f"New training assigned: {assignment.module.title}",
                f"/employee/trainings/{assignment.pk}/",
            )
            messages.success(
                request, f"'{assignment.module.title}' was assigned to {assignment.employee.display_name}."
            )
            return redirect("training:trainer_assign")
        messages.error(request, "Please correct the errors below.")
    assignments = ModuleAssignment.objects.filter(employee__employee_profile__trainer=request.user).select_related(
        "employee", "module__category"
    )
    return render(request, "trainer_panel/assign.html", {"form": form, "assignments": assignments})


@trainer_required
@require_POST
def trainer_assignment_delete(request, pk):
    assignment = get_object_or_404(
        ModuleAssignment, pk=pk, employee__employee_profile__trainer=request.user
    )
    assignment.delete()
    messages.success(request, "Assignment removed.")
    return redirect("training:trainer_assign")


@trainer_required
def trainer_submissions(request):
    status = request.GET.get("status", "")
    submissions = _my_submissions(request.user)
    if status in (Submission.Status.SUBMITTED, Submission.Status.EVALUATED):
        submissions = submissions.filter(status=status)
    return render(request, "trainer_panel/submissions.html", {"submissions": paginate(request, submissions, 10), "status": status})


@trainer_required
def trainer_evaluate(request, pk):
    # Shudhu nijer trainee der submission evaluate kora jabe (onnoder holey 404)
    submission = get_object_or_404(_my_submissions(request.user), pk=pk)
    feedback = Feedback.objects.filter(submission=submission).first()
    form = FeedbackForm(request.POST or None, instance=feedback, submission=submission)
    if request.method == "POST":
        if form.is_valid():
            fb = form.save(commit=False)
            fb.submission = submission
            fb.trainer = request.user
            fb.save()
            submission.status = Submission.Status.EVALUATED
            submission.save(update_fields=["status", "updated_at"])
            # Evaluate korle employee er skill level auto update hoy
            update_skill_level(submission.employee, submission.task.module.category)
            notify(
                submission.employee,
                f"Your submission '{submission.task.title}' was evaluated: {fb.score}/{submission.task.max_score}.",
                "/employee/feedback/",
            )
            messages.success(request, "Evaluation and feedback saved. The employee's skill level was updated.")
            return redirect("training:trainer_submissions")
        messages.error(request, "Please correct the errors below.")
    return render(request, "trainer_panel/evaluate.html", {"submission": submission, "form": form, "feedback": feedback})
