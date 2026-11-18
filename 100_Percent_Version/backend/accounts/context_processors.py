"""
Context processor = prottek template e automatic kichu variable pathay.
Ekhane amra role onujayi sidebar navigation menu toiri kore pathachchi (nav_items).
Ekbar likhlei shob page e sidebar ta paoa jay - code duplicate korte hoy na.
"""
from .models import User


def _item(request, label, url_name, icon, active_names, badge=0):
    from django.urls import reverse

    current = request.resolver_match.url_name if request.resolver_match else ""
    return {
        "label": label,
        "url": reverse(url_name),
        "icon": icon,
        "active": current in active_names,
        "badge": badge,
    }


def navigation(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_approved:
        return {}

    items = []
    if user.role == User.Role.ADMIN:
        pending = User.objects.filter(role=User.Role.EMPLOYEE, is_approved=False).count()
        items = [
            _item(request, "Dashboard", "training:admin_dashboard", "home", ["admin_dashboard"]),
            _item(request, "HR & Trainers", "training:staff_list", "users", ["staff_list", "staff_add"]),
            _item(request, "Employees", "training:admin_employees", "user-check", ["admin_employees"], pending),
            _item(
                request, "Categories", "training:category_list", "tag",
                ["category_list", "category_add", "category_edit"],
            ),
            _item(
                request, "Training Modules", "training:module_list", "book",
                ["module_list", "module_create", "module_detail", "module_edit", "lesson_add", "lesson_edit",
                 "resource_add", "task_add", "task_edit"],
            ),
        ]
    elif user.role == User.Role.HR:
        items = [
            _item(request, "Dashboard", "training:hr_dashboard", "home", ["hr_dashboard"]),
            _item(request, "Employees", "training:hr_employees", "users", ["hr_employees", "hr_employee_detail"]),
            _item(request, "Skill Gaps", "training:hr_skill_gaps", "target", ["hr_skill_gaps"]),
            _item(request, "Progress Monitor", "training:hr_progress", "trending-up", ["hr_progress"]),
        ]
    elif user.role == User.Role.TRAINER:
        from training.models import Submission

        pending = Submission.objects.filter(
            employee__employee_profile__trainer=user, status=Submission.Status.SUBMITTED
        ).count()
        items = [
            _item(request, "Dashboard", "training:trainer_dashboard", "home", ["trainer_dashboard"]),
            _item(
                request, "My Employees", "training:trainer_employees", "users",
                ["trainer_employees", "trainer_employee_detail"],
            ),
            _item(
                request, "My Modules", "training:module_list", "book",
                ["module_list", "module_create", "module_detail", "module_edit", "lesson_add", "lesson_edit",
                 "resource_add", "task_add", "task_edit"],
            ),
            _item(request, "Assign Training", "training:trainer_assign", "link", ["trainer_assign"]),
            _item(
                request, "Submissions", "training:trainer_submissions", "inbox",
                ["trainer_submissions", "trainer_evaluate"], pending,
            ),
        ]
    elif user.role == User.Role.EMPLOYEE:
        items = [
            _item(request, "Dashboard", "training:employee_dashboard", "home", ["employee_dashboard"]),
            _item(
                request, "My Trainings", "training:employee_trainings", "book",
                ["employee_trainings", "employee_training_detail"],
            ),
            _item(request, "My Tasks", "training:employee_tasks", "clipboard", ["employee_tasks", "employee_task_submit"]),
            _item(request, "Feedback", "training:employee_feedback", "message", ["employee_feedback"]),
        ]

    # 100% version: shob role er jonno Calendar; Admin/HR er jonno Reports; Admin er jonno Import + Audit log
    if user.role in (User.Role.ADMIN, User.Role.HR):
        items.append(_item(request, "Reports", "core:reports", "bar-chart", ["reports"]))
    if user.role == User.Role.ADMIN:
        items.append(_item(request, "Bulk Import", "training:bulk_import", "upload", ["bulk_import"]))
        items.append(_item(request, "Audit Log", "core:audit_log", "shield", ["audit_log"]))
    if user.role == User.Role.EMPLOYEE:
        items.append(_item(request, "Certificates", "training:employee_certificates", "award", ["employee_certificates", "certificate_view"]))
    items.append(_item(request, "Calendar", "core:calendar", "calendar", ["calendar"]))

    account_items = [
        _item(request, "My Profile", "accounts:profile", "user", ["profile", "password_change"]),
    ]
    return {"nav_items": items, "account_items": account_items}
