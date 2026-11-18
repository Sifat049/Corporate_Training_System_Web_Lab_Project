"""
core/views.py - Notifications, Audit log, Reports (CSV export), Calendar, Protected file download.
"""
import calendar as pycalendar
import csv
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required, role_required
from accounts.models import User
from training.models import (
    EmployeeSkill, ModuleAssignment, Resource, Submission, Task, TrainingCategory,
)
from training.services import employee_avg_progress, employee_avg_skill, skill_gap_list

from .models import AuditLog, Notification
from .utils import audit, csv_safe, paginate, serve_file

ALL_ROLES = ("admin", "hr", "trainer", "employee")


# ---------------- Notifications ----------------
@role_required(*ALL_ROLES)
def notification_list(request):
    items = Notification.objects.filter(user=request.user)
    return render(request, "core/notifications.html", {"items": paginate(request, items, 15)})


@role_required(*ALL_ROLES)
def notification_open(request, pk):
    """Notification read mark kore tar link e pathay."""
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])
    target = n.url if n.url.startswith("/") and not n.url.startswith("//") else "/notifications/"
    return redirect(target)


@role_required(*ALL_ROLES)
@require_POST
def notification_read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("core:notifications")


# ---------------- Audit log (Admin) ----------------
@admin_required
def audit_log(request):
    q = request.GET.get("q", "").strip()
    logs = AuditLog.objects.all()
    if q:
        logs = logs.filter(Q(actor_name__icontains=q) | Q(action__icontains=q) | Q(detail__icontains=q))
    return render(request, "core/audit_log.html", {"logs": paginate(request, logs, 20), "q": q})


# ---------------- Reports (Admin + HR) ----------------
@role_required("admin", "hr")
def reports(request):
    employees = User.objects.filter(role=User.Role.EMPLOYEE, is_approved=True).select_related("employee_profile")
    dept = {}
    for e in employees:
        name = e.employee_profile.department or "Unassigned"
        row = dept.setdefault(name, {"department": name, "count": 0, "progress": [], "skill": []})
        row["count"] += 1
        row["progress"].append(employee_avg_progress(e))
        s = employee_avg_skill(e)
        if s:
            row["skill"].append(s)
    dept_rows = []
    for row in dept.values():
        dept_rows.append(
            {
                "department": row["department"],
                "count": row["count"],
                "avg_progress": round(sum(row["progress"]) / len(row["progress"])) if row["progress"] else 0,
                "avg_skill": round(sum(row["skill"]) / len(row["skill"]), 1) if row["skill"] else None,
            }
        )
    dept_rows.sort(key=lambda r: r["department"])
    cat_rows = []
    for c in TrainingCategory.objects.all():
        agg = EmployeeSkill.objects.filter(category=c).aggregate(avg=Avg("level"), n=Count("id"))
        cat_rows.append({"category": c, "avg": round(agg["avg"], 1) if agg["avg"] else None, "assessed": agg["n"]})
    status_counts = {
        s: ModuleAssignment.objects.filter(status=s).count() for s in ("not_started", "in_progress", "completed")
    }
    charts = {
        "dept": {
            "labels": [r["department"] for r in dept_rows],
            "series": [{"label": "Avg progress %", "values": [r["avg_progress"] for r in dept_rows]}],
            "max": 100,
        },
        "status": {
            "labels": ["Not started", "In progress", "Completed"],
            "values": [status_counts["not_started"], status_counts["in_progress"], status_counts["completed"]],
        },
    }
    return render(request, "core/reports.html", {"dept_rows": dept_rows, "cat_rows": cat_rows, "charts": charts, "status_counts": status_counts})


def _csv_response(filename, header, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("﻿")  # Excel e UTF-8 thik dekhanor jonno
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow([csv_safe(c) for c in row])
    return response


@role_required("admin", "hr")
def export_employees(request):
    rows = []
    for e in User.objects.filter(role=User.Role.EMPLOYEE, is_approved=True).select_related("employee_profile__trainer").order_by("first_name", "username"):
        p = e.employee_profile
        rows.append([e.username, e.display_name, e.email, p.department, p.job_title,
                     p.trainer.display_name if p.trainer else "", employee_avg_progress(e), employee_avg_skill(e) or ""])
    audit(request.user, "export", "employees.csv")
    return _csv_response("employees.csv", ["Username", "Name", "Email", "Department", "Job title", "Trainer", "Avg progress %", "Avg skill level"], rows)


@role_required("admin", "hr")
def export_progress(request):
    rows = [
        [a.employee.username, a.employee.display_name, a.module.title, a.module.category.name, a.get_status_display(),
         a.progress_percent, a.due_date or "", "Yes" if a.is_overdue else "No"]
        for a in ModuleAssignment.objects.select_related("employee", "module__category").filter(employee__is_approved=True)
    ]
    audit(request.user, "export", "progress.csv")
    return _csv_response("training_progress.csv", ["Username", "Name", "Module", "Category", "Status", "Progress %", "Due date", "Overdue"], rows)


@role_required("admin", "hr")
def export_gaps(request):
    rows = []
    employees = User.objects.filter(role=User.Role.EMPLOYEE, is_approved=True).select_related("employee_profile")
    for g in skill_gap_list(list(employees)):
        rows.append([g["employee"].username, g["employee"].display_name, g["category"].name, g["level"], g["required"], g["gap"]])
    audit(request.user, "export", "skill_gaps.csv")
    return _csv_response("skill_gaps.csv", ["Username", "Name", "Category", "Current level", "Required level", "Gap"], rows)


# ---------------- Calendar ----------------
def _events_for(user, start, end):
    """start..end (date) er moddhe due date wala jinis. Role onujayi alada."""
    events = []
    assignments = ModuleAssignment.objects.select_related("employee", "module").filter(due_date__range=(start, end))
    tasks = Task.objects.select_related("module").filter(due_date__range=(start, end))
    if user.role == User.Role.EMPLOYEE:
        assignments = assignments.filter(employee=user)
        mine = ModuleAssignment.objects.filter(employee=user).values_list("module_id", flat=True)
        tasks = tasks.filter(module_id__in=mine)
        submitted = set(Submission.objects.filter(employee=user).values_list("task_id", flat=True))
        for a in assignments:
            events.append({"date": a.due_date, "label": f"Module due: {a.module.title}", "kind": "module", "url": f"/employee/trainings/{a.pk}/"})
        for t in tasks:
            events.append({"date": t.due_date, "label": f"Task: {t.title}", "kind": "done" if t.id in submitted else "task",
                           "url": f"/employee/tasks/{t.pk}/submit/"})
    else:
        if user.role == User.Role.TRAINER:
            assignments = assignments.filter(employee__employee_profile__trainer=user)
            tasks = tasks.filter(module__created_by=user)
        elif user.role == User.Role.HR:
            tasks = tasks.none()
        for a in assignments:
            events.append({"date": a.due_date, "label": f"{a.employee.display_name}: {a.module.title}", "kind": "module", "url": ""})
        for t in tasks:
            events.append({"date": t.due_date, "label": f"Task: {t.title}", "kind": "task", "url": f"/modules/{t.module_id}/"})
    return events


@role_required(*ALL_ROLES)
def calendar_view(request):
    today = timezone.localdate()
    try:
        year, month = (int(x) for x in request.GET.get("month", "").split("-"))
        first = datetime.date(year, month, 1)
    except (ValueError, TypeError):
        first = today.replace(day=1)
    last_day = pycalendar.monthrange(first.year, first.month)[1]
    last = first.replace(day=last_day)
    events = _events_for(request.user, first, last)
    by_day = {}
    for ev in events:
        by_day.setdefault(ev["date"], []).append(ev)
    weeks = []
    for week in pycalendar.Calendar(firstweekday=0).monthdatescalendar(first.year, first.month):
        weeks.append([{"date": d, "in_month": d.month == first.month, "is_today": d == today, "events": by_day.get(d, [])} for d in week])
    prev_month = (first - datetime.timedelta(days=1)).replace(day=1)
    next_month = last + datetime.timedelta(days=1)
    upcoming = sorted([e for e in _events_for(request.user, today, today + datetime.timedelta(days=30))], key=lambda e: e["date"])[:8]
    return render(
        request, "core/calendar.html",
        {"weeks": weeks, "month_start": first, "prev_month": prev_month.strftime("%Y-%m"), "next_month": next_month.strftime("%Y-%m"),
         "upcoming": upcoming, "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
    )


# ---------------- Protected file download ----------------
@role_required(*ALL_ROLES)
def resource_file(request, pk):
    resource = get_object_or_404(Resource.objects.select_related("module"), pk=pk)
    user = request.user
    allowed = False
    if user.role in (User.Role.ADMIN, User.Role.HR):
        allowed = True
    elif user.role == User.Role.TRAINER:
        allowed = resource.module.created_by_id == user.id or ModuleAssignment.objects.filter(
            module=resource.module, employee__employee_profile__trainer=user
        ).exists()
    elif user.role == User.Role.EMPLOYEE:
        allowed = ModuleAssignment.objects.filter(employee=user, module=resource.module).exists()
    if not allowed:
        raise PermissionDenied
    return serve_file(request, resource.file, as_attachment=request.GET.get("download") == "1")


@role_required(*ALL_ROLES)
def submission_file(request, pk):
    sub = get_object_or_404(Submission.objects.select_related("employee__employee_profile", "task__module"), pk=pk)
    user = request.user
    allowed = False
    if user.role in (User.Role.ADMIN, User.Role.HR):
        allowed = True
    elif user.role == User.Role.EMPLOYEE:
        allowed = sub.employee_id == user.id
    elif user.role == User.Role.TRAINER:
        profile = getattr(sub.employee, "employee_profile", None)
        allowed = bool(profile and profile.trainer_id == user.id) or sub.task.module.created_by_id == user.id
    if not allowed:
        raise PermissionDenied
    return serve_file(request, sub.attachment, as_attachment=True)
