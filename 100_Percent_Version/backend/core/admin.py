from django.contrib import admin

from .models import AuditLog, Notification

admin.site.register(Notification)
admin.site.register(AuditLog)
