from django.urls import path

from . import views_admin, views_employee, views_hr, views_modules, views_trainer

app_name = "training"

urlpatterns = [
    # ----- Admin -----
    path("admin-panel/", views_admin.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/staff/", views_admin.staff_list, name="staff_list"),
    path("admin-panel/staff/add/", views_admin.staff_add, name="staff_add"),
    path("admin-panel/staff/<int:pk>/delete/", views_admin.staff_delete, name="staff_delete"),
    path("admin-panel/employees/", views_admin.admin_employees, name="admin_employees"),
    path("admin-panel/employees/<int:pk>/approve/", views_admin.employee_approve, name="employee_approve"),
    path("admin-panel/employees/<int:pk>/delete/", views_admin.employee_delete, name="employee_delete"),
    path("admin-panel/categories/", views_admin.category_list, name="category_list"),
    path("admin-panel/categories/add/", views_admin.category_add, name="category_add"),
    path("admin-panel/categories/<int:pk>/edit/", views_admin.category_edit, name="category_edit"),
    path("admin-panel/categories/<int:pk>/delete/", views_admin.category_delete, name="category_delete"),

    # ----- Modules (Admin + Trainer) -----
    path("modules/", views_modules.module_list, name="module_list"),
    path("modules/add/", views_modules.module_create, name="module_create"),
    path("modules/<int:pk>/", views_modules.module_detail, name="module_detail"),
    path("modules/<int:pk>/edit/", views_modules.module_edit, name="module_edit"),
    path("modules/<int:pk>/delete/", views_modules.module_delete, name="module_delete"),
    path("modules/<int:module_id>/lessons/add/", views_modules.lesson_add, name="lesson_add"),
    path("lessons/<int:pk>/edit/", views_modules.lesson_edit, name="lesson_edit"),
    path("lessons/<int:pk>/delete/", views_modules.lesson_delete, name="lesson_delete"),
    path("modules/<int:module_id>/resources/add/", views_modules.resource_add, name="resource_add"),
    path("resources/<int:pk>/delete/", views_modules.resource_delete, name="resource_delete"),
    path("modules/<int:module_id>/tasks/add/", views_modules.task_add, name="task_add"),
    path("tasks/<int:pk>/edit/", views_modules.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete/", views_modules.task_delete, name="task_delete"),

    # ----- HR Manager -----
    path("hr/", views_hr.hr_dashboard, name="hr_dashboard"),
    path("hr/employees/", views_hr.hr_employees, name="hr_employees"),
    path("hr/employees/<int:pk>/", views_hr.hr_employee_detail, name="hr_employee_detail"),
    path("hr/employees/<int:pk>/assign-trainer/", views_hr.hr_assign_trainer, name="hr_assign_trainer"),
    path("hr/skill-gaps/", views_hr.hr_skill_gaps, name="hr_skill_gaps"),
    path("hr/progress/", views_hr.hr_progress, name="hr_progress"),

    # ----- Trainer -----
    path("trainer/", views_trainer.trainer_dashboard, name="trainer_dashboard"),
    path("trainer/employees/", views_trainer.trainer_employees, name="trainer_employees"),
    path("trainer/employees/<int:pk>/", views_trainer.trainer_employee_detail, name="trainer_employee_detail"),
    path("trainer/assign/", views_trainer.trainer_assign, name="trainer_assign"),
    path("trainer/assign/<int:pk>/remove/", views_trainer.trainer_assignment_delete, name="trainer_assignment_delete"),
    path("trainer/submissions/", views_trainer.trainer_submissions, name="trainer_submissions"),
    path("trainer/submissions/<int:pk>/evaluate/", views_trainer.trainer_evaluate, name="trainer_evaluate"),

    # ----- Employee -----
    path("employee/", views_employee.employee_dashboard, name="employee_dashboard"),
    path("employee/trainings/", views_employee.employee_trainings, name="employee_trainings"),
    path("employee/trainings/<int:pk>/", views_employee.employee_training_detail, name="employee_training_detail"),
    path(
        "employee/trainings/<int:assignment_id>/lessons/<int:lesson_id>/toggle/",
        views_employee.employee_lesson_toggle,
        name="employee_lesson_toggle",
    ),
    path("employee/tasks/", views_employee.employee_tasks, name="employee_tasks"),
    path("employee/tasks/<int:pk>/submit/", views_employee.employee_task_submit, name="employee_task_submit"),
    path("employee/feedback/", views_employee.employee_feedback, name="employee_feedback"),
]
