"""
Demo data toiri korar command:   python manage.py seed_demo
Demo login (shob role) o ekhan theke toiri hoy. Abar fresh kore shuru korte: python manage.py seed_demo --reset
"""
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from training.models import (
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
from training.services import update_skill_level

DEMO_USERS = [
    # username, password, role, first, last, email, extra
    ("admin", "Admin@123", "admin", "System", "Admin", "admin@corptrain.local", {}),
    ("hr_manager", "Hr@12345", "hr", "Sadia", "Rahman", "sadia.hr@corptrain.local", {}),
    ("trainer1", "Trainer@123", "trainer", "Imran", "Hossain", "imran@corptrain.local", {"expertise": "Python, Data & Software Engineering"}),
    ("trainer2", "Trainer@123", "trainer", "Nusrat", "Jahan", "nusrat@corptrain.local", {"expertise": "Communication & Leadership"}),
    ("employee1", "Employee@123", "employee", "Rafiq", "Ahmed", "rafiq@corptrain.local", {"department": "Engineering", "job_title": "Junior Developer", "trainer": "trainer1"}),
    ("employee2", "Employee@123", "employee", "Tania", "Akter", "tania@corptrain.local", {"department": "Marketing", "job_title": "Marketing Executive", "trainer": "trainer2"}),
    ("employee3", "Employee@123", "employee", "Karim", "Uddin", "karim@corptrain.local", {"department": "Sales", "job_title": "Sales Associate", "trainer": "trainer1"}),
]


class Command(BaseCommand):
    help = "Create demo users and sample training data."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all existing data first.")

    def handle(self, *args, **options):
        if options["reset"]:
            TrainingModule.objects.all().delete()
            TrainingCategory.objects.all().delete()
            User.objects.all().delete()
            self.stdout.write("Old data deleted.")
        elif User.objects.filter(username="admin").exists():
            self.stdout.write(self.style.WARNING("Demo data already exists. Use --reset to recreate."))
            return

        users = {}
        for username, password, role, first, last, email, extra in DEMO_USERS:
            if role == "admin":
                user = User.objects.create_superuser(username, email, password, first_name=first, last_name=last)
            else:
                user = User(username=username, email=email, first_name=first, last_name=last, role=role, is_approved=True)
                user.set_password(password)
                user.save()
            users[username] = user
            if role == "trainer":
                profile = user.trainer_profile
                profile.expertise = extra.get("expertise", "")
                profile.save()
        for username, *_rest, extra in DEMO_USERS:
            if users[username].role == "employee":
                profile = users[username].employee_profile
                profile.department = extra["department"]
                profile.job_title = extra["job_title"]
                profile.trainer = users[extra["trainer"]]
                profile.save()

        # Ekjon pending employee (Admin approve korar demo er jonno)
        pending = User(username="newhire", email="mehedi@corptrain.local", first_name="Mehedi", last_name="Hasan", role="employee", is_approved=False)
        pending.set_password("Employee@123")
        pending.save()
        pending.employee_profile.department = "Finance"
        pending.employee_profile.job_title = "Accounts Trainee"
        pending.employee_profile.save()

        cats = {
            name: TrainingCategory.objects.create(name=name, description=desc, required_level=level)
            for name, desc, level in [
                ("Technical Skills", "Programming, tools and technical problem solving.", 4),
                ("Communication", "Written and verbal communication at work.", 3),
                ("Leadership", "Team management and decision making.", 3),
                ("Compliance & Safety", "Workplace rules, safety and company policy.", 3),
            ]
        }

        today = timezone.localdate()
        t1, t2, admin = users["trainer1"], users["trainer2"], users["admin"]

        def make_module(title, cat, owner, desc, difficulty, hours, lessons, tasks):
            module = TrainingModule.objects.create(
                title=title, category=cats[cat], created_by=owner, description=desc, difficulty=difficulty, duration_hours=hours
            )
            for i, (ltitle, lcontent) in enumerate(lessons, start=1):
                Lesson.objects.create(module=module, title=ltitle, content=lcontent, order=i)
            for ttitle, instr, days, score in tasks:
                Task.objects.create(
                    module=module, title=ttitle, instructions=instr, due_date=today + timedelta(days=days),
                    max_score=score, created_by=owner,
                )
            return module

        python = make_module(
            "Python for Beginners", "Technical Skills", t1,
            "Learn Python basics: variables, conditions, loops and functions with hands-on practice.", "beginner", 12,
            [
                ("Variables and Data Types", "Python e variable e value rakha hoy. Example: name = 'Rafiq', age = 24. Common types: int, float, str, bool, list, dict."),
                ("Conditions and Loops", "if / elif / else diye decision nei. for ar while loop diye kaj repeat kori."),
                ("Functions", "def keyword diye function banano hoy. Function code reuse korte help kore."),
            ],
            [
                ("Write a Number Guessing Program", "Write a Python program that picks a random number from 1 to 20 and lets the user guess until correct. Paste your code in the answer box.", 14, 100),
                ("Functions Practice Sheet", "Create 3 small functions: add(a,b), is_even(n) and greet(name). Explain how each one works.", 21, 50),
            ],
        )
        comm = make_module(
            "Effective Business Communication", "Communication", t2,
            "Write clear emails, run productive meetings and give feedback professionally.", "intermediate", 8,
            [
                ("Writing Professional Emails", "A good email has a clear subject, short paragraphs and one clear request."),
                ("Running Effective Meetings", "Share the agenda early, keep time, and end with action items and owners."),
            ],
            [("Write a Status Update Email", "Write a 150-200 word email updating your manager on a project that is slightly delayed.", 10, 100)],
        )
        safety = make_module(
            "Workplace Safety Essentials", "Compliance & Safety", admin,
            "Basic safety rules, emergency procedures and reporting every employee must know.", "beginner", 4,
            [
                ("Emergency Exits and Evacuation", "Know your nearest exit and the assembly point. Never use the lift during a fire alarm."),
                ("Reporting Incidents", "Report every incident or near-miss to your supervisor within 24 hours."),
            ],
            [("Safety Quiz Reflection", "List three safety rules you learned and how you will apply them in your own work area.", 7, 20)],
        )
        leadership = make_module(
            "Team Leadership Basics", "Leadership", t1,
            "Delegation, motivation and giving feedback as a new team lead.", "intermediate", 10,
            [
                ("What Makes a Good Leader", "Good leaders listen, set clear goals and take responsibility."),
                ("Delegation", "Delegate the outcome, not every step. Check progress without micro-managing."),
            ],
            [("Delegation Plan", "Choose a real project and write who you would delegate each part to and why.", 15, 100)],
        )

        # Ekta sample document resource (file upload feature demo)
        resource = Resource(module=python, title="Python Quick Reference (Cheat Sheet)", kind="document", uploaded_by=t1)
        resource.file.save(
            "python_cheat_sheet.txt",
            ContentFile(b"PYTHON CHEAT SHEET\n==================\nprint('hello')\nfor i in range(5): print(i)\ndef add(a, b): return a + b\n"),
            save=False,
        )
        resource.save()

        # ---- Assignments ----
        e1, e2, e3 = users["employee1"], users["employee2"], users["employee3"]
        a_py1 = ModuleAssignment.objects.create(employee=e1, module=python, assigned_by=t1, due_date=today + timedelta(days=30))
        ModuleAssignment.objects.create(employee=e1, module=safety, assigned_by=t1, due_date=today + timedelta(days=20))
        a_comm2 = ModuleAssignment.objects.create(employee=e2, module=comm, assigned_by=t2, due_date=today + timedelta(days=25))
        ModuleAssignment.objects.create(employee=e3, module=python, assigned_by=t1, due_date=today + timedelta(days=30))
        ModuleAssignment.objects.create(employee=e3, module=leadership, assigned_by=t1, due_date=today + timedelta(days=40))

        # ---- Sample progress: Rafiq 2 ta lesson complete + 1 ta task submit & evaluate ----
        for lesson in python.lessons.all()[:2]:
            LessonCompletion.objects.create(assignment=a_py1, lesson=lesson)
        task1 = python.tasks.first()
        sub = Submission.objects.create(
            task=task1, employee=e1, answer_text="import random\nsecret = random.randint(1, 20)\nwhile True:\n    g = int(input('Guess: '))\n    if g == secret: break\nprint('Correct!')",
        )
        Feedback.objects.create(submission=sub, trainer=t1, score=85, comment="Good logic and clean code. Add hints like 'too high/low' and handle invalid input next time.")
        sub.status = Submission.Status.EVALUATED
        sub.save()
        update_skill_level(e1, python.category)
        a_py1.recalculate()

        # Tania ekta task submit korse, evaluation pending
        lesson = comm.lessons.first()
        LessonCompletion.objects.create(assignment=a_comm2, lesson=lesson)
        Submission.objects.create(task=comm.tasks.first(), employee=e2, answer_text="Subject: Update on Project Alpha timeline\n\nHi Anika, the final testing needs two more days...")
        a_comm2.recalculate()

        self.stdout.write(self.style.SUCCESS("Demo data created successfully!"))
        self.stdout.write("Logins:  admin/Admin@123  hr_manager/Hr@12345  trainer1/Trainer@123  employee1/Employee@123")
