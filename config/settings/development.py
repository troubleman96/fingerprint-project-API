"""Development settings.

These settings trade strict production security for local convenience.
Production should use config.settings.production instead.
"""
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
