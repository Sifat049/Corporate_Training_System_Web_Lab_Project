from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmployeeProfile, TrainerProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_approved", "is_active")
    list_filter = ("role", "is_approved", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Training System", {"fields": ("role", "phone", "is_approved")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Training System", {"fields": ("role", "phone", "is_approved")}),)


admin.site.register(EmployeeProfile)
admin.site.register(TrainerProfile)
