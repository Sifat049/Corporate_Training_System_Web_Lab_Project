"""Login hole audit log e ekta entry."""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .utils import audit


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    audit(user, "login", f"{user.username} ({user.get_role_display()}) signed in")
