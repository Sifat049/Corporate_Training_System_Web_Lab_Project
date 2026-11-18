"""
training/services.py - Business logic (hishab-nikash) ekhane rakha hoyeche.

Banglish note:
View ke chhoto rakhar jonno complex calculation (skill level, skill gap, task status)
alada file e rakhi. Tahole code duplicate hoy na, test kora shohoj hoy.
"""
import math

from django.db.models import Avg
from django.utils import timezone

from accounts.models import User

from .models import (
    EmployeeSkill,
    Feedback,
    QuizAttempt,
    ModuleAssignment,
    Submission,
    Task,
    TrainingCategory,
)


def update_skill_level(employee, category):
    """
    Employee er oi category te shob evaluated task er gor percentage theke level (1-5) ber kore.
    0-20% => 1, 21-40% => 2, 41-60% => 3, 61-80% => 4, 81-100% => 5
    """
    feedbacks = Feedback.objects.filter(
        submission__employee=employee, submission__task__module__category=category
    ).select_related("submission__task")
    percentages = [f.percentage for f in feedbacks]
    # 100% version: quiz er best score-o skill level e dhora hoy (prottek quiz er shob cheye bhalo attempt)
    best_quiz = {}
    for attempt in QuizAttempt.objects.filter(employee=employee, quiz__module__category=category):
        best_quiz[attempt.quiz_id] = max(best_quiz.get(attempt.quiz_id, 0), attempt.percent)
    percentages += list(best_quiz.values())
    if not percentages:
        return None
    average = sum(percentages) / len(percentages)
    level = min(5, max(1, math.ceil(average / 20)))
    skill, _ = EmployeeSkill.objects.update_or_create(
        employee=employee, category=category, defaults={"level": level}
    )
    return skill


def employee_skill_rows(employee, categories=None):
    """Employee er shob category te level, required level ar gap list hishebe return kore."""
    categories = categories if categories is not None else list(TrainingCategory.objects.all())
    levels = {s.category_id: s.level for s in EmployeeSkill.objects.filter(employee=employee)}
    rows = []
    for category in categories:
        level = levels.get(category.id, 0)
        rows.append(
            {
                "category": category,
                "level": level,
                "required": category.required_level,
                "gap": max(category.required_level - level, 0),
                "assessed": category.id in levels,
            }
        )
    return rows


def employee_avg_skill(employee):
    result = EmployeeSkill.objects.filter(employee=employee).aggregate(avg=Avg("level"))["avg"]
    return round(result, 1) if result is not None else None


def employee_avg_progress(employee):
    result = ModuleAssignment.objects.filter(employee=employee).aggregate(avg=Avg("progress_percent"))["avg"]
    return round(result) if result is not None else 0


def skill_gap_list(employees, categories=None, category_id=None):
    """HR er jonno: shob employee x category te jekhane level < required, sheta gap hishebe return."""
    categories = categories if categories is not None else list(TrainingCategory.objects.all())
    if category_id:
        categories = [c for c in categories if c.id == category_id]
    skills = {}
    for s in EmployeeSkill.objects.filter(employee__in=employees):
        skills[(s.employee_id, s.category_id)] = s.level
    gaps = []
    for employee in employees:
        for category in categories:
            level = skills.get((employee.id, category.id), 0)
            gap = category.required_level - level
            if gap > 0:
                gaps.append(
                    {
                        "employee": employee,
                        "category": category,
                        "level": level,
                        "required": category.required_level,
                        "gap": gap,
                        "assessed": (employee.id, category.id) in skills,
                    }
                )
    gaps.sort(key=lambda g: (-g["gap"], g["employee"].display_name))
    return gaps


def tasks_for_employee(employee):
    """
    Employee er assign kora module gulor shob task, tader status shoho.
    state: pending / overdue / submitted / evaluated
    """
    module_ids = ModuleAssignment.objects.filter(employee=employee).values_list("module_id", flat=True)
    tasks = list(Task.objects.filter(module_id__in=module_ids).select_related("module").order_by("due_date", "id"))
    submissions = {
        s.task_id: s for s in Submission.objects.filter(employee=employee).select_related("feedback")
    }
    today = timezone.localdate()
    for task in tasks:
        task.submission = submissions.get(task.id)
        if task.submission is None:
            task.state = "overdue" if task.due_date and task.due_date < today else "pending"
        else:
            task.state = task.submission.status
    return tasks


def assignment_trainees(trainer):
    return User.objects.filter(
        role=User.Role.EMPLOYEE, is_approved=True, employee_profile__trainer=trainer
    ).select_related("employee_profile")
