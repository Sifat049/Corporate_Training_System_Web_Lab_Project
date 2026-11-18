"""Employee er view: dashboard, assigned module, lesson complete, task submit, feedback."""
from django.contrib import messages
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import employee_required

from .forms import SubmissionForm
from .models import Feedback, Lesson, LessonCompletion, ModuleAssignment, Submission, Task
from .services import employee_avg_progress, employee_skill_rows, tasks_for_employee


@employee_required
def employee_dashboard(request):
    user = request.user
    assignments = list(ModuleAssignment.objects.filter(employee=user).select_related("module__category"))
    tasks = tasks_for_employee(user)
    feedbacks = Feedback.objects.filter(submission__employee=user).select_related("submission__task", "trainer")
    avg_score = feedbacks.aggregate(a=Avg("score"))["a"]
    percentages = [f.percentage for f in feedbacks]
    skills = employee_skill_rows(user)

    stats = {
        "assigned": len(assignments),
        "completed": sum(1 for a in assignments if a.status == "completed"),
        "avg_progress": employee_avg_progress(user),
        "pending_tasks": sum(1 for t in tasks if t.state in ("pending", "overdue")),
        "avg_score": round(sum(percentages) / len(percentages)) if percentages else None,
    }
    charts = {
        "progress": {
            "labels": [a.module.title for a in assignments],
            "datasets": [{"label": "Progress %", "values": [a.progress_percent for a in assignments]}],
            "max": 100,
        },
        "skills": {
            "labels": [s["category"].name for s in skills],
            "datasets": [
                {"label": "Your level", "values": [s["level"] for s in skills]},
                {"label": "Required level", "values": [s["required"] for s in skills]},
            ],
            "max": 5,
        },
    }
    return render(
        request,
        "employee_panel/dashboard.html",
        {
            "stats": stats,
            "charts": charts,
            "assignments": assignments[:4],
            "pending_tasks": [t for t in tasks if t.state in ("pending", "overdue")][:5],
            "recent_feedback": feedbacks[:3],
            "skills": skills,
            "avg_score_raw": avg_score,
        },
    )


@employee_required
def employee_trainings(request):
    assignments = ModuleAssignment.objects.filter(employee=request.user).select_related(
        "module__category", "assigned_by"
    )
    status = request.GET.get("status", "")
    if status in ("not_started", "in_progress", "completed"):
        assignments = assignments.filter(status=status)
    return render(request, "employee_panel/trainings.html", {"assignments": assignments, "status": status})


@employee_required
def employee_training_detail(request, pk):
    # Employee shudhu nijer assign kora module dekhte pabe
    assignment = get_object_or_404(
        ModuleAssignment.objects.select_related("module__category", "assigned_by"), pk=pk, employee=request.user
    )
    module = assignment.module
    done_ids = set(assignment.completions.values_list("lesson_id", flat=True))
    lessons = list(module.lessons.all())
    for lesson in lessons:
        lesson.done = lesson.id in done_ids
    tasks = [t for t in tasks_for_employee(request.user) if t.module_id == module.id]
    return render(
        request,
        "employee_panel/training_detail.html",
        {
            "assignment": assignment,
            "module": module,
            "lessons": lessons,
            "resources": module.resources.all(),
            "tasks": tasks,
        },
    )


@employee_required
@require_POST
def employee_lesson_toggle(request, assignment_id, lesson_id):
    assignment = get_object_or_404(ModuleAssignment, pk=assignment_id, employee=request.user)
    lesson = get_object_or_404(Lesson, pk=lesson_id, module=assignment.module)
    completion, created = LessonCompletion.objects.get_or_create(assignment=assignment, lesson=lesson)
    if created:
        messages.success(request, f"Lesson '{lesson.title}' marked as complete.")
    else:
        completion.delete()
        messages.info(request, f"Lesson '{lesson.title}' marked as not complete.")
    assignment.recalculate()
    return redirect("training:employee_training_detail", pk=assignment.pk)


@employee_required
def employee_tasks(request):
    tasks = tasks_for_employee(request.user)
    state = request.GET.get("state", "")
    if state:
        tasks = [t for t in tasks if t.state == state]
    return render(request, "employee_panel/tasks.html", {"tasks": tasks, "state": state})


@employee_required
def employee_task_submit(request, pk):
    task = get_object_or_404(Task.objects.select_related("module"), pk=pk)
    # Task er module employee ke assign kora na thakle access nai
    assignment = get_object_or_404(ModuleAssignment, employee=request.user, module=task.module)
    submission = Submission.objects.filter(task=task, employee=request.user).first()
    if submission and submission.status == Submission.Status.EVALUATED:
        messages.info(request, "This task is already evaluated, so it can no longer be changed.")
        return redirect("training:employee_feedback")

    form = SubmissionForm(request.POST or None, request.FILES or None, instance=submission)
    if request.method == "POST":
        if form.is_valid():
            sub = form.save(commit=False)
            sub.task = task
            sub.employee = request.user
            sub.status = Submission.Status.SUBMITTED
            sub.save()
            assignment.recalculate()
            messages.success(request, "Your submission was saved. Your trainer will evaluate it soon.")
            return redirect("training:employee_training_detail", pk=assignment.pk)
        messages.error(request, "Please correct the errors below.")
    return render(
        request,
        "employee_panel/task_submit.html",
        {"task": task, "form": form, "submission": submission, "assignment": assignment},
    )


@employee_required
def employee_feedback(request):
    feedbacks = Feedback.objects.filter(submission__employee=request.user).select_related(
        "submission__task__module", "trainer"
    )
    return render(request, "employee_panel/feedback.html", {"feedbacks": feedbacks})
