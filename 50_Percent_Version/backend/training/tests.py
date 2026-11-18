"""
Training app tests: role permissions, CRUD, assignment, submission, evaluation, progress, skill gap.
Run:  python manage.py test
"""
import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.tests import make_user

from .models import (
    EmployeeSkill,
    Feedback,
    Lesson,
    LessonCompletion,
    ModuleAssignment,
    Resource,
    Submission,
    Task,
    TrainingCategory,
    TrainingModule,
)
from .services import skill_gap_list

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class BaseTrainingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "a@test.local", "Pass@12345")
        cls.hr = make_user("hr", "hr")
        cls.trainer = make_user("trainer", "trainer")
        cls.trainer2 = make_user("trainer2", "trainer")
        cls.emp = make_user("emp", "employee")
        cls.emp2 = make_user("emp2", "employee")  # trainer ache na
        profile = cls.emp.employee_profile
        profile.trainer = cls.trainer
        profile.save()
        cls.category = TrainingCategory.objects.create(name="Technical", required_level=4)
        cls.module = TrainingModule.objects.create(
            title="Python Basics", description="d", category=cls.category, created_by=cls.trainer
        )
        cls.lesson1 = Lesson.objects.create(module=cls.module, title="L1", content="c", order=1)
        cls.lesson2 = Lesson.objects.create(module=cls.module, title="L2", content="c", order=2)
        cls.task = Task.objects.create(
            module=cls.module, title="T1", instructions="do it", max_score=100, created_by=cls.trainer
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def login(self, username):
        self.client.logout()
        self.assertTrue(self.client.login(username=username, password="Pass@12345"))


class RolePermissionTests(BaseTrainingTest):
    """Prottek role shudhu nijer page dekhte parbe."""

    URLS = {
        "admin": ["training:admin_dashboard", "training:staff_list", "training:staff_add", "training:admin_employees",
                  "training:category_list", "training:category_add"],
        "hr": ["training:hr_dashboard", "training:hr_employees", "training:hr_skill_gaps", "training:hr_progress"],
        "trainer": ["training:trainer_dashboard", "training:trainer_employees", "training:trainer_assign",
                    "training:trainer_submissions"],
        "employee": ["training:employee_dashboard", "training:employee_trainings", "training:employee_tasks",
                     "training:employee_feedback"],
    }

    def test_every_role_can_open_own_pages_only(self):
        users = {"admin": "admin", "hr": "hr", "trainer": "trainer", "employee": "emp"}
        for role, username in users.items():
            self.login(username)
            for other_role, names in self.URLS.items():
                for name in names:
                    status = self.client.get(reverse(name)).status_code
                    expected = 200 if other_role == role else 403
                    self.assertEqual(status, expected, f"{role} -> {name} gave {status}, expected {expected}")

    def test_employee_blocked_from_module_management(self):
        self.login("emp")
        for name, args in [("training:module_list", []), ("training:module_create", []), ("training:module_detail", [self.module.pk])]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403)

    def test_hr_blocked_from_module_management(self):
        self.login("hr")
        self.assertEqual(self.client.get(reverse("training:module_list")).status_code, 403)

    def test_employee_cannot_post_admin_actions(self):
        self.login("emp")
        self.assertEqual(self.client.post(reverse("training:employee_approve", args=[self.emp2.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("training:staff_delete", args=[self.trainer.pk])).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.trainer.pk).exists())

    def test_delete_requires_post(self):
        self.login("admin")
        self.assertEqual(self.client.get(reverse("training:staff_delete", args=[self.trainer.pk])).status_code, 405)


class AdminCrudTests(BaseTrainingTest):
    def setUp(self):
        self.login("admin")

    def test_create_and_remove_staff(self):
        data = {
            "first_name": "New", "last_name": "Trainer", "username": "nt", "email": "nt@test.local", "phone": "",
            "role": "trainer", "expertise": "Java", "password1": "Strong#Pass99", "password2": "Strong#Pass99",
        }
        response = self.client.post(reverse("training:staff_add"), data)
        self.assertRedirects(response, reverse("training:staff_list"))
        user = User.objects.get(username="nt")
        self.assertEqual(user.role, "trainer")
        self.assertTrue(user.is_approved)
        self.assertEqual(user.trainer_profile.expertise, "Java")
        # HR create
        data.update(username="nh", email="nh@test.local", role="hr")
        self.client.post(reverse("training:staff_add"), data)
        self.assertEqual(User.objects.get(username="nh").role, "hr")
        # Remove
        self.client.post(reverse("training:staff_delete", args=[user.pk]))
        self.assertFalse(User.objects.filter(username="nt").exists())

    def test_staff_role_cannot_be_admin(self):
        data = {"first_name": "X", "last_name": "Y", "username": "sneaky", "email": "s@test.local", "role": "admin",
                "password1": "Strong#Pass99", "password2": "Strong#Pass99"}
        response = self.client.post(reverse("training:staff_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="sneaky").exists())

    def test_staff_delete_cannot_remove_employee_or_admin(self):
        self.client.post(reverse("training:staff_delete", args=[self.emp.pk]))
        self.assertTrue(User.objects.filter(pk=self.emp.pk).exists())
        self.assertEqual(self.client.post(reverse("training:staff_delete", args=[self.admin.pk])).status_code, 404)

    def test_approve_and_reject_employee(self):
        pending = make_user("pend", "employee", approved=False)
        self.client.post(reverse("training:employee_approve", args=[pending.pk]))
        pending.refresh_from_db()
        self.assertTrue(pending.is_approved)
        other = make_user("pend2", "employee", approved=False)
        self.client.post(reverse("training:employee_delete", args=[other.pk]))
        self.assertFalse(User.objects.filter(pk=other.pk).exists())

    def test_category_crud(self):
        self.client.post(reverse("training:category_add"), {"name": "Leadership", "description": "x", "required_level": 3})
        cat = TrainingCategory.objects.get(name="Leadership")
        self.client.post(reverse("training:category_edit", args=[cat.pk]), {"name": "Leadership 2", "description": "y", "required_level": 5})
        cat.refresh_from_db()
        self.assertEqual((cat.name, cat.required_level), ("Leadership 2", 5))
        self.client.post(reverse("training:category_delete", args=[cat.pk]))
        self.assertFalse(TrainingCategory.objects.filter(pk=cat.pk).exists())

    def test_category_validation_and_protected_delete(self):
        response = self.client.post(reverse("training:category_add"), {"name": "technical", "required_level": 3})
        self.assertIn("name", response.context["form"].errors)  # duplicate (case-insensitive)
        self.client.post(reverse("training:category_delete", args=[self.category.pk]), follow=True)
        self.assertTrue(TrainingCategory.objects.filter(pk=self.category.pk).exists())  # module ache, delete hoy ni

    def test_admin_can_manage_any_module(self):
        response = self.client.get(reverse("training:module_detail", args=[self.module.pk]))
        self.assertEqual(response.status_code, 200)
        self.client.post(reverse("training:module_create"), {
            "title": "Safety", "category": self.category.pk, "description": "d", "difficulty": "beginner",
            "duration_hours": 3, "is_published": "on",
        })
        self.assertTrue(TrainingModule.objects.filter(title="Safety", created_by=self.admin).exists())

    def test_dashboard_statistics(self):
        response = self.client.get(reverse("training:admin_dashboard"))
        self.assertEqual(response.context["stats"]["modules"], 1)
        self.assertEqual(response.context["stats"]["trainers"], 2)


class ModuleCrudTests(BaseTrainingTest):
    def test_trainer_module_crud(self):
        self.login("trainer")
        url = reverse("training:module_create")
        response = self.client.post(url, {"title": "AB", "category": self.category.pk, "description": "d", "difficulty": "beginner", "duration_hours": 2})
        self.assertIn("title", response.context["form"].errors)  # kom character
        response = self.client.post(url, {"title": "Data Analysis", "category": self.category.pk, "description": "d", "difficulty": "advanced", "duration_hours": 5, "is_published": "on"})
        module = TrainingModule.objects.get(title="Data Analysis")
        self.assertRedirects(response, reverse("training:module_detail", args=[module.pk]))
        self.assertEqual(module.created_by, self.trainer)
        self.client.post(reverse("training:module_edit", args=[module.pk]), {"title": "Data Analysis 2", "category": self.category.pk, "description": "d", "difficulty": "advanced", "duration_hours": 6})
        module.refresh_from_db()
        self.assertEqual(module.title, "Data Analysis 2")
        self.assertFalse(module.is_published)
        self.client.post(reverse("training:module_delete", args=[module.pk]))
        self.assertFalse(TrainingModule.objects.filter(pk=module.pk).exists())

    def test_trainer_cannot_touch_other_trainers_module(self):
        self.login("trainer2")
        self.assertEqual(self.client.get(reverse("training:module_detail", args=[self.module.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("training:module_delete", args=[self.module.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("training:task_delete", args=[self.task.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("training:lesson_add", args=[self.module.pk])).status_code, 403)
        listing = self.client.get(reverse("training:module_list"))
        self.assertNotContains(listing, "Python Basics")

    def test_lesson_crud_and_auto_order(self):
        self.login("trainer")
        response = self.client.get(reverse("training:lesson_add", args=[self.module.pk]))
        self.assertEqual(response.context["form"].initial["order"], 3)
        self.client.post(reverse("training:lesson_add", args=[self.module.pk]), {"title": "L3", "order": 3, "content": "body"})
        lesson = Lesson.objects.get(title="L3")
        self.client.post(reverse("training:lesson_edit", args=[lesson.pk]), {"title": "L3 edited", "order": 3, "content": "body"})
        lesson.refresh_from_db()
        self.assertEqual(lesson.title, "L3 edited")
        self.client.post(reverse("training:lesson_delete", args=[lesson.pk]))
        self.assertFalse(Lesson.objects.filter(pk=lesson.pk).exists())

    def test_task_crud_and_validation(self):
        self.login("trainer")
        past = (timezone.localdate() - timedelta(days=2)).isoformat()
        response = self.client.post(reverse("training:task_add", args=[self.module.pk]), {"title": "T2", "instructions": "x", "due_date": past, "max_score": 50})
        self.assertIn("due_date", response.context["form"].errors)
        future = (timezone.localdate() + timedelta(days=5)).isoformat()
        self.client.post(reverse("training:task_add", args=[self.module.pk]), {"title": "T2", "instructions": "x", "due_date": future, "max_score": 50})
        task = Task.objects.get(title="T2")
        self.assertEqual(task.created_by, self.trainer)
        self.client.post(reverse("training:task_edit", args=[task.pk]), {"title": "T2 new", "instructions": "x", "due_date": future, "max_score": 60})
        task.refresh_from_db()
        self.assertEqual((task.title, task.max_score), ("T2 new", 60))
        self.client.post(reverse("training:task_delete", args=[task.pk]))
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_resource_upload_validation_and_delete(self):
        self.login("trainer")
        url = reverse("training:resource_add", args=[self.module.pk])
        # document type e .mp4 file -> reject
        bad = SimpleUploadedFile("clip.mp4", b"x" * 20, content_type="video/mp4")
        response = self.client.post(url, {"title": "Doc", "kind": "document", "file": bad})
        self.assertIn("file", response.context["form"].errors)
        # exe file -> reject
        exe = SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")
        response = self.client.post(url, {"title": "Doc", "kind": "document", "file": exe})
        self.assertIn("file", response.context["form"].errors)
        good = SimpleUploadedFile("notes.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        self.client.post(url, {"title": "Notes", "kind": "document", "file": good})
        res = Resource.objects.get(title="Notes")
        self.assertEqual(res.uploaded_by, self.trainer)
        self.assertEqual(res.extension, "pdf")
        video = SimpleUploadedFile("intro.mp4", b"video-bytes", content_type="video/mp4")
        self.client.post(url, {"title": "Intro", "kind": "video", "file": video})
        self.assertEqual(Resource.objects.filter(module=self.module).count(), 2)
        self.client.post(reverse("training:resource_delete", args=[res.pk]))
        self.assertFalse(Resource.objects.filter(pk=res.pk).exists())

    def test_module_delete_cascades(self):
        self.login("admin")
        self.client.post(reverse("training:module_delete", args=[self.module.pk]))
        self.assertEqual(Lesson.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)


class HrTests(BaseTrainingTest):
    def setUp(self):
        self.login("hr")

    def test_assign_trainer(self):
        self.client.post(reverse("training:hr_assign_trainer", args=[self.emp2.pk]), {"trainer": self.trainer2.pk})
        self.emp2.employee_profile.refresh_from_db()
        self.assertEqual(self.emp2.employee_profile.trainer, self.trainer2)
        self.client.post(reverse("training:hr_assign_trainer", args=[self.emp2.pk]), {"trainer": ""})
        self.emp2.employee_profile.refresh_from_db()
        self.assertIsNone(self.emp2.employee_profile.trainer)

    def test_cannot_assign_non_trainer(self):
        self.client.post(reverse("training:hr_assign_trainer", args=[self.emp2.pk]), {"trainer": self.hr.pk})
        self.emp2.employee_profile.refresh_from_db()
        self.assertIsNone(self.emp2.employee_profile.trainer)

    def test_employee_list_search_and_detail(self):
        response = self.client.get(reverse("training:hr_employees"), {"q": "emp2"})
        self.assertEqual([e.username for e in response.context["employees"]], ["emp2"])
        self.assertEqual(self.client.get(reverse("training:hr_employee_detail", args=[self.emp.pk])).status_code, 200)
        # pending employee dekha jabe na
        pend = make_user("pend", "employee", approved=False)
        self.assertEqual(self.client.get(reverse("training:hr_employee_detail", args=[pend.pk])).status_code, 404)

    def test_skill_gap_report(self):
        gaps = skill_gap_list(list(User.objects.filter(role="employee", is_approved=True)))
        self.assertEqual(len(gaps), 2)  # duijon employee, duijoner e level 0 < 4
        EmployeeSkill.objects.create(employee=self.emp, category=self.category, level=4)
        gaps = skill_gap_list(list(User.objects.filter(role="employee", is_approved=True)))
        self.assertEqual([g["employee"].username for g in gaps], ["emp2"])
        response = self.client.get(reverse("training:hr_skill_gaps"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["gaps"]), 1)

    def test_progress_monitor_filter(self):
        ModuleAssignment.objects.create(employee=self.emp, module=self.module, assigned_by=self.trainer)
        response = self.client.get(reverse("training:hr_progress"), {"status": "completed"})
        self.assertEqual(len(response.context["assignments"]), 0)
        response = self.client.get(reverse("training:hr_progress"), {"status": "not_started"})
        self.assertEqual(len(response.context["assignments"]), 1)


class TrainerWorkflowTests(BaseTrainingTest):
    def test_trainer_sees_only_own_trainees(self):
        self.login("trainer")
        response = self.client.get(reverse("training:trainer_employees"))
        self.assertEqual([e.username for e in response.context["employees"]], ["emp"])
        self.assertEqual(self.client.get(reverse("training:trainer_employee_detail", args=[self.emp2.pk])).status_code, 404)

    def test_assign_module_validation(self):
        self.login("trainer")
        url = reverse("training:trainer_assign")
        # employee tar trainee na -> invalid choice
        response = self.client.post(url, {"employee": self.emp2.pk, "module": self.module.pk})
        self.assertIn("employee", response.context["form"].errors)
        # past due date
        past = (timezone.localdate() - timedelta(days=1)).isoformat()
        response = self.client.post(url, {"employee": self.emp.pk, "module": self.module.pk, "due_date": past})
        self.assertIn("due_date", response.context["form"].errors)
        # valid
        future = (timezone.localdate() + timedelta(days=9)).isoformat()
        self.client.post(url, {"employee": self.emp.pk, "module": self.module.pk, "due_date": future})
        assignment = ModuleAssignment.objects.get(employee=self.emp, module=self.module)
        self.assertEqual(assignment.assigned_by, self.trainer)
        self.assertEqual(assignment.status, "not_started")
        # duplicate
        response = self.client.post(url, {"employee": self.emp.pk, "module": self.module.pk})
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertEqual(ModuleAssignment.objects.count(), 1)
        # remove
        self.client.post(reverse("training:trainer_assignment_delete", args=[assignment.pk]))
        self.assertEqual(ModuleAssignment.objects.count(), 0)

    def test_draft_module_not_assignable(self):
        draft = TrainingModule.objects.create(title="Draft", description="d", category=self.category, is_published=False)
        self.login("trainer")
        response = self.client.post(reverse("training:trainer_assign"), {"employee": self.emp.pk, "module": draft.pk})
        self.assertIn("module", response.context["form"].errors)

    def test_other_trainer_cannot_remove_assignment(self):
        assignment = ModuleAssignment.objects.create(employee=self.emp, module=self.module, assigned_by=self.trainer)
        self.login("trainer2")
        self.assertEqual(self.client.post(reverse("training:trainer_assignment_delete", args=[assignment.pk])).status_code, 404)


class EmployeeWorkflowTests(BaseTrainingTest):
    """Pura flow: assign -> lesson complete -> submit -> evaluate -> feedback -> skill + progress."""

    def setUp(self):
        self.assignment = ModuleAssignment.objects.create(employee=self.emp, module=self.module, assigned_by=self.trainer)

    def test_progress_tracking_full_flow(self):
        self.login("emp")
        # 2 lesson + 1 task = 3 ta item. Prothome 0%
        self.assertEqual(self.client.get(reverse("training:employee_training_detail", args=[self.assignment.pk])).status_code, 200)
        toggle = lambda lesson: reverse("training:employee_lesson_toggle", args=[self.assignment.pk, lesson.pk])
        self.client.post(toggle(self.lesson1))
        self.assignment.refresh_from_db()
        self.assertEqual((self.assignment.progress_percent, self.assignment.status), (33, "in_progress"))
        # toggle abar -> undo
        self.client.post(toggle(self.lesson1))
        self.assignment.refresh_from_db()
        self.assertEqual((self.assignment.progress_percent, self.assignment.status), (0, "not_started"))
        self.client.post(toggle(self.lesson1))
        self.client.post(toggle(self.lesson2))
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.progress_percent, 67)
        # Task submit
        response = self.client.post(reverse("training:employee_task_submit", args=[self.task.pk]), {"answer_text": "My answer"})
        self.assertRedirects(response, reverse("training:employee_training_detail", args=[self.assignment.pk]))
        self.assignment.refresh_from_db()
        self.assertEqual((self.assignment.progress_percent, self.assignment.status), (100, "completed"))
        submission = Submission.objects.get(task=self.task, employee=self.emp)
        self.assertEqual(submission.status, "submitted")

        # Trainer evaluate kore
        self.login("trainer")
        self.assertEqual(self.client.get(reverse("training:trainer_dashboard")).context["stats"]["pending"], 1)
        bad = self.client.post(reverse("training:trainer_evaluate", args=[submission.pk]), {"score": 150, "comment": "Great work"})
        self.assertIn("score", bad.context["form"].errors)
        short = self.client.post(reverse("training:trainer_evaluate", args=[submission.pk]), {"score": 90, "comment": "ok"})
        self.assertIn("comment", short.context["form"].errors)
        ok = self.client.post(reverse("training:trainer_evaluate", args=[submission.pk]), {"score": 90, "comment": "Great work, keep going"})
        self.assertRedirects(ok, reverse("training:trainer_submissions"))
        submission.refresh_from_db()
        self.assertEqual(submission.status, "evaluated")
        self.assertEqual(submission.feedback.score, 90)
        # Skill level auto update: 90% => level 5
        self.assertEqual(EmployeeSkill.objects.get(employee=self.emp, category=self.category).level, 5)

        # Employee feedback dekhe
        self.login("emp")
        response = self.client.get(reverse("training:employee_feedback"))
        self.assertContains(response, "Great work, keep going")
        dash = self.client.get(reverse("training:employee_dashboard"))
        self.assertEqual(dash.context["stats"]["avg_progress"], 100)
        self.assertEqual(dash.context["stats"]["avg_score"], 90)
        # Evaluated task abar edit kora jabe na
        again = self.client.post(reverse("training:employee_task_submit", args=[self.task.pk]), {"answer_text": "changed"})
        self.assertRedirects(again, reverse("training:employee_feedback"))
        submission.refresh_from_db()
        self.assertEqual(submission.answer_text, "My answer")

    def test_submission_validation_and_resubmit(self):
        self.login("emp")
        url = reverse("training:employee_task_submit", args=[self.task.pk])
        response = self.client.post(url, {"answer_text": "   "})
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertEqual(Submission.objects.count(), 0)
        self.client.post(url, {"answer_text": "v1"})
        self.client.post(url, {"answer_text": "v2"})  # edit before evaluation
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Submission.objects.get().answer_text, "v2")

    def test_submission_with_attachment_and_bad_extension(self):
        self.login("emp")
        url = reverse("training:employee_task_submit", args=[self.task.pk])
        with override_settings(MEDIA_ROOT=TEMP_MEDIA):
            bad = SimpleUploadedFile("run.exe", b"MZ")
            response = self.client.post(url, {"answer_text": "", "attachment": bad})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Submission.objects.count(), 0)
            good = SimpleUploadedFile("answer.pdf", b"%PDF-1.4")
            self.client.post(url, {"answer_text": "", "attachment": good})
            self.assertTrue(Submission.objects.get().attachment.name.endswith(".pdf"))

    def test_employee_cannot_access_unassigned_or_others_content(self):
        other_module = TrainingModule.objects.create(title="Other", description="d", category=self.category)
        other_task = Task.objects.create(module=other_module, title="OT", instructions="i")
        self.login("emp")
        self.assertEqual(self.client.get(reverse("training:employee_task_submit", args=[other_task.pk])).status_code, 404)
        other_assignment = ModuleAssignment.objects.create(employee=self.emp2, module=self.module, assigned_by=self.trainer)
        self.assertEqual(self.client.get(reverse("training:employee_training_detail", args=[other_assignment.pk])).status_code, 404)
        self.assertEqual(
            self.client.post(reverse("training:employee_lesson_toggle", args=[other_assignment.pk, self.lesson1.pk])).status_code, 404
        )

    def test_trainer_cannot_evaluate_other_trainers_trainee(self):
        sub = Submission.objects.create(task=self.task, employee=self.emp, answer_text="a")
        self.login("trainer2")
        self.assertEqual(self.client.get(reverse("training:trainer_evaluate", args=[sub.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("training:trainer_evaluate", args=[sub.pk]), {"score": 5, "comment": "hello world"}).status_code, 404)
        self.assertFalse(Feedback.objects.exists())

    def test_progress_recalculates_when_content_added(self):
        self.login("emp")
        self.client.post(reverse("training:employee_lesson_toggle", args=[self.assignment.pk, self.lesson1.pk]))
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.progress_percent, 33)
        Lesson.objects.create(module=self.module, title="L3", content="c", order=3)  # 1 / 4
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.progress_percent, 25)
        self.lesson2.delete()  # 1 / 3
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.progress_percent, 33)

    def test_task_states(self):
        from .services import tasks_for_employee

        Task.objects.create(
            module=self.module, title="Late", instructions="x", due_date=timezone.localdate() - timedelta(days=3)
        )
        states = {t.title: t.state for t in tasks_for_employee(self.emp)}
        self.assertEqual(states, {"T1": "pending", "Late": "overdue"})

    def test_skill_level_boundaries(self):
        from .services import update_skill_level

        sub = Submission.objects.create(task=self.task, employee=self.emp, answer_text="a")
        for score, level in [(10, 1), (20, 1), (21, 2), (50, 3), (75, 4), (81, 5), (100, 5)]:
            Feedback.objects.update_or_create(submission=sub, defaults={"score": score, "comment": "ok ok", "trainer": self.trainer})
            self.assertEqual(update_skill_level(self.emp, self.category).level, level, f"score {score}")

    def test_dashboard_pages_render_with_data(self):
        LessonCompletion.objects.create(assignment=self.assignment, lesson=self.lesson1)
        self.login("emp")
        for name in ("training:employee_dashboard", "training:employee_trainings", "training:employee_tasks"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.login("hr")
        self.assertEqual(self.client.get(reverse("training:hr_dashboard")).status_code, 200)
        self.login("trainer")
        self.assertEqual(self.client.get(reverse("training:trainer_dashboard")).status_code, 200)


class CsrfTests(BaseTrainingTest):
    def test_post_without_csrf_token_is_rejected(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        client.login(username="admin", password="Pass@12345")
        response = client.post(reverse("training:staff_delete", args=[self.trainer.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.trainer.pk).exists())
