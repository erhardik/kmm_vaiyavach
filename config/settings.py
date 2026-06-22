import os

if os.getenv("DJANGO_ENV", "development").lower() in {"production", "prod"}:
    from .settings_prod import *  # noqa: F401,F403
else:
    from .settings_dev import *  # noqa: F401,F403

