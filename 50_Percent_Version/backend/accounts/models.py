"""
accounts/models.py - User, EmployeeProfile, TrainerProfile

Banglish note:
Django te "model" mane database table. Ekta Python class = ekta table,
ar class er field gulo = table er column.
"""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-]{7,20}$",
    message="Enter a valid phone number (digits, spaces, + and - only).",
)


class User(AbstractUser):
    """Custom user. AbstractUser theke username/password/email shob pai, amra shudhu role add korechi."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        HR = "hr", "HR Manager"
        TRAINER = "trainer", "Trainer"
        EMPLOYEE = "employee", "Employee"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    # Employee register korle prothome False thake; Admin approve korle True hoy
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # createsuperuser diye banano user shobsomoy Admin + approved
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_approved = True
        super().save(*args, **kwargs)

    # Template ar view e shohoje role check korar jonno chhoto property
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_hr(self):
        return self.role == self.Role.HR

    @property
    def is_trainer(self):
        return self.role == self.Role.TRAINER

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        parts = self.display_name.split()
        return "".join(p[0] for p in parts[:2]).upper() or "U"

    def __str__(self):
        return f"{self.display_name} ({self.get_role_display()})"


class EmployeeProfile(models.Model):
    """Employee er extra information. User er sathe OneToOne (ekjon user = ekta profile)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile")
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    # HR Manager ekhane trainer assign kore. Trainer delete hole SET_NULL (employee thake, trainer faka hoy)
    trainer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trainees",
        limit_choices_to={"role": "trainer"},
    )
    joined_on = models.DateField(default=timezone.localdate)

    def __str__(self):
        return f"Profile of {self.user.display_name}"


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="trainer_profile")
    expertise = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Trainer profile of {self.user.display_name}"
