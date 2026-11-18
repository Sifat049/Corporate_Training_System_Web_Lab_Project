"""
training/forms.py - training related shob form.
Validation gulo ekhane (server-side) - HTML e shudhu 'required' dilei hoy na, backend e check must.
"""
from django import forms
from django.conf import settings
from django.utils import timezone

from accounts.forms import StyledFormMixin
from accounts.models import User

from .models import (
    Feedback,
    Lesson,
    ModuleAssignment,
    Resource,
    Submission,
    Task,
    TrainingCategory,
    TrainingModule,
)


class DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(**kwargs)


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TrainingCategory
        fields = ("name", "description", "required_level")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}
        help_texts = {"required_level": "Employees should reach at least this skill level in this category."}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = TrainingCategory.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name


class ModuleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TrainingModule
        fields = ("title", "category", "description", "difficulty", "duration_hours", "is_published")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
        labels = {"is_published": "Published (visible for assignment)"}

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters.")
        return title


class LessonForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ("title", "order", "content")
        widgets = {"content": forms.Textarea(attrs={"rows": 8})}
        help_texts = {"order": "Lesson sequence number (1, 2, 3 ...)"}

    def clean_order(self):
        order = self.cleaned_data["order"]
        if order < 1:
            raise forms.ValidationError("Order must be 1 or more.")
        return order


class ResourceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Resource
        fields = ("title", "kind", "file")
        labels = {"kind": "Resource type"}

    def clean_file(self):
        upload = self.cleaned_data.get("file")
        if upload and hasattr(upload, "size"):
            limit = settings.MAX_UPLOAD_MB * 1024 * 1024
            if upload.size > limit:
                raise forms.ValidationError(f"File is too large. Maximum size is {settings.MAX_UPLOAD_MB} MB.")
        return upload


class TaskForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "instructions", "due_date", "max_score")
        widgets = {"instructions": forms.Textarea(attrs={"rows": 5}), "due_date": DateInput()}

    def clean_due_date(self):
        due = self.cleaned_data.get("due_date")
        # Notun task e past date dewa jabe na (edit e purono date thakte pare)
        if due and not self.instance.pk and due < timezone.localdate():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due


class SubmissionForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Submission
        fields = ("answer_text", "attachment")
        widgets = {"answer_text": forms.Textarea(attrs={"rows": 7, "placeholder": "Write your answer here..."})}
        labels = {"answer_text": "Your answer", "attachment": "Attachment (optional)"}

    def clean_attachment(self):
        upload = self.cleaned_data.get("attachment")
        if upload and hasattr(upload, "size") and upload.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f"File is too large. Maximum size is {settings.MAX_UPLOAD_MB} MB.")
        return upload

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get("answer_text") or "").strip()
        has_file = bool(cleaned.get("attachment"))
        if not text and not has_file:
            raise forms.ValidationError("Please write an answer or attach a file.")
        cleaned["answer_text"] = text
        return cleaned


class FeedbackForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("score", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 5, "placeholder": "Write constructive feedback..."})}

    def __init__(self, *args, submission=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.submission = submission
        self.fields["score"].widget.attrs["min"] = 0
        self.fields["score"].widget.attrs["max"] = submission.task.max_score
        self.fields["score"].label = f"Score (out of {submission.task.max_score})"

    def clean_score(self):
        score = self.cleaned_data["score"]
        if score > self.submission.task.max_score:
            raise forms.ValidationError(f"Score cannot be more than {self.submission.task.max_score}.")
        return score

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()
        if len(comment) < 5:
            raise forms.ValidationError("Please write at least a short feedback (5+ characters).")
        return comment


class AssignModuleForm(StyledFormMixin, forms.Form):
    """Trainer nijer trainee ke module assign kore."""

    employee = forms.ModelChoiceField(queryset=User.objects.none())
    module = forms.ModelChoiceField(queryset=TrainingModule.objects.none())
    due_date = forms.DateField(required=False, widget=DateInput())

    def __init__(self, *args, trainer, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee"].queryset = User.objects.filter(
            role=User.Role.EMPLOYEE, is_approved=True, employee_profile__trainer=trainer
        ).order_by("first_name", "username")
        self.fields["employee"].label_from_instance = lambda u: f"{u.display_name} ({u.username})"
        self.fields["module"].queryset = TrainingModule.objects.filter(is_published=True).select_related("category")
        self.fields["module"].label_from_instance = lambda m: f"{m.title} [{m.category.name}]"

    def clean_due_date(self):
        due = self.cleaned_data.get("due_date")
        if due and due < timezone.localdate():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due

    def clean(self):
        cleaned = super().clean()
        employee, module = cleaned.get("employee"), cleaned.get("module")
        if employee and module and ModuleAssignment.objects.filter(employee=employee, module=module).exists():
            raise forms.ValidationError(f"{employee.display_name} is already assigned to '{module.title}'.")
        return cleaned


class AssignTrainerForm(StyledFormMixin, forms.Form):
    """HR Manager employee ke trainer er sathe jure."""

    trainer = forms.ModelChoiceField(queryset=User.objects.none(), required=False, empty_label="-- No trainer --")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["trainer"].queryset = User.objects.filter(role=User.Role.TRAINER, is_approved=True)
        self.fields["trainer"].label_from_instance = lambda u: u.display_name


# =====================================================================
# 100% version forms: Quiz, Question, Comment, Bulk CSV import
# =====================================================================
from .models import Quiz  # noqa: E402


class QuizForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ("title", "description", "pass_percent")
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 3:
            raise forms.ValidationError("Title must be at least 3 characters.")
        return title


class QuestionForm(StyledFormMixin, forms.Form):
    """Ekta MCQ: question + 4 ta option (kom pokkhe 2 ta) + kon ta thik uttor."""

    text = forms.CharField(label="Question", max_length=500, widget=forms.Textarea(attrs={"rows": 2}))
    choice1 = forms.CharField(label="Option 1", max_length=300)
    choice2 = forms.CharField(label="Option 2", max_length=300)
    choice3 = forms.CharField(label="Option 3 (optional)", max_length=300, required=False)
    choice4 = forms.CharField(label="Option 4 (optional)", max_length=300, required=False)
    correct = forms.ChoiceField(
        label="Correct answer", choices=[("1", "Option 1"), ("2", "Option 2"), ("3", "Option 3"), ("4", "Option 4")]
    )

    def clean(self):
        data = super().clean()
        correct = data.get("correct")
        if correct and not (data.get(f"choice{correct}") or "").strip():
            self.add_error("correct", "The correct answer must point to a filled option.")
        texts = [(data.get(f"choice{i}") or "").strip().lower() for i in range(1, 5)]
        texts = [t for t in texts if t]
        if len(texts) != len(set(texts)):
            raise forms.ValidationError("Options must be different from each other.")
        return data

    @classmethod
    def from_question(cls, question):
        choices = list(question.choices.all())
        initial = {"text": question.text}
        for i, choice in enumerate(choices[:4], start=1):
            initial[f"choice{i}"] = choice.text
            if choice.is_correct:
                initial["correct"] = str(i)
        return initial


class CommentForm(StyledFormMixin, forms.Form):
    body = forms.CharField(
        label="", max_length=1000, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Write a question or reply..."})
    )

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("Write something first.")
        return body


class BulkImportForm(StyledFormMixin, forms.Form):
    csv_file = forms.FileField(label="CSV file")

    def clean_csv_file(self):
        f = self.cleaned_data["csv_file"]
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        if f.size > 1024 * 1024:
            raise forms.ValidationError("CSV file is too large (max 1 MB).")
        return f
