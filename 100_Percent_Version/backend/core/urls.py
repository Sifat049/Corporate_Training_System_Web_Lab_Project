from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("notifications/", views.notification_list, name="notifications"),
    path("notifications/<int:pk>/open/", views.notification_open, name="notification_open"),
    path("notifications/read-all/", views.notification_read_all, name="notification_read_all"),
    path("audit-log/", views.audit_log, name="audit_log"),
    path("reports/", views.reports, name="reports"),
    path("reports/export/employees.csv", views.export_employees, name="export_employees"),
    path("reports/export/progress.csv", views.export_progress, name="export_progress"),
    path("reports/export/skill-gaps.csv", views.export_gaps, name="export_gaps"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("files/resource/<int:pk>/", views.resource_file, name="resource_file"),
    path("files/submission/<int:pk>/", views.submission_file, name="submission_file"),
]
