"""
Training module CRUD - Admin (shob module) ar Trainer (shudhu nijer banano module) duijon use kore.
Lesson, Resource (video/document upload), Task er CRUD-o ekhane.

Permission rule:
  - Admin: shob module manage korte pare.
  - Trainer: shudhu jei module se nije create koreche.
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import module_manager_required
from accounts.models import User
from core.utils import audit, paginate

from .forms import CommentForm, LessonForm, ModuleForm, ResourceForm, TaskForm
from .models import Lesson, ModuleAssignment, Resource, Task, TrainingCategory, TrainingModule


def _check_owner(user, module):
    """Trainer onno kono trainer er module touch korte parbe na."""
    if user.role == User.Role.TRAINER and module.created_by_id != user.id:
        raise PermissionDenied


def _get_module(request, pk):
    module = get_object_or_404(TrainingModule.objects.select_related("category", "created_by"), pk=pk)
    _check_owner(request.user, module)
    return module


@module_manager_required
def module_list(request):
    q = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    modules = TrainingModule.objects.select_related("category", "created_by").order_by("-created_at", "-id").annotate(
        lesson_count=Count("lessons", distinct=True),
        task_count=Count("tasks", distinct=True),
        assigned_count=Count("assignments", distinct=True),
    )
    if request.user.role == User.Role.TRAINER:
        modules = modules.filter(created_by=request.user)
    if q:
        modules = modules.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category_id.isdigit():
        modules = modules.filter(category_id=int(category_id))
    return render(
        request,
        "shared/module_list.html",
        {"modules": paginate(request, modules, 9), "q": q, "category_id": category_id, "categories": TrainingCategory.objects.all()},
    )


@module_manager_required
def module_create(request):
    form = ModuleForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            module = form.save(commit=False)
            module.created_by = request.user
            module.save()
            audit(request.user, "module_created", module.title)
            messages.success(request, "Module created. Now add lessons, resources and tasks.")
            return redirect("training:module_detail", pk=module.pk)
        messages.error(request, "Please correct the errors below.")
    if not TrainingCategory.objects.exists():
        messages.warning(request, "No training category exists yet. Ask an Admin to create one first.")
    return render(
        request,
        "shared/form.html",
        {"form": form, "title": "Create Training Module", "cancel_url": "training:module_list", "submit_label": "Create module"},
    )


@module_manager_required
def module_detail(request, pk):
    module = _get_module(request, pk)
    context = {
        "module": module,
        "lessons": module.lessons.all(),
        "resources": module.resources.select_related("uploaded_by"),
        "tasks": module.tasks.annotate(sub_count=Count("submissions")),
        "assignments": module.assignments.select_related("employee"),
        "quizzes": module.quizzes.prefetch_related("questions"),
        "comments": module.comments.filter(parent__isnull=True).select_related("author").prefetch_related("replies__author"),
        "comment_form": CommentForm(),
    }
    return render(request, "shared/module_detail.html", context)


@module_manager_required
def module_edit(request, pk):
    module = _get_module(request, pk)
    form = ModuleForm(request.POST or None, instance=module)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Module updated successfully.")
            return redirect("training:module_detail", pk=module.pk)
        messages.error(request, "Please correct the errors below.")
    return render(
        request,
        "shared/form.html",
        {"form": form, "title": f"Edit Module: {module.title}", "cancel_url": "training:module_detail", "cancel_arg": module.pk, "submit_label": "Update module"},
    )


@module_manager_required
@require_POST
def module_delete(request, pk):
    module = _get_module(request, pk)
    title = module.title
    audit(request.user, "module_deleted", title)
    module.delete()
    messages.success(request, f"Module '{title}' and all its content were deleted.")
    return redirect("training:module_list")


# ---------- Generic helper: Lesson / Resource / Task er add-edit ekoi pattern ----------
def _save_child(request, module, form_class, title, instance=None, owner_field=None, multipart=False, label="", initial=None):
    form = form_class(request.POST or None, request.FILES or None, instance=instance, initial=initial)
    if request.method == "POST":
        if form.is_valid():
            obj = form.save(commit=False)
            obj.module = module
            if owner_field and not obj.pk:
                setattr(obj, owner_field, request.user)
            obj.save()
            messages.success(request, f"{label} {'updated' if instance else 'added'} successfully.")
            return redirect("training:module_detail", pk=module.pk)
        messages.error(request, "Please correct the errors below.")
    return render(
        request,
        "shared/form.html",
        {
            "form": form,
            "title": title,
            "subtitle": f"Module: {module.title}",
            "cancel_url": "training:module_detail",
            "cancel_arg": module.pk,
            "submit_label": "Save",
            "multipart": multipart,
        },
    )


# Lessons
@module_manager_required
def lesson_add(request, module_id):
    module = _get_module(request, module_id)
    # Notun lesson e order auto set: ager lesson gulor porer number
    return _save_child(
        request, module, LessonForm, "Add Lesson", label="Lesson", initial={"order": module.lessons.count() + 1}
    )


@module_manager_required
def lesson_edit(request, pk):
    lesson = get_object_or_404(Lesson.objects.select_related("module"), pk=pk)
    _check_owner(request.user, lesson.module)
    return _save_child(request, lesson.module, LessonForm, "Edit Lesson", instance=lesson, label="Lesson")


@module_manager_required
@require_POST
def lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson.objects.select_related("module"), pk=pk)
    _check_owner(request.user, lesson.module)
    module_id = lesson.module_id
    lesson.delete()
    messages.success(request, "Lesson deleted.")
    return redirect("training:module_detail", pk=module_id)


# Resources (video / document upload)
@module_manager_required
def resource_add(request, module_id):
    module = _get_module(request, module_id)
    return _save_child(
        request, module, ResourceForm, "Upload Resource", owner_field="uploaded_by", multipart=True, label="Resource"
    )


@module_manager_required
@require_POST
def resource_delete(request, pk):
    resource = get_object_or_404(Resource.objects.select_related("module"), pk=pk)
    _check_owner(request.user, resource.module)
    module_id = resource.module_id
    resource.file.delete(save=False)  # disk theke file-o muche felo
    resource.delete()
    messages.success(request, "Resource deleted.")
    return redirect("training:module_detail", pk=module_id)


# Tasks
@module_manager_required
def task_add(request, module_id):
    module = _get_module(request, module_id)
    return _save_child(request, module, TaskForm, "Create Task", owner_field="created_by", label="Task")


@module_manager_required
def task_edit(request, pk):
    task = get_object_or_404(Task.objects.select_related("module"), pk=pk)
    _check_owner(request.user, task.module)
    return _save_child(request, task.module, TaskForm, "Edit Task", instance=task, label="Task")


@module_manager_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task.objects.select_related("module"), pk=pk)
    _check_owner(request.user, task.module)
    module_id = task.module_id
    task.delete()
    messages.success(request, "Task deleted.")
    return redirect("training:module_detail", pk=module_id)
