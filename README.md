# Corporate Training & Employee Skill Evaluation System

A multi-role corporate training platform built with **HTML5, CSS3, Vanilla JavaScript, Python, Django and SQLite** (no frontend frameworks). Four roles: **Admin, HR Manager, Trainer, Employee**.

<p align="center"><img src="100_Percent_Version/documentation/screenshots/admin_dashboard.png" alt="Admin dashboard" width="92%"></p>

| Version | Status | Folder |
|---|---|---|
| 50% | Complete: auth, RBAC, modules, lessons, tasks, evaluation, skill gaps, progress | [`50_Percent_Version`](50_Percent_Version) |
| **100%** | **Complete: + quizzes, certificates, discussion, notifications, reports, calendar, audit log, bulk import, dark mode** | [`100_Percent_Version`](100_Percent_Version) |

## Highlights

- Role-based dashboards with canvas charts (no chart library)
- Quizzes with auto-grading, progress tracking, auto-issued certificates with a public verify page
- Module discussion, notification bell, deadline calendar
- Reports with CSV export, audit log, bulk CSV import
- Protected media downloads, dark mode, mobile friendly
- 116 automated tests and a real-Chrome end-to-end run

## Screenshots

### Hero
<table>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/login.png" alt="Login page" width="100%"><br><sub><b>Login page</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/login_dark.png" alt="Login (dark mode)" width="100%"><br><sub><b>Login (dark mode)</b></sub></td></tr>
</table>

### Dashboards (light and dark)
<table>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/admin_dashboard.png" alt="Admin dashboard" width="100%"><br><sub><b>Admin dashboard</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/admin_dashboard_dark.png" alt="Admin dashboard (dark)" width="100%"><br><sub><b>Admin dashboard (dark)</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/hr_dashboard.png" alt="HR dashboard" width="100%"><br><sub><b>HR dashboard</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/trainer_dashboard.png" alt="Trainer dashboard" width="100%"><br><sub><b>Trainer dashboard</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/employee_dashboard.png" alt="Employee dashboard" width="100%"><br><sub><b>Employee dashboard</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/employee_dashboard_dark.png" alt="Employee dashboard (dark)" width="100%"><br><sub><b>Employee dashboard (dark)</b></sub></td></tr>
</table>

### Learning: quizzes, progress and certificates
<table>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/employee_quiz_take.png" alt="Taking a quiz" width="100%"><br><sub><b>Taking a quiz</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/employee_quiz_result.png" alt="Quiz result" width="100%"><br><sub><b>Quiz result</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/employee_training_detail.png" alt="Module page: lessons, tasks, discussion" width="100%"><br><sub><b>Module page: lessons, tasks, discussion</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/quiz_manage.png" alt="Quiz builder" width="100%"><br><sub><b>Quiz builder</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/certificate.png" alt="Printable certificate" width="100%"><br><sub><b>Printable certificate</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/employee_certificates.png" alt="My certificates" width="100%"><br><sub><b>My certificates</b></sub></td></tr>
</table>

### Management: reports, import, audit, calendar
<table>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/admin_reports.png" alt="Reports and analytics" width="100%"><br><sub><b>Reports and analytics</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/admin_audit_log.png" alt="Audit log" width="100%"><br><sub><b>Audit log</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/admin_bulk_import.png" alt="Bulk CSV import" width="100%"><br><sub><b>Bulk CSV import</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/admin_calendar.png" alt="Deadline calendar" width="100%"><br><sub><b>Deadline calendar</b></sub></td></tr>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/bell_dropdown.png" alt="Notification bell" width="100%"><br><sub><b>Notification bell</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/hr_employees.png" alt="Employee directory" width="100%"><br><sub><b>Employee directory</b></sub></td></tr>
</table>

### Mobile
<table>
<tr><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/mobile_employee_dashboard.png" alt="Mobile dashboard" width="100%"><br><sub><b>Mobile dashboard</b></sub></td><td width="50%" align="center"><img src="100_Percent_Version/documentation/screenshots/mobile_calendar.png" alt="Mobile calendar" width="100%"><br><sub><b>Mobile calendar</b></sub></td></tr>
</table>


## Run it (macOS)

```bash
cd 100_Percent_Version
chmod +x run_mac.sh
./run_mac.sh
```

Open http://127.0.0.1:8000/ and log in:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |
| HR Manager | `hr_manager` | `Hr@12345` |
| Trainer | `trainer1` | `Trainer@123` |
| Employee | `employee1` | `Employee@123` |

Full details: [100% README](100_Percent_Version/README.md), [MASTER_README](MASTER_README.md), and the PDFs in `100_Percent_Version/documentation/`.
