#!/usr/bin/env python
"""Django's command-line utility (runserver, migrate, test ... shob ekhan theke cholay)."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django install kora nei. Age virtual environment activate kore "
            "'pip install -r requirements.txt' chalan."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
