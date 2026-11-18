from django.contrib import admin

from .models import (
    EmployeeSkill,
    Feedback,
    Lesson,
    LessonCompletion,
    ModuleAssignment,
    Resource,
    Submission,
    Task,
    TrainingCategory,
    TrainingModule,
)

for model in (
    TrainingCategory, TrainingModule, Lesson, Resource, ModuleAssignment, LessonCompletion,
    Task, Submission, Feedback, EmployeeSkill,
):
    admin.site.register(model)
