"""
Lesson ba Task add / delete korle oi module er shob assignment er progress abar hishab kora hoy.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Lesson, ModuleAssignment, Task


def _refresh_module_progress(module_id):
    for assignment in ModuleAssignment.objects.filter(module_id=module_id).select_related("module"):
        assignment.recalculate()


@receiver([post_save, post_delete], sender=Lesson)
@receiver([post_save, post_delete], sender=Task)
def update_progress_on_content_change(sender, instance, **kwargs):
    _refresh_module_progress(instance.module_id)
