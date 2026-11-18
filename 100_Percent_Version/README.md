# Corporate Training & Employee Skill Evaluation System - 100% Version

Complete Django web application for corporate training: four roles (Admin, HR Manager, Trainer, Employee), training modules, quizzes with auto-grading, tasks and evaluations, certificates, discussions, notifications, reports, calendar, audit log and bulk import.

**Stack (strict):** HTML5, CSS3, Vanilla JavaScript, Python, Django, SQLite. No React/Vue/Bootstrap/Tailwind. Charts are plain `<canvas>` JavaScript.

## Screenshots

### Hero
<table>
<tr><td width="50%" align="center"><img src="documentation/screenshots/login.png" alt="Login page" width="100%"><br><sub><b>Login page</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/login_dark.png" alt="Login (dark mode)" width="100%"><br><sub><b>Login (dark mode)</b></sub></td></tr>
</table>

### Dashboards (light and dark)
<table>
<tr><td width="50%" align="center"><img src="documentation/screenshots/admin_dashboard.png" alt="Admin dashboard" width="100%"><br><sub><b>Admin dashboard</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/admin_dashboard_dark.png" alt="Admin dashboard (dark)" width="100%"><br><sub><b>Admin dashboard (dark)</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="documentation/screenshots/hr_dashboard.png" alt="HR dashboard" width="100%"><br><sub><b>HR dashboard</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/trainer_dashboard.png" alt="Trainer dashboard" width="100%"><br><sub><b>Trainer dashboard</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="documentation/screenshots/employee_dashboard.png" alt="Employee dashboard" width="100%"><br><sub><b>Employee dashboard</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/employee_dashboard_dark.png" alt="Employee dashboard (dark)" width="100%"><br><sub><b>Employee dashboard (dark)</b></sub></td></tr>
</table>

### Learning: quizzes, progress and certificates
<table>
<tr><td width="50%" align="center"><img src="documentation/screenshots/employee_quiz_take.png" alt="Taking a quiz" width="100%"><br><sub><b>Taking a quiz</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/employee_quiz_result.png" alt="Quiz result" width="100%"><br><sub><b>Quiz result</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="documentation/screenshots/employee_training_detail.png" alt="Module page: lessons, tasks, discussion" width="100%"><br><sub><b>Module page: lessons, tasks, discussion</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/quiz_manage.png" alt="Quiz builder" width="100%"><br><sub><b>Quiz builder</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="documentation/screenshots/certificate.png" alt="Printable certificate" width="100%"><br><sub><b>Printable certificate</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/employee_certificates.png" alt="My certificates" width="100%"><br><sub><b>My certificates</b></sub></td></tr>
</table>

### Management: reports, import, audit, calendar
<table>
<tr><td width="50%" align="center"><img src="documentation/screenshots/admin_reports.png" alt="Reports and analytics" width="100%"><br><sub><b>Reports and analytics</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/admin_audit_log.png" alt="Audit log" width="100%"><br><sub><b>Audit log</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="documentation/screenshots/admin_bulk_import.png" alt="Bulk CSV import" width="100%"><br><sub><b>Bulk CSV import</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/admin_calendar.png" alt="Deadline calendar" width="100%"><br><sub><b>Deadline calendar</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="documentation/screenshots/bell_dropdown.png" alt="Notification bell" width="100%"><br><sub><b>Notification bell</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/hr_employees.png" alt="Employee directory" width="100%"><br><sub><b>Employee directory</b></sub></td></tr>
</table>

### Mobile
<table>
<tr><td width="50%" align="center"><img src="documentation/screenshots/mobile_employee_dashboard.png" alt="Mobile dashboard" width="100%"><br><sub><b>Mobile dashboard</b></sub></td><td width="50%" align="center"><img src="documentation/screenshots/mobile_calendar.png" alt="Mobile calendar" width="100%"><br><sub><b>Mobile calendar</b></sub></td></tr>
</table>


## Folder structure

```
Corporate_Training_System/
├── MASTER_README.md
├── 50_Percent_Version/               (frozen, complete)
└── 100_Percent_Version/
    ├── README.md                     (this file)
    ├── run_mac.sh                    (one-command setup + run for macOS)
    ├── backend/
    │   ├── manage.py, requirements.txt
    │   ├── config/                   settings.py, urls.py
    │   ├── accounts/                 User (role, is_approved), auth, password reset, decorators, template tags
    │   ├── core/                     Notification, AuditLog, reports, CSV export/import, calendar, protected media
    │   └── training/                 models (Quiz, Certificate, Comment ...), services, views_*, tests, seed_demo
    ├── frontend/
    │   ├── templates/                base.html, layouts/, partials/, accounts/, shared/, *_panel/, core/
    │   └── static/                   css/style.css, css/theme.css, js/app.js, js/charts.js
    └── documentation/
        ├── Project_Report.pdf
        ├── How_To_Build_Banglish.pdf
        └── screenshots/
```

## Quick start on macOS / VS Code

Requirements: Python 3.9+ (`python3 --version`).

### Option A - one command
```bash
cd "Corporate_Training_System/100_Percent_Version"
chmod +x run_mac.sh
./run_mac.sh
```

### Option B - step by step
```bash
cd "Corporate_Training_System/100_Percent_Version/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # demo users + data (add --reset to start fresh)
python manage.py runserver
```

Open **http://127.0.0.1:8000/**. Stop with `Ctrl + C`.

## Demo credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@123` |
| HR Manager | `hr_manager` | `Hr@12345` |
| Trainer | `trainer1`, `trainer2` | `Trainer@123` |
| Employee | `employee1`, `employee2`, `employee3` | `Employee@123` |
| Pending employee (Admin must approve) | `newhire` | `Employee@123` |

**Passwords have NO rules now** - any length (even 1 character) is accepted (`AUTH_PASSWORD_VALIDATORS = []`).

**Forgot password demo:** the reset email is printed in the Terminal where `runserver` is running (console email backend). Copy the link from there into the browser.

## What is new in the 100% version

- **Design:** new `theme.css` - gradients, hero banners, cards with shadows, dark mode toggle (remembered), notification bell, mobile friendly, print-ready certificate.
- **Quizzes:** trainers build quizzes (single/multiple choice, true/false); auto-graded, pass mark, attempts history.
- **Progress** = lessons + tasks + passed quizzes. At 100% a **Certificate** is issued automatically with a public verify page (`/verify/<code>/`).
- **Discussion** (comments & replies) on each module with notifications.
- **Notifications** centre + bell dropdown.
- **Audit log** (login, approve, import, export ...).
- **Reports** with CSV export (CSV-injection safe).
- **Calendar** (month view of deadlines) for every role.
- **Bulk CSV import** of employees (max 500 rows / 1 MB).
- **Password reset** by email (console backend).
- **Protected media**: no public `/media/`; files are served only through permission-checked views (supports video seeking).
- **Pagination** on long lists.
- **No password rules.**

## Features remaining (out of scope)

Real SMTP email, PostgreSQL / production deployment settings, multi-language UI, 2FA.

## Run the tests

```bash
cd backend
python manage.py check
python manage.py test          # 116 tests (Django 4.2 and 5.2 verified)
```
A real-Chrome end-to-end run covered 35 checks with zero JavaScript errors.

## Push to GitHub

```bash
cd "Corporate_Training_System"
git init
git add .
git commit -m "Corporate Training System - 50% and 100% versions"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo>.git
git push -u origin main
```
`.gitignore` already excludes `venv/`, `db.sqlite3`, `media/` and `__pycache__`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: python3` | Install Python from python.org or `brew install python`. |
| `No module named 'django'` | `source venv/bin/activate` then `pip install -r requirements.txt`. |
| Port in use | `python manage.py runserver 8001`. |
| Login says "waiting for approval" | Log in as `admin` > Employees > Approve. |
| Clean database | Delete `backend/db.sqlite3` and `backend/media/`, then `migrate` and `seed_demo`. |
