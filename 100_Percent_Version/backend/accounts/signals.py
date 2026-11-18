"""
Signal = "kono ghotona ghotle auto kichu cholbe".
Ekhane: User save hole role onujayi profile automatic toiri hobe.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmployeeProfile, TrainerProfile, User


@receiver(post_save, sender=User)
def create_role_profile(sender, instance, **kwargs):
    if instance.role == User.Role.EMPLOYEE:
        EmployeeProfile.objects.get_or_create(user=instance)
    elif instance.role == User.Role.TRAINER:
        TrainerProfile.objects.get_or_create(user=instance)
