"""
Quiz: Admin/Trainer banay (module manager), Employee dey. Auto-grading ekhane.
"""
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import employee_required, module_manager_required
from core.utils import notify

from .forms import QuestionForm, QuizForm
from .models import Choice, ModuleAssignment, Question, Quiz, QuizAttempt
from .views_modules import _check_owner, _get_module


def _get_quiz(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("module"), pk=pk)
    _check_owner(request.user, quiz.module)
    return quiz


# ---------------- Admin / Trainer ----------------
@module_manager_required
def quiz_add(request, module_id):
    module = _get_module(request, module_id)
    form = QuizForm(request.POST or None, initial={"pass_percent": 60})
    if request.method == "POST":
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.module = module
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, "Quiz created. Now add questions.")
            return redirect("training:quiz_detail", pk=quiz.pk)
        messages.error(request, "Please correct the errors below.")
    return render(
        request, "shared/form.html",
        {"form": form, "title": "Add Quiz", "subtitle": f"Module: {module.title}", "cancel_url": "training:module_detail",
         "cancel_arg": module.pk, "submit_label": "Create quiz"},
    )


@module_manager_required
def quiz_detail(request, pk):
    quiz = _get_quiz(request, pk)
    questions = quiz.questions.prefetch_related("choices")
    return render(request, "shared/quiz_detail.html", {"quiz": quiz, "questions": questions, "attempt_count": quiz.attempts.count()})


@module_manager_required
def quiz_edit(request, pk):
    quiz = _get_quiz(request, pk)
    form = QuizForm(request.POST or None, instance=quiz)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz updated.")
            return redirect("training:quiz_detail", pk=quiz.pk)
        messages.error(request, "Please correct the errors below.")
    return render(
        request, "shared/form.html",
        {"form": form, "title": f"Edit Quiz: {quiz.title}", "cancel_url": "training:quiz_detail", "cancel_arg": quiz.pk,
         "submit_label": "Save quiz"},
    )


@module_manager_required
@require_POST
def quiz_delete(request, pk):
    quiz = _get_quiz(request, pk)
    module_id = quiz.module_id
    quiz.delete()
    messages.success(request, "Quiz deleted.")
    return redirect("training:module_detail", pk=module_id)


def _save_question(form, quiz, question=None):
    data = form.cleaned_data
    with transaction.atomic():
        if question is None:
            question = Question.objects.create(quiz=quiz, text=data["text"], order=quiz.questions.count() + 1)
        else:
            question.text = data["text"]
            question.save()
            question.choices.all().delete()
        for i in range(1, 5):
            text = (data.get(f"choice{i}") or "").strip()
            if text:
                Choice.objects.create(question=question, text=text, is_correct=(data["correct"] == str(i)))
    return question


@module_manager_required
def question_add(request, quiz_id):
    quiz = _get_quiz(request, quiz_id)
    form = QuestionForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            _save_question(form, quiz)
            messages.success(request, "Question added.")
            return redirect("training:quiz_detail", pk=quiz.pk)
        messages.error(request, "Please correct the errors below.")
    return render(
        request, "shared/form.html",
        {"form": form, "title": "Add Question", "subtitle": f"Quiz: {quiz.title}", "cancel_url": "training:quiz_detail",
         "cancel_arg": quiz.pk, "submit_label": "Save question"},
    )


@module_manager_required
def question_edit(request, pk):
    question = get_object_or_404(Question.objects.select_related("quiz__module"), pk=pk)
    _check_owner(request.user, question.quiz.module)
    form = QuestionForm(request.POST or None, initial=QuestionForm.from_question(question))
    if request.method == "POST":
        if form.is_valid():
            _save_question(form, question.quiz, question)
            messages.success(request, "Question updated.")
            return redirect("training:quiz_detail", pk=question.quiz_id)
        messages.error(request, "Please correct the errors below.")
    return render(
        request, "shared/form.html",
        {"form": form, "title": "Edit Question", "subtitle": f"Quiz: {question.quiz.title}", "cancel_url": "training:quiz_detail",
         "cancel_arg": question.quiz_id, "submit_label": "Save question"},
    )


@module_manager_required
@require_POST
def question_delete(request, pk):
    question = get_object_or_404(Question.objects.select_related("quiz__module"), pk=pk)
    _check_owner(request.user, question.quiz.module)
    quiz_id = question.quiz_id
    question.delete()
    messages.success(request, "Question deleted.")
    return redirect("training:quiz_detail", pk=quiz_id)


# ---------------- Employee ----------------
def _employee_quiz_context(request, quiz):
    """Employee oi module e assigned kina check (na hole 404)."""
    assignment = get_object_or_404(ModuleAssignment, employee=request.user, module=quiz.module)
    return assignment


@employee_required
def employee_quiz(request, pk):
    quiz = get_object_or_404(Quiz.objects.select_related("module"), pk=pk)
    assignment = _employee_quiz_context(request, quiz)
    questions = list(quiz.questions.prefetch_related("choices"))
    if not questions:
        messages.info(request, "This quiz has no questions yet.")
        return redirect("training:employee_training_detail", pk=assignment.pk)
    errors = []
    selected = {}
    if request.method == "POST":
        answers = {}
        for q in questions:
            raw = request.POST.get(f"q{q.id}", "")
            valid_ids = {str(c.id) for c in q.choices.all()}
            if raw in valid_ids:
                answers[str(q.id)] = int(raw)
                selected[q.id] = int(raw)
            else:
                errors.append(q.id)
        if errors:
            messages.error(request, "Please answer every question before submitting.")
        else:
            correct = sum(1 for q in questions if q.correct_choice and q.correct_choice.id == answers[str(q.id)])
            percent = round(correct * 100 / len(questions))
            attempt = QuizAttempt.objects.create(
                quiz=quiz, employee=request.user, correct=correct, total=len(questions), percent=percent,
                passed=percent >= quiz.pass_percent, answers=answers,
            )
            if quiz.module.created_by_id:
                notify(
                    quiz.module.created_by,
                    f"{request.user.display_name} scored {percent}% on quiz '{quiz.title}'.",
                    f"/quizzes/{quiz.pk}/",
                )
            return redirect("training:employee_quiz_result", pk=attempt.pk)
    attempts = QuizAttempt.objects.filter(quiz=quiz, employee=request.user)[:5]
    return render(
        request, "employee_panel/quiz_take.html",
        {"quiz": quiz, "questions": questions, "assignment": assignment, "errors": errors, "selected": selected, "attempts": attempts},
    )


@employee_required
def employee_quiz_result(request, pk):
    attempt = get_object_or_404(QuizAttempt.objects.select_related("quiz__module"), pk=pk, employee=request.user)
    assignment = get_object_or_404(ModuleAssignment, employee=request.user, module=attempt.quiz.module)
    rows = []
    for q in attempt.quiz.questions.prefetch_related("choices"):
        chosen = attempt.answers.get(str(q.id))
        rows.append({"question": q, "chosen": chosen, "correct": q.correct_choice, "is_right": bool(q.correct_choice and q.correct_choice.id == chosen)})
    return render(request, "employee_panel/quiz_result.html", {"attempt": attempt, "rows": rows, "assignment": assignment})
