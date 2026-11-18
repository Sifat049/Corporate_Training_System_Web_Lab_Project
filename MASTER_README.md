# Corporate Training & Employee Skill Evaluation System

Academic project built step by step with **HTML5, CSS3, Vanilla JavaScript, Python, Django and SQLite** (no frontend frameworks).

A multi-role platform where an **Admin** manages staff, categories and modules, an **HR Manager** analyses skills and assigns trainers, a **Trainer** builds content and evaluates work, and an **Employee** learns, submits tasks and tracks progress.

## Project layout

```
Corporate_Training_System/
├── MASTER_README.md          <- you are here
├── 50_Percent_Version/       <- COMPLETE and tested (see its README.md)
└── 100_Percent_Version/      <- COMPLETE and tested (see its README.md)
```

## Version comparison

| Area | 50% version (done) | 100% version (done) |
|------|--------------------|------------------------|
| Roles & auth | 4 roles, login, register + Admin approval, RBAC, CSRF, password change | Email verification, password reset by email, 2FA option, audit log |
| Admin | Staff add/remove, employee approval, categories, modules, statistics | Advanced reports, CSV/PDF export, bulk import, system settings |
| HR Manager | Employee profiles, skill levels, basic skill gaps, assign trainers, progress monitor | Training needs forecasting, department analytics, exportable reports |
| Trainer | Assigned employees, modules, lessons, video/doc upload, tasks, evaluation + feedback | Quizzes with auto-grading, rubrics, announcements, batch evaluation |
| Employee | Dashboard, modules, lessons, resources, submit tasks, feedback, progress | Certificates, badges, learning paths, calendar reminders, Q&A forum |
| Skills | Level 1-5 per category, auto-updated from evaluations | Skill matrix, competency frameworks, 360 assessments |
| UI | Responsive sidebar dashboards, canvas charts | Dark mode, notifications centre, richer charts, accessibility audit |
| Data & ops | SQLite, local media | PostgreSQL option, protected downloads, deployment config |
| Quality | 49 automated tests + browser end-to-end run | Wider coverage, performance tests |
| Documentation | Project report PDF + Banglish build tutorial PDF | Updated report, deployment guide, user manual |

## Where to start

1. Read `50_Percent_Version/README.md` for setup and demo logins (macOS).
2. Read `50_Percent_Version/documentation/How_To_Build_Banglish.pdf` to learn how it was built.
3. Read `50_Percent_Version/documentation/Project_Report.pdf` for the full report with screenshots.

## 100% version

Run `100_Percent_Version/run_mac.sh`. It adds quizzes, certificates, discussion, notifications, audit log, reports + CSV export, calendar, bulk import, password reset, dark mode, protected media and a redesigned UI. Passwords have no rules. 116 automated tests + Chrome end-to-end pass. Docs: `100_Percent_Version/documentation/`.
