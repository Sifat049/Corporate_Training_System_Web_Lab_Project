"""
accounts/forms.py - Login, Registration, Staff create, Profile form.

Banglish note:
Django Form = HTML form + validation er kaj ekshathe kore. Amra user er input ke
server side e validate kori (email unique, password match, phone format ityadi).
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import EmployeeProfile, TrainerProfile, User


class StyledFormMixin:
    """Shob form field e automatic CSS class lagay, jate amader design system er sathe match kore."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-check" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {css}".strip()


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Username"}))
    password = forms.CharField(
        strip=False, widget=forms.PasswordInput(attrs={"placeholder": "Password", "autocomplete": "current-password"})
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        # Employee approve na howa porjonto login korte parbe na
        if not user.is_approved:
            raise forms.ValidationError(
                "Your account is waiting for admin approval. Please try again later.",
                code="not_approved",
            )


class EmployeeRegistrationForm(StyledFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField()
    department = forms.CharField(max_length=100)
    job_title = forms.CharField(max_length=100)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone", "department", "job_title")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.EMPLOYEE
        user.is_approved = False  # Admin approve korbe
        if commit:
            user.save()
            profile = user.employee_profile  # signal diye toiri hoyeche
            profile.department = self.cleaned_data["department"]
            profile.job_title = self.cleaned_data["job_title"]
            profile.save()
        return user


class StaffCreateForm(StyledFormMixin, UserCreationForm):
    """Admin ei form diye HR Manager ba Trainer account banay."""

    ROLE_CHOICES = [(User.Role.HR, "HR Manager"), (User.Role.TRAINER, "Trainer")]

    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    expertise = forms.CharField(max_length=200, required=False, help_text="Trainer hole expertise likhun (optional).")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        user.is_approved = True  # Admin nije banalo, tai approved
        if commit:
            user.save()
            if user.role == User.Role.TRAINER:
                TrainerProfile.objects.update_or_create(
                    user=user, defaults={"expertise": self.cleaned_data.get("expertise", "")}
                )
        return user


class ProfileForm(StyledFormMixin, forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is used by another account.")
        return email


class EmployeeProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = ("department", "job_title")
