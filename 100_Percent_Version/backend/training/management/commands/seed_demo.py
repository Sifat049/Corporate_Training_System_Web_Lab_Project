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
    Choice,
    Comment,
    Question,
    Quiz,
    QuizAttempt,
)
from core.models import AuditLog, Notification
from core.utils import audit, notify
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
            Notification.objects.all().delete()
            AuditLog.objects.all().delete()
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


        # ================= 100% version demo data =================
        def make_quiz(module, owner, title, pass_percent, questions):
            quiz = Quiz.objects.create(module=module, title=title, pass_percent=pass_percent, created_by=owner,
                                       description="Choose the best answer. You can retry any time.")
            for order, (text, options, right) in enumerate(questions, start=1):
                q = Question.objects.create(quiz=quiz, text=text, order=order)
                for i, opt in enumerate(options):
                    Choice.objects.create(question=q, text=opt, is_correct=(i == right))
            return quiz

        py_quiz = make_quiz(python, t1, "Python Basics Check", 60, [
            ("Which keyword defines a function in Python?", ["func", "def", "function", "lambda only"], 1),
            ("What is the result of 7 // 2 in Python?", ["3.5", "4", "3", "2"], 2),
            ("Which data type stores key-value pairs?", ["list", "tuple", "dict", "set"], 2),
            ("How do you start a for loop over numbers 0 to 4?", ["for i in range(5):", "for i = 0 to 4", "loop i in 5", "foreach i in 5"], 0),
        ])
        comm_quiz = make_quiz(comm, t2, "Email Etiquette Quiz", 60, [
            ("What should a good email subject line do?", ["Be empty", "Clearly state the topic", "Use ALL CAPS", "Be as long as possible"], 1),
            ("A meeting should end with...", ["Nothing", "Action items and owners", "A joke", "A new meeting"], 1),
        ])
        safety_quiz = make_quiz(safety, admin, "Safety Rules Quiz", 60, [
            ("During a fire alarm you should use...", ["The lift", "The nearest stairs/exit", "Nothing, wait", "The window"], 1),
            ("Incidents must be reported within...", ["24 hours", "1 month", "Never", "1 year"], 0),
        ])

        def attempt(quiz, employee, picks):
            correct = 0
            answers = {}
            qs = list(quiz.questions.prefetch_related("choices"))
            for q, pick in zip(qs, picks):
                choice = list(q.choices.all())[pick]
                answers[str(q.id)] = choice.id
                correct += 1 if choice.is_correct else 0
            percent = round(correct * 100 / len(qs))
            return QuizAttempt.objects.create(quiz=quiz, employee=employee, correct=correct, total=len(qs), percent=percent,
                                              passed=percent >= quiz.pass_percent, answers=answers)

        attempt(py_quiz, e1, [1, 2, 2, 0])  # Rafiq: python quiz 100%

        # Rafiq "Workplace Safety Essentials" puro complete kore -> certificate auto issue hoy
        a_safe1 = ModuleAssignment.objects.get(employee=e1, module=safety)
        for lesson in safety.lessons.all():
            LessonCompletion.objects.create(assignment=a_safe1, lesson=lesson)
        s_sub = Submission.objects.create(task=safety.tasks.first(), employee=e1, answer_text="1) Know exits 2) Report incidents 3) Keep walkways clear.")
        Feedback.objects.create(submission=s_sub, trainer=t1, score=18, comment="Clear and practical. Well done!")
        s_sub.status = Submission.Status.EVALUATED
        s_sub.save()
        attempt(safety_quiz, e1, [1, 0])
        update_skill_level(e1, safety.category)

        # Discussion
        q1 = Comment.objects.create(module=python, author=e1, body="Should the number guessing program handle wrong input like letters?")
        Comment.objects.create(module=python, author=t1, parent=q1, body="Yes - use try/except around int(input(...)) so the program does not crash.")
        Comment.objects.create(module=comm, author=e2, body="Is it okay to use bullet points in a status email?")

        # Notifications + audit log
        notify(e1, "Your submission 'Write a Number Guessing Program' was evaluated: 85/100.", "/employee/feedback/")
        notify(e2, "New training assigned: Effective Business Communication", f"/employee/trainings/{a_comm2.pk}/")
        notify(t2, "Tania Akter submitted 'Write a Status Update Email'.", "/trainer/submissions/")
        notify(users["admin"], "New employee registration waiting for approval: Mehedi Hasan", "/admin-panel/employees/")
        audit(admin, "seed_demo", "Demo data created")
        audit(admin, "staff_created", "Trainer trainer1 created")
        audit(admin, "category_created", "Technical Skills")

        self.stdout.write(self.style.SUCCESS("Demo data created successfully!"))
        self.stdout.write("Logins:  admin/Admin@123  hr_manager/Hr@12345  trainer1/Trainer@123  employee1/Employee@123")
