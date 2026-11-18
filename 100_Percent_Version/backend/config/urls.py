"""Root URL configuration - shob URL er entry point."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),       # Django-r built-in admin (developer er jonno)
    path("", include("accounts.urls")),           # login, register, dashboard redirect
    path("", include("training.urls")),           # baki shob role-based page
    path("", include("core.urls")),               # notification, report, calendar, protected files
]

# 100% version: /media/ sorasori khola nai. Upload kora file permission check kore core.views.resource_file diye dey.

# Custom error page (frontend/templates/403.html, 404.html)
handler403 = "accounts.views.permission_denied_view"
handler404 = "accounts.views.not_found_view"
