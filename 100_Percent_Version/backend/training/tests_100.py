"""
100% version tests: password rules removed, quiz auto-grading, certificate, discussion, notifications,
audit log, reports/CSV, calendar, bulk import, protected files, pagination.
Run:  python manage.py test
"""
import shutil
import tempfile
from datetime import timedelta

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.tests import make_user
from core.models import AuditLog, Notification

from .models import (
    Certificate, Choice, Comment, Feedback, Lesson, LessonCompletion, ModuleAssignment, Question, Quiz, QuizAttempt,
    Resource, Submission, Task, TrainingCategory, TrainingModule,
)

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class Base100(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "a@test.local", "x")
        cls.hr = make_user("hr", "hr")
        cls.trainer = make_user("trainer", "trainer")
        cls.trainer2 = make_user("trainer2", "trainer")
        cls.emp = make_user("emp", "employee")
        cls.emp2 = make_user("emp2", "employee")
        p = cls.emp.employee_profile
        p.trainer = cls.trainer
        p.department = "Eng"
        p.save()
        cls.category = TrainingCategory.objects.create(name="Technical", required_level=4)
        cls.module = TrainingModule.objects.create(title="Python Basics", description="d", category=cls.category, created_by=cls.trainer)
        cls.lesson = Lesson.objects.create(module=cls.module, title="L1", content="c", order=1)
        cls.assignment = ModuleAssignment.objects.create(employee=cls.emp, module=cls.module, assigned_by=cls.trainer,
                                                         due_date=timezone.localdate() + timedelta(days=3))
        cls.quiz = Quiz.objects.create(module=cls.module, title="Q", pass_percent=50, created_by=cls.trainer)
        cls.q1 = Question.objects.create(quiz=cls.quiz, text="2+2?", order=1)
        cls.q1_right = Choice.objects.create(question=cls.q1, text="4", is_correct=True)
        cls.q1_wrong = Choice.objects.create(question=cls.q1, text="5")
        cls.q2 = Question.objects.create(quiz=cls.quiz, text="Capital of BD?", order=2)
        cls.q2_right = Choice.objects.create(question=cls.q2, text="Dhaka", is_correct=True)
        cls.q2_wrong = Choice.objects.create(question=cls.q2, text="Khulna")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def login(self, username):
        self.client.login(username=username, password="Pass@12345" if username != "admin" else "x")


class PasswordRuleTests(Base100):
    def test_any_password_allowed_on_registration(self):
        data = {"first_name": "A", "last_name": "B", "username": "weak1", "email": "w1@x.com", "phone": "", "department": "D",
                "job_title": "J", "password1": "a", "password2": "a"}
        response = self.client.post(reverse("accounts:register"), data)
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertTrue(User.objects.get(username="weak1").check_password("a"))

    def test_numeric_and_common_passwords_allowed_for_staff(self):
        self.login("admin")
        data = {"first_name": "T", "last_name": "R", "username": "tr9", "email": "tr9@x.com", "phone": "", "role": "trainer",
                "expertise": "", "password1": "12345", "password2": "12345"}
        self.assertRedirects(self.client.post(reverse("training:staff_add"), data), reverse("training:staff_list"))

    def test_password_mismatch_still_rejected(self):
        data = {"first_name": "A", "last_name": "B", "username": "weak2", "email": "w2@x.com", "department": "D", "job_title": "J",
                "password1": "abc", "password2": "abd"}
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="weak2").exists())

    def test_change_password_to_short(self):
        self.login("emp")
        response = self.client.post(reverse("accounts:password_change"),
                                    {"old_password": "Pass@12345", "new_password1": "1", "new_password2": "1"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(username="emp").check_password("1"))

    def test_password_reset_flow(self):
        user = User.objects.get(username="emp")
        user.email = "emp@test.local"
        user.save()
        self.client.post(reverse("accounts:password_reset"), {"email": "emp@test.local"})
        self.assertEqual(len(mail.outbox), 1)
        link = [l for l in mail.outbox[0].body.splitlines() if "/reset/" in l][0].strip()
        path = "/" + link.split("://", 1)[1].split("/", 1)[1]
        response = self.client.get(path, follow=True)
        response = self.client.post(response.redirect_chain[-1][0], {"new_password1": "7", "new_password2": "7"})
        self.assertRedirects(response, reverse("accounts:password_reset_complete"))
        self.assertTrue(User.objects.get(username="emp").check_password("7"))


class QuizTests(Base100):
    def test_trainer_creates_quiz_and_question(self):
        self.login("trainer")
        r = self.client.post(reverse("training:quiz_add", args=[self.module.pk]), {"title": "New quiz", "description": "", "pass_percent": 70})
        quiz = Quiz.objects.get(title="New quiz")
        self.assertRedirects(r, reverse("training:quiz_detail", args=[quiz.pk]))
        data = {"text": "Pick B", "choice1": "A", "choice2": "B", "choice3": "", "choice4": "", "correct": "2"}
        self.client.post(reverse("training:question_add", args=[quiz.pk]), data)
        q = quiz.questions.get()
        self.assertEqual(q.choices.count(), 2)
        self.assertEqual(q.correct_choice.text, "B")

    def test_question_validation(self):
        self.login("trainer")
        url = reverse("training:question_add", args=[self.quiz.pk])
        bad = {"text": "x", "choice1": "A", "choice2": "B", "choice3": "", "choice4": "", "correct": "3"}
        self.assertContains(self.client.post(url, bad), "must point to a filled option")
        dup = {"text": "x", "choice1": "A", "choice2": "a", "correct": "1"}
        self.assertContains(self.client.post(url, dup), "different from each other")
        self.assertEqual(self.quiz.questions.count(), 2)

    def test_pass_percent_validation(self):
        self.login("trainer")
        r = self.client.post(reverse("training:quiz_add", args=[self.module.pk]), {"title": "Bad", "pass_percent": 150})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Quiz.objects.filter(title="Bad").exists())

    def test_other_trainer_cannot_manage(self):
        self.login("trainer2")
        self.assertEqual(self.client.get(reverse("training:quiz_detail", args=[self.quiz.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("training:quiz_delete", args=[self.quiz.pk])).status_code, 403)

    def test_employee_cannot_open_quiz_manager(self):
        self.login("emp")
        self.assertEqual(self.client.get(reverse("training:quiz_detail", args=[self.quiz.pk])).status_code, 403)

    def test_edit_question_and_delete(self):
        self.login("trainer")
        data = {"text": "Edited?", "choice1": "yes", "choice2": "no", "correct": "2"}
        self.client.post(reverse("training:question_edit", args=[self.q1.pk]), data)
        self.q1.refresh_from_db()
        self.assertEqual(self.q1.text, "Edited?")
        self.assertEqual(self.q1.correct_choice.text, "no")
        self.client.post(reverse("training:question_delete", args=[self.q2.pk]))
        self.assertEqual(self.quiz.questions.count(), 1)

    def test_employee_pass_attempt_and_progress(self):
        self.login("emp")
        r = self.client.post(reverse("training:employee_quiz", args=[self.quiz.pk]),
                             {f"q{self.q1.id}": self.q1_right.id, f"q{self.q2.id}": self.q2_right.id})
        attempt = QuizAttempt.objects.get()
        self.assertRedirects(r, reverse("training:employee_quiz_result", args=[attempt.pk]))
        self.assertEqual((attempt.percent, attempt.passed), (100, True))
        self.assignment.refresh_from_db()
        # lesson (0/1) + quiz passed (1/1) => 1 of 2 items
        self.assertEqual(self.assignment.progress_percent, 50)

    def test_employee_fail_attempt_does_not_count(self):
        self.login("emp")
        self.client.post(reverse("training:employee_quiz", args=[self.quiz.pk]),
                         {f"q{self.q1.id}": self.q1_wrong.id, f"q{self.q2.id}": self.q2_wrong.id})
        a = QuizAttempt.objects.get()
        self.assertEqual((a.percent, a.passed), (0, False))
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.progress_percent, 0)

    def test_unanswered_rejected(self):
        self.login("emp")
        r = self.client.post(reverse("training:employee_quiz", args=[self.quiz.pk]), {f"q{self.q1.id}": self.q1_right.id})
        self.assertContains(r, "Please answer every question")
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_forged_choice_id_rejected(self):
        self.login("emp")
        other_q = Question.objects.create(quiz=Quiz.objects.create(module=self.module, title="Z"), text="o")
        foreign = Choice.objects.create(question=other_q, text="f", is_correct=True)
        r = self.client.post(reverse("training:employee_quiz", args=[self.quiz.pk]),
                             {f"q{self.q1.id}": foreign.id, f"q{self.q2.id}": self.q2_right.id})
        self.assertEqual(QuizAttempt.objects.count(), 0)
        self.assertEqual(r.status_code, 200)

    def test_not_assigned_employee_404(self):
        self.login("emp2")
        self.assertEqual(self.client.get(reverse("training:employee_quiz", args=[self.quiz.pk])).status_code, 404)

    def test_result_page_only_owner(self):
        a = QuizAttempt.objects.create(quiz=self.quiz, employee=self.emp, correct=1, total=2, percent=50, passed=True)
        self.login("emp2")
        self.assertEqual(self.client.get(reverse("training:employee_quiz_result", args=[a.pk])).status_code, 404)
        self.login("emp")
        self.assertEqual(self.client.get(reverse("training:employee_quiz_result", args=[a.pk])).status_code, 200)

    def test_quiz_score_affects_skill_level(self):
        from .models import EmployeeSkill
        self.login("emp")
        self.client.post(reverse("training:employee_quiz", args=[self.quiz.pk]),
                         {f"q{self.q1.id}": self.q1_right.id, f"q{self.q2.id}": self.q2_right.id})
        self.assertEqual(EmployeeSkill.objects.get(employee=self.emp, category=self.category).level, 5)

    def test_empty_quiz_not_counted_in_progress(self):
        Quiz.objects.create(module=self.module, title="Empty")
        self.assignment.recalculate()
        self.assertEqual(self.assignment.progress_percent, 0)


class CertificateTests(Base100):
    def complete(self):
        self.login("emp")
        self.client.post(reverse("training:employee_lesson_toggle", args=[self.assignment.pk, self.lesson.pk]))
        self.client.post(reverse("training:employee_quiz", args=[self.quiz.pk]),
                         {f"q{self.q1.id}": self.q1_right.id, f"q{self.q2.id}": self.q2_right.id})

    def test_certificate_issued_at_100(self):
        self.complete()
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.progress_percent, 100)
        cert = Certificate.objects.get(assignment=self.assignment)
        self.assertEqual(len(cert.code), 12)
        self.assertTrue(Notification.objects.filter(user=self.emp, message__icontains="certificate").exists())

    def test_no_certificate_before_100(self):
        self.login("emp")
        self.client.post(reverse("training:employee_lesson_toggle", args=[self.assignment.pk, self.lesson.pk]))
        self.assertFalse(Certificate.objects.exists())

    def test_certificate_view_permissions(self):
        self.complete()
        cert = Certificate.objects.get()
        url = reverse("training:certificate_view", args=[cert.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertContains(self.client.get(url), self.emp.display_name)
        for user, code in (("emp2", 403), ("trainer2", 403), ("trainer", 200), ("hr", 200), ("admin", 200)):
            self.login(user)
            self.assertEqual(self.client.get(url).status_code, code, user)

    def test_public_verify(self):
        self.complete()
        cert = Certificate.objects.get()
        self.client.logout()
        ok = self.client.get(reverse("training:certificate_verify", args=[cert.code]))
        self.assertContains(ok, "Valid certificate")
        bad = self.client.get(reverse("training:certificate_verify", args=["NOPE"]))
        self.assertEqual(bad.status_code, 404)

    def test_certificates_list(self):
        self.complete()
        self.assertContains(self.client.get(reverse("training:employee_certificates")), "Python Basics")


class DiscussionTests(Base100):
    def post(self, user, body, parent=None, module=None):
        self.login(user)
        data = {"body": body, "next": "/x/"}
        if parent:
            data["parent"] = parent.pk
        return self.client.post(reverse("training:comment_add", args=[(module or self.module).pk]), data)

    def test_employee_posts_and_trainer_notified(self):
        self.post("emp", "How do loops work?")
        self.assertEqual(Comment.objects.count(), 1)
        self.assertTrue(Notification.objects.filter(user=self.trainer, message__icontains="posted").exists())

    def test_trainer_reply_notifies_employee(self):
        self.post("emp", "Question?")
        c = Comment.objects.get()
        self.post("trainer", "Answer!", parent=c)
        self.assertEqual(c.replies.count(), 1)
        self.assertTrue(Notification.objects.filter(user=self.emp, message__icontains="replied").exists())

    def test_unassigned_employee_and_hr_forbidden(self):
        self.assertEqual(self.post("emp2", "hi").status_code, 403)
        self.assertEqual(self.post("hr", "hi").status_code, 403)
        self.assertEqual(self.post("trainer2", "hi").status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)

    def test_empty_comment_rejected(self):
        self.post("emp", "   ")
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_rules(self):
        self.post("emp", "mine")
        c = Comment.objects.get()
        self.login("trainer")
        self.assertEqual(self.client.post(reverse("training:comment_delete", args=[c.pk])).status_code, 403)
        self.login("admin")
        self.client.post(reverse("training:comment_delete", args=[c.pk]), {"next": "/x/"})
        self.assertEqual(Comment.objects.count(), 0)

    def test_open_redirect_blocked(self):
        self.login("emp")
        r = self.client.post(reverse("training:comment_add", args=[self.module.pk]), {"body": "x", "next": "//evil.com"})
        self.assertNotIn("evil", r["Location"])

    def test_discussion_visible_on_pages(self):
        self.post("emp", "VisibleText")
        self.assertContains(self.client.get(reverse("training:employee_training_detail", args=[self.assignment.pk])), "VisibleText")
        self.login("trainer")
        self.assertContains(self.client.get(reverse("training:module_detail", args=[self.module.pk])), "VisibleText")


class NotificationTests(Base100):
    def test_assign_notifies_employee(self):
        mod2 = TrainingModule.objects.create(title="M2", description="d", category=self.category, created_by=self.trainer)
        self.login("trainer")
        self.client.post(reverse("training:trainer_assign"), {"employee": self.emp.pk, "module": mod2.pk, "due_date": ""})
        self.assertTrue(Notification.objects.filter(user=self.emp, message__icontains="New training assigned").exists())

    def test_register_notifies_admin_and_approve_notifies_employee(self):
        data = {"first_name": "N", "last_name": "H", "username": "nh", "email": "nh@x.com", "department": "D", "job_title": "J",
                "password1": "p", "password2": "p"}
        self.client.post(reverse("accounts:register"), data)
        self.assertTrue(Notification.objects.filter(user=self.admin, message__icontains="registration").exists())
        self.login("admin")
        nh = User.objects.get(username="nh")
        self.client.post(reverse("training:employee_approve", args=[nh.pk]))
        self.assertTrue(Notification.objects.filter(user=nh, message__icontains="approved").exists())

    def test_submit_and_evaluate_notifications(self):
        task = Task.objects.create(module=self.module, title="T", instructions="i", max_score=10, created_by=self.trainer)
        self.login("emp")
        self.client.post(reverse("training:employee_task_submit", args=[task.pk]), {"answer_text": "done"})
        self.assertTrue(Notification.objects.filter(user=self.trainer, message__icontains="submitted").exists())
        sub = Submission.objects.get()
        self.login("trainer")
        self.client.post(reverse("training:trainer_evaluate", args=[sub.pk]), {"score": 9, "comment": "great"})
        self.assertTrue(Notification.objects.filter(user=self.emp, message__icontains="evaluated").exists())

    def test_list_open_and_read_all(self):
        n = Notification.objects.create(user=self.emp, message="Hello", url="/employee/")
        Notification.objects.create(user=self.emp, message="Other")
        self.login("emp")
        self.assertContains(self.client.get(reverse("core:notifications")), "Hello")
        r = self.client.get(reverse("core:notification_open", args=[n.pk]))
        self.assertRedirects(r, "/employee/", fetch_redirect_response=False)
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.client.post(reverse("core:notification_read_all"))
        self.assertEqual(Notification.objects.filter(user=self.emp, is_read=False).count(), 0)

    def test_cannot_open_others_notification(self):
        n = Notification.objects.create(user=self.emp, message="secret")
        self.login("emp2")
        self.assertEqual(self.client.get(reverse("core:notification_open", args=[n.pk])).status_code, 404)

    def test_unsafe_url_falls_back(self):
        n = Notification.objects.create(user=self.emp, message="x", url="//evil.com")
        self.login("emp")
        r = self.client.get(reverse("core:notification_open", args=[n.pk]))
        self.assertEqual(r["Location"], "/notifications/")

    def test_unread_count_in_topbar(self):
        Notification.objects.create(user=self.emp, message="NotifTextHere")
        self.login("emp")
        self.assertContains(self.client.get(reverse("training:employee_dashboard")), "NotifTextHere")

    def test_read_all_get_not_allowed(self):
        self.login("emp")
        self.assertEqual(self.client.get(reverse("core:notification_read_all")).status_code, 405)


class AuditTests(Base100):
    def test_login_logged_and_admin_only(self):
        self.login("emp")
        self.assertTrue(AuditLog.objects.filter(action="login", actor=self.emp).exists())
        self.assertEqual(self.client.get(reverse("core:audit_log")).status_code, 403)
        self.login("admin")
        self.assertContains(self.client.get(reverse("core:audit_log")), "login")

    def test_admin_actions_logged(self):
        self.login("admin")
        self.client.post(reverse("training:category_add"), {"name": "NewCat", "description": "", "required_level": 3})
        self.client.post(reverse("training:employee_approve", args=[self.emp2.pk]))
        actions = set(AuditLog.objects.values_list("action", flat=True))
        self.assertTrue({"category_created", "employee_approved"} <= actions)

    def test_search(self):
        self.login("admin")
        self.client.post(reverse("training:category_add"), {"name": "ZzCat", "description": "", "required_level": 3})
        r = self.client.get(reverse("core:audit_log"), {"q": "ZzCat"})
        self.assertContains(r, "ZzCat")


class ReportTests(Base100):
    def test_reports_permissions(self):
        for user, code in (("admin", 200), ("hr", 200), ("trainer", 403), ("emp", 403)):
            self.login(user)
            self.assertEqual(self.client.get(reverse("core:reports")).status_code, code, user)

    def test_csv_exports(self):
        self.login("hr")
        for name in ("export_employees", "export_progress", "export_gaps"):
            r = self.client.get(reverse(f"core:{name}"))
            self.assertEqual(r.status_code, 200)
            self.assertIn("text/csv", r["Content-Type"])
            self.assertIn("attachment", r["Content-Disposition"])
        self.assertContains(self.client.get(reverse("core:export_progress")), "Python Basics")

    def test_csv_export_forbidden_for_employee(self):
        self.login("emp")
        self.assertEqual(self.client.get(reverse("core:export_employees")).status_code, 403)

    def test_csv_formula_injection_neutralised(self):
        from core.utils import csv_safe
        self.assertEqual(csv_safe("=SUM(A1)"), "'=SUM(A1)")
        self.assertEqual(csv_safe("+1"), "'+1")
        self.assertEqual(csv_safe("normal"), "normal")
        self.assertEqual(csv_safe(None), "")

    def test_export_is_audited(self):
        self.login("hr")
        self.client.get(reverse("core:export_employees"))
        self.assertTrue(AuditLog.objects.filter(action="export").exists())


class CalendarTests(Base100):
    def test_all_roles_open_calendar(self):
        for user in ("admin", "hr", "trainer", "emp"):
            self.login(user)
            self.assertEqual(self.client.get(reverse("core:calendar")).status_code, 200, user)

    def test_shows_due_module_for_employee(self):
        self.login("emp")
        r = self.client.get(reverse("core:calendar"), {"month": self.assignment.due_date.strftime("%Y-%m")})
        self.assertContains(r, "Module due: Python Basics")

    def test_other_employee_does_not_see(self):
        self.login("emp2")
        r = self.client.get(reverse("core:calendar"), {"month": self.assignment.due_date.strftime("%Y-%m")})
        self.assertNotContains(r, "Python Basics")

    def test_bad_month_param_safe(self):
        self.login("emp")
        self.assertEqual(self.client.get(reverse("core:calendar"), {"month": "garbage"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:calendar"), {"month": "2026-13"}).status_code, 200)


class BulkImportTests(Base100):
    def upload(self, text, name="emps.csv"):
        self.login("admin")
        return self.client.post(reverse("training:bulk_import"), {"csv_file": SimpleUploadedFile(name, text.encode(), content_type="text/csv")})

    def test_import_valid_rows(self):
        csv_text = "username,first_name,last_name,email,department,job_title,password\nrahim,Rahim,U,rahim@x.com,Eng,Dev,1\nkarima,Karima,B,karima@x.com,HR,Exec,\n"
        r = self.upload(csv_text)
        self.assertContains(r, "2 created")
        u = User.objects.get(username="rahim")
        self.assertTrue(u.is_approved and u.check_password("1") and u.role == "employee")
        self.assertEqual(u.employee_profile.department, "Eng")
        self.assertTrue(User.objects.get(username="karima").check_password("Welcome@123"))
        self.assertTrue(AuditLog.objects.filter(action="bulk_import").exists())

    def test_bad_rows_skipped_with_report(self):
        csv_text = "username,email\nemp,dup@x.com\nnewone,not-an-email\nok1,ok1@x.com\n,missing@x.com\nok2,ok1@x.com\n"
        r = self.upload(csv_text)
        self.assertContains(r, "1 created")
        self.assertContains(r, "already exists")
        self.assertContains(r, "invalid email")
        self.assertContains(r, "required")
        self.assertFalse(User.objects.filter(username="newone").exists())

    def test_missing_columns_and_extension(self):
        self.assertContains(self.upload("name,age\nx,1\n"), "Missing required column")
        self.assertContains(self.upload("username,email\n", name="x.txt"), "upload a .csv")

    def test_non_admin_forbidden(self):
        self.login("hr")
        self.assertEqual(self.client.get(reverse("training:bulk_import")).status_code, 403)
        self.assertEqual(self.client.get(reverse("training:bulk_import_template")).status_code, 403)

    def test_template_download(self):
        self.login("admin")
        r = self.client.get(reverse("training:bulk_import_template"))
        self.assertIn("username,first_name", r.content.decode())

    def test_invalid_username_chars(self):
        r = self.upload("username,email\nbad name!,b@x.com\n")
        self.assertContains(r, "invalid username")


class ProtectedFileTests(Base100):
    def setUp(self):
        self.res = Resource(module=self.module, title="Doc", kind="document", uploaded_by=self.trainer)
        self.res.file.save("notes.txt", SimpleUploadedFile("notes.txt", b"0123456789"), save=False)
        self.res.save()
        self.sub = Submission(task=Task.objects.create(module=self.module, title="T", instructions="i"), employee=self.emp)
        self.sub.attachment.save("work.txt", SimpleUploadedFile("work.txt", b"mywork"), save=False)
        self.sub.save()

    def test_media_url_not_public(self):
        self.login("admin")
        self.assertEqual(self.client.get("/media/" + self.res.file.name).status_code, 404)

    def test_anonymous_redirected(self):
        r = self.client.get(reverse("core:resource_file", args=[self.res.pk]))
        self.assertEqual(r.status_code, 302)

    def test_resource_permissions(self):
        url = reverse("core:resource_file", args=[self.res.pk])
        for user, code in (("emp", 200), ("emp2", 403), ("trainer", 200), ("trainer2", 403), ("hr", 200), ("admin", 200)):
            self.login(user)
            r = self.client.get(url)
            self.assertEqual(r.status_code, code, user)
            if code == 200:
                self.assertEqual(b"".join(r.streaming_content), b"0123456789")

    def test_range_request(self):
        self.login("emp")
        r = self.client.get(reverse("core:resource_file", args=[self.res.pk]), HTTP_RANGE="bytes=2-5")
        self.assertEqual(r.status_code, 206)
        self.assertEqual(b"".join(r.streaming_content), b"2345")
        self.assertEqual(r["Content-Range"], "bytes 2-5/10")
        bad = self.client.get(reverse("core:resource_file", args=[self.res.pk]), HTTP_RANGE="bytes=50-60")
        self.assertEqual(bad.status_code, 416)

    def test_submission_permissions(self):
        url = reverse("core:submission_file", args=[self.sub.pk])
        for user, code in (("emp", 200), ("emp2", 403), ("trainer", 200), ("trainer2", 403), ("hr", 200), ("admin", 200)):
            self.login(user)
            self.assertEqual(self.client.get(url).status_code, code, user)
        self.login("emp")
        self.assertIn("attachment", self.client.get(url)["Content-Disposition"])

    def test_page_links_use_protected_url(self):
        self.login("emp")
        r = self.client.get(reverse("training:employee_training_detail", args=[self.assignment.pk]))
        self.assertContains(r, reverse("core:resource_file", args=[self.res.pk]))
        self.assertNotContains(r, "/media/")


class PaginationTests(Base100):
    def test_admin_employee_list_paginates(self):
        for i in range(25):
            make_user(f"bulk{i}", "employee", approved=True)
        self.login("admin")
        r = self.client.get(reverse("training:admin_employees"), {"status": "approved"})
        self.assertContains(r, 'class="pagination"')
        r2 = self.client.get(reverse("training:admin_employees"), {"status": "approved", "page": 3})
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, "status=approved")  # filter page change e thake

    def test_bad_page_number_safe(self):
        self.login("admin")
        self.assertEqual(self.client.get(reverse("training:admin_employees"), {"page": "abc"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("training:admin_employees"), {"page": 999}).status_code, 200)


class PermissionMatrix100(Base100):
    def test_new_urls_require_login(self):
        urls = [reverse("core:notifications"), reverse("core:calendar"), reverse("core:reports"), reverse("core:audit_log"),
                reverse("training:bulk_import"), reverse("training:employee_certificates"),
                reverse("training:quiz_detail", args=[self.quiz.pk]), reverse("training:employee_quiz", args=[self.quiz.pk])]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_dark_mode_toggle_present(self):
        self.login("emp")
        r = self.client.get(reverse("training:employee_dashboard"))
        self.assertContains(r, 'id="themeToggle"')
        self.assertContains(r, 'id="bell"')
