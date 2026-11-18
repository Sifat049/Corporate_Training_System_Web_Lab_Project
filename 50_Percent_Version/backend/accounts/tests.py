"""Authentication + role permission tests.  Run:  python manage.py test accounts"""
from django.test import TestCase
from django.urls import reverse

from .models import EmployeeProfile, User


def make_user(username, role, approved=True, password="Pass@12345", **extra):
    user = User(username=username, role=role, is_approved=approved, email=f"{username}@test.local", **extra)
    user.set_password(password)
    user.save()
    return user


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "a@test.local", "Pass@12345")
        cls.hr = make_user("hr", "hr")
        cls.trainer = make_user("trainer", "trainer")
        cls.employee = make_user("emp", "employee")
        cls.pending = make_user("pend", "employee", approved=False)

    def test_each_role_lands_on_own_dashboard(self):
        expected = {
            "admin": "training:admin_dashboard",
            "hr": "training:hr_dashboard",
            "trainer": "training:trainer_dashboard",
            "emp": "training:employee_dashboard",
        }
        for username, url_name in expected.items():
            self.client.logout()
            response = self.client.post(reverse("accounts:login"), {"username": username, "password": "Pass@12345"})
            self.assertRedirects(response, reverse("accounts:dashboard"), fetch_redirect_response=False)
            response = self.client.get(reverse("accounts:dashboard"))
            self.assertRedirects(response, reverse(url_name))
            self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_wrong_password_rejected(self):
        response = self.client.post(reverse("accounts:login"), {"username": "emp", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password")

    def test_unapproved_employee_cannot_login(self):
        response = self.client.post(reverse("accounts:login"), {"username": "pend", "password": "Pass@12345"})
        self.assertContains(response, "waiting for admin approval")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_works(self):
        self.client.login(username="emp", password="Pass@12345")
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_redirected_to_login(self):
        for name in ("training:admin_dashboard", "training:hr_dashboard", "training:employee_dashboard", "accounts:profile"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("accounts:login"), response.url)


class RegistrationTests(TestCase):
    data = {
        "first_name": "New", "last_name": "Hire", "username": "newhire", "email": "new@test.local",
        "phone": "01711223344", "department": "Finance", "job_title": "Analyst",
        "password1": "Strong#Pass99", "password2": "Strong#Pass99",
    }

    def test_register_creates_pending_employee_with_profile(self):
        response = self.client.post(reverse("accounts:register"), self.data)
        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="newhire")
        self.assertEqual(user.role, "employee")
        self.assertFalse(user.is_approved)
        self.assertEqual(user.employee_profile.department, "Finance")

    def test_register_validation_errors(self):
        bad = dict(self.data, password2="different", email="not-an-email", phone="abc")
        response = self.client.post(reverse("accounts:register"), bad)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newhire").exists())
        form = response.context["form"]
        self.assertIn("password2", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("phone", form.errors)

    def test_duplicate_email_rejected(self):
        User.objects.create_user("other", "dup@test.local", "Pass@12345")
        response = self.client.post(reverse("accounts:register"), dict(self.data, email="DUP@test.local"))
        self.assertIn("email", response.context["form"].errors)

    def test_profile_created_by_signal(self):
        user = make_user("e1", "employee")
        self.assertTrue(EmployeeProfile.objects.filter(user=user).exists())
        trainer = make_user("t1", "trainer")
        self.assertTrue(hasattr(trainer, "trainer_profile"))


class ProfileTests(TestCase):
    def setUp(self):
        self.emp = make_user("emp", "employee")
        self.client.login(username="emp", password="Pass@12345")

    def test_update_profile(self):
        response = self.client.post(
            reverse("accounts:profile"),
            {"user-first_name": "Rafiq", "user-last_name": "Ahmed", "user-email": "r@test.local", "user-phone": "01700000000",
             "emp-department": "IT", "emp-job_title": "Dev"},
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.first_name, "Rafiq")
        self.assertEqual(self.emp.employee_profile.department, "IT")

    def test_change_password_keeps_session(self):
        response = self.client.post(
            reverse("accounts:password_change"),
            {"old_password": "Pass@12345", "new_password1": "Brand#New123", "new_password2": "Brand#New123"},
        )
        self.assertRedirects(response, reverse("accounts:profile"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)
        self.assertTrue(User.objects.get(username="emp").check_password("Brand#New123"))
