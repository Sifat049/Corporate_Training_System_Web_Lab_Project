"""
core/models.py - Notification (in-app bell) ar AuditLog (admin er activity record)

Banglish note:
- Notification: kono ghotona ghotle (assign, evaluate, approve...) user er bell e message jay.
- AuditLog: kon user kokhon ki korlo - Admin eta dekhte pare (security / accountability).
"""
from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user} - {self.message[:40]}"


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_entries")
    actor_name = models.CharField(max_length=150, blank=True)  # user delete hole-o naam thake
    action = models.CharField(max_length=60)
    detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.actor_name}: {self.action}"
