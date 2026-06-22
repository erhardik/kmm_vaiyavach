from .settings_base import *  # noqa: F401,F403

DEBUG = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost","kmm.pythonanywhere.com"]
