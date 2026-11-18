"""
training/models.py - Training related shob database table.

Relationship overview (Banglish):
  TrainingCategory 1 --- * TrainingModule 1 --- * Lesson / Resource / Task
  User(employee)  1 --- * ModuleAssignment * --- 1 TrainingModule      (employee assignment + progress)
  Task 1 --- * Submission (employee der joma deoa) 1 --- 1 Feedback (trainer er mantobbo)
  User(employee) 1 --- * EmployeeSkill * --- 1 TrainingCategory        (skill level)
"""
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

LEVEL_CHOICES = [
    (1, "1 - Beginner"),
    (2, "2 - Basic"),
    (3, "3 - Intermediate"),
    (4, "4 - Advanced"),
    (5, "5 - Expert"),
]

VIDEO_EXTENSIONS = ["mp4", "webm", "mov", "mkv", "avi"]
DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx", "ppt", "pptx", "txt", "md", "xls", "xlsx", "csv"]
SUBMISSION_EXTENSIONS = DOCUMENT_EXTENSIONS + ["zip", "png", "jpg", "jpeg"]


class TrainingCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Ei category te employee er minimum koto level thaka dorkar (skill gap hishab er jonno)
    required_level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "training categories"

    def __str__(self):
        return self.name


class TrainingModule(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    title = models.CharField(max_length=200)
    description = models.TextField()
    # PROTECT: category te module thakle category delete kora jabe na (data safe)
    category = models.ForeignKey(TrainingCategory, on_delete=models.PROTECT, related_name="modules")
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    duration_hours = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(200)], help_text="Estimated hours (1-200)"
    )
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_modules"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.module.title} - {self.title}"


def resource_upload_path(instance, filename):
    return f"resources/module_{instance.module_id}/{filename}"


class Resource(models.Model):
    class Kind(models.TextChoices):
        VIDEO = "video", "Video"
        DOCUMENT = "document", "Document"

    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.DOCUMENT)
    file = models.FileField(upload_to=resource_upload_path)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_resources"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def extension(self):
        return os.path.splitext(self.file.name)[1].lower().lstrip(".")

    def clean(self):
        # File er extension kind er sathe match kore kina check
        if self.file and self.file.name:
            ext = self.extension
            allowed = VIDEO_EXTENSIONS if self.kind == self.Kind.VIDEO else DOCUMENT_EXTENSIONS
            if ext not in allowed:
                raise ValidationError(
                    {"file": f"For a {self.get_kind_display()} resource please upload: {', '.join(allowed)}."}
                )

    def __str__(self):
        return self.title


class ModuleAssignment(models.Model):
    """Employee ke module assign kora + oi module e tar progress (Training Progress)."""

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments",
        limit_choices_to={"role": "employee"},
    )
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name="assignments")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="given_assignments"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    progress_percent = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "module"], name="unique_employee_module"),
        ]

    def recalculate(self):
        """
        Progress hishab: (complete kora lesson + submit kora task) / (mot lesson + mot task) * 100
        Lesson ba task add/delete holeo signal diye ei method call hoy.
        """
        total = self.module.lessons.count() + self.module.tasks.count()
        done_lessons = self.completions.filter(lesson__module=self.module).count()
        done_tasks = Submission.objects.filter(employee=self.employee, task__module=self.module).count()
        percent = round((done_lessons + done_tasks) * 100 / total) if total else 0
        percent = min(percent, 100)
        if percent == 0:
            status = self.Status.NOT_STARTED
        elif percent >= 100:
            status = self.Status.COMPLETED
        else:
            status = self.Status.IN_PROGRESS
        self.progress_percent = percent
        self.status = status
        self.save(update_fields=["progress_percent", "status"])

    @property
    def is_overdue(self):
        return bool(self.due_date and self.due_date < timezone.localdate() and self.status != self.Status.COMPLETED)

    def __str__(self):
        return f"{self.employee.display_name} -> {self.module.title}"


class LessonCompletion(models.Model):
    assignment = models.ForeignKey(ModuleAssignment, on_delete=models.CASCADE, related_name="completions")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="completions")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assignment", "lesson"], name="unique_assignment_lesson"),
        ]


class Task(models.Model):
    module = models.ForeignKey(TrainingModule, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    max_score = models.PositiveSmallIntegerField(
        default=100, validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        EVALUATED = "evaluated", "Evaluated"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="submissions")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    answer_text = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="submissions/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(SUBMISSION_EXTENSIONS)],
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["task", "employee"], name="unique_task_employee"),
        ]

    @property
    def is_late(self):
        return bool(self.task.due_date and self.submitted_at.date() > self.task.due_date)

    def __str__(self):
        return f"{self.employee.display_name} - {self.task.title}"


class Feedback(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="feedback")
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="given_feedback"
    )
    score = models.PositiveSmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    @property
    def percentage(self):
        max_score = self.submission.task.max_score
        return round(self.score * 100 / max_score) if max_score else 0

    def __str__(self):
        return f"Feedback for {self.submission}"


class EmployeeSkill(models.Model):
    """Employee er kono category te current skill level (1-5). Trainer evaluate korle auto update hoy."""

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skills")
    category = models.ForeignKey(TrainingCategory, on_delete=models.CASCADE, related_name="employee_skills")
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["employee", "category"], name="unique_employee_category"),
        ]

    @property
    def gap(self):
        return max(self.category.required_level - self.level, 0)

    def __str__(self):
        return f"{self.employee.display_name} - {self.category.name}: {self.level}"
