#!/usr/bin/env python
"""Django command-line entrypoint.

Use this file for local administration tasks:
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
