from .settings_base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost","kmm.pythonanywhere.com"]






# Import routes support
DJANGO_SETTINGS_MODULE = 'config.settings_dev'
