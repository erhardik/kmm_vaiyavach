"""
Standalone helper to bootstrap the default KMM accounts.

Usage:
    python deployment/create_admin_user.py
"""

import os
import sys
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django  # noqa: WPS433

    django.setup()

    from apps.accounts.services import bootstrap_default_users, ensure_role_groups

    ensure_role_groups()
    users = bootstrap_default_users(
        passwords={
            "systemadmin": os.getenv("SYSTEMADMIN_PASSWORD"),
            "admin": os.getenv("ADMIN_PASSWORD"),
            "viewer": os.getenv("VIEWER_PASSWORD"),
        },
        reset_passwords=True,
    )
    for user in users:
        print(f"{user['username']}: {user['password'] or 'unchanged'}")


if __name__ == "__main__":
    main()
