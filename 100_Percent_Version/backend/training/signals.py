"""
Lesson / Task / Quiz / Question add ba delete korle oi module er shob assignment er progress abar hishab kora hoy.
QuizAttempt save hole: progress + skill level update.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Lesson, ModuleAssignment, Question, Quiz, QuizAttempt, Task


def _refresh_module_progress(module_id):
    for assignment in ModuleAssignment.objects.filter(module_id=module_id).select_related("module"):
        assignment.recalculate()


@receiver([post_save, post_delete], sender=Lesson)
@receiver([post_save, post_delete], sender=Task)
@receiver([post_save, post_delete], sender=Quiz)
def update_progress_on_content_change(sender, instance, **kwargs):
    _refresh_module_progress(instance.module_id)


@receiver([post_save, post_delete], sender=Question)
def update_progress_on_question_change(sender, instance, **kwargs):
    quiz = Quiz.objects.filter(pk=instance.quiz_id).first()
    if quiz:  # quiz delete er shomoy cascade e question delete hole quiz nai
        _refresh_module_progress(quiz.module_id)


@receiver(post_save, sender=QuizAttempt)
def update_after_attempt(sender, instance, created, **kwargs):
    if not created:
        return
    from .services import update_skill_level

    assignment = ModuleAssignment.objects.filter(employee=instance.employee, module=instance.quiz.module).first()
    if assignment:
        assignment.recalculate()
    update_skill_level(instance.employee, instance.quiz.module.category)
