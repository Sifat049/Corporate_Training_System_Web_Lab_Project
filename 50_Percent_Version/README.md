# Corporate Training & Employee Skill Evaluation System - 50% Version

A working Django web application for corporate training: four roles (Admin, HR Manager, Trainer, Employee), role-based dashboards, training modules with lessons / video & document uploads, assignments, task submissions, trainer feedback, skill-gap analysis and progress tracking.

**Stack (strict):** HTML5, CSS3, Vanilla JavaScript, Python, Django, SQLite. No React/Bootstrap/Tailwind. Charts are drawn with plain `<canvas>` JavaScript (no Chart.js).

## Folder structure

```
Corporate_Training_System/
├── MASTER_README.md
├── 100_Percent_Version/              (empty - next phase)
└── 50_Percent_Version/
    ├── README.md                     (this file)
    ├── run_mac.sh                    (one-command setup + run for macOS)
    ├── backend/
    │   ├── manage.py
    │   ├── requirements.txt
    │   ├── config/                   settings.py, urls.py, wsgi.py, asgi.py
    │   ├── accounts/                 User model (roles), login/register/profile, decorators, forms, tests
    │   └── training/                 models, services, forms, views_{admin,hr,trainer,employee,modules}.py, urls, tests, seed_demo
    ├── frontend/
    │   ├── templates/                base.html, layouts/, partials/, accounts/, shared/, admin_panel/, hr_panel/, trainer_panel/, employee_panel/
    │   └── static/                   css/style.css, js/app.js, js/charts.js, img/favicon.svg
    └── documentation/
        ├── Project_Report.pdf
        ├── How_To_Build_Banglish.pdf
        └── screenshots/
```

## Quick start on macOS

Requirements: Python 3.9+ (3.10+ recommended). Check with `python3 --version`. If missing, install from https://www.python.org/downloads/ or run `brew install python`.

### Option A - one command

```bash
cd "Corporate_Training_System/50_Percent_Version"
chmod +x run_mac.sh
./run_mac.sh
```

### Option B - step by step

```bash
cd "Corporate_Training_System/50_Percent_Version/backend"
python3 -m venv venv                 # create virtual environment
source venv/bin/activate             # activate it
pip install -r requirements.txt      # install Django
python manage.py migrate             # create the SQLite database tables
python manage.py seed_demo           # create demo users + sample training data
python manage.py runserver           # start the server
```

Open **http://127.0.0.1:8000/** in your browser. Stop the server with `Ctrl + C`.

To start over with fresh demo data: `python manage.py seed_demo --reset`

## Demo credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@123` |
| HR Manager | `hr_manager` | `Hr@12345` |
| Trainer | `trainer1` (also `trainer2`) | `Trainer@123` |
| Employee | `employee1` (also `employee2`, `employee3`) | `Employee@123` |
| Pending employee (Admin must approve) | `newhire` | `Employee@123` |

Django's built-in admin site is at `/django-admin/` (log in as `admin`).

## Features implemented (50%)

**Authentication & security** - login/logout, employee self-registration with Admin approval, role-based access control (decorator on every view, 403 page), CSRF protection on all forms, password change, server-side validation, success/error messages.

**Admin** - add/remove HR Managers and Trainers, approve/reject/delete employees, training category CRUD (with required skill level), create/manage all training modules, system-wide statistics dashboard with charts.

**HR Manager** - employee directory with search/filter, employee profile with skill levels, basic skill-gap analysis (current vs required level), assign employees to trainers, monitor training progress.

**Trainer** - view assigned employees, create modules, add lessons, upload video/document resources (type + size validated), create tasks, assign modules to employees, evaluate submissions with score + feedback (skill level updates automatically).

**Employee** - register/login, personal dashboard with charts, assigned modules, lessons (mark complete), resources, tasks, submit/edit answers (text + file) until evaluated, see trainer feedback, live progress tracking.

## Features remaining for 100%

Email notifications, password reset by email, certificates / PDF export, advanced analytics and reports (CSV/PDF export), quizzes with auto-grading, discussion/Q&A per module, calendar & deadline reminders, audit log, bulk CSV import of employees, protected (permission-checked) media downloads, pagination for large lists, multi-language, and production deployment settings (PostgreSQL, HTTPS, environment variables).

## Run the tests

```bash
cd backend
python manage.py check
python manage.py test          # 49 automated tests
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: python3` | Install Python (see above). |
| `ModuleNotFoundError: No module named 'django'` | Activate the virtual environment: `source venv/bin/activate`, then `pip install -r requirements.txt`. |
| `That port is already in use` | `python manage.py runserver 8001` and open port 8001. |
| Page has no styling | Run the server from the `backend` folder; check `frontend/static/css/style.css` exists. |
| Login says "waiting for admin approval" | Log in as `admin`, open **Employees**, click **Approve**. |
| Want a clean database | Delete `backend/db.sqlite3` and `backend/media/`, then `migrate` and `seed_demo` again. |

More detail is in `documentation/How_To_Build_Banglish.pdf` (section 17: common errors).
