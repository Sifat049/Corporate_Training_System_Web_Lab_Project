from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # signals file ta load kora - na korle signal kaj korbe na
        from . import signals  # noqa: F401
