import getpass

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from apps.accounts.services import bootstrap_default_users, ensure_role_groups


class Command(BaseCommand):
    help = "Create the default access roles and login accounts."

    def add_arguments(self, parser):
        parser.add_argument("--systemadmin-password")
        parser.add_argument("--admin-password")
        parser.add_argument("--viewer-password")
        parser.add_argument("--manager-password")
        parser.add_argument("--reset-passwords", action="store_true")

    def handle(self, *args, **options):
        ensure_role_groups()
        passwords = {
            "systemadmin": options.get("systemadmin_password"),
            "admin": options.get("admin_password"),
            "viewer": options.get("viewer_password"),
            "manager": options.get("manager_password"),
        }
        for key in passwords:
            if not passwords[key]:
                prompt = _("Enter password for {role}").format(role=key)
                passwords[key] = getpass.getpass(f"{prompt}: ")
        created = bootstrap_default_users(
            passwords=passwords,
            reset_passwords=options["reset_passwords"],
        )
        for row in created:
            if row["password"]:
                self.stdout.write(self.style.SUCCESS(f"{row['username']}: {row['password']}"))
            else:
                self.stdout.write(self.style.WARNING(f"{row['username']}: password unchanged"))
