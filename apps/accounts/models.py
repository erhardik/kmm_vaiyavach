from django.conf import settings
from django.db import models

from config.models import EventScopedModel, TimeStampedModel


class RoleChoices(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    PROCUREMENT_TEAM = "PROCUREMENT_TEAM", "Procurement Team"
    SPONSORSHIP_TEAM = "SPONSORSHIP_TEAM", "Sponsorship Team"
    DISTRIBUTION_TEAM = "DISTRIBUTION_TEAM", "Distribution Team"
    ACCOUNTS_TEAM = "ACCOUNTS_TEAM", "Accounts Team"
    VIEWER = "VIEWER", "Viewer"


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    mobile = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    area = models.CharField(max_length=120, blank=True)

    def __str__(self) -> str:
        return self.user.get_username()


class EventMembership(EventScopedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_memberships")
    role = models.CharField(max_length=40, choices=RoleChoices.choices, default=RoleChoices.VIEWER)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "user"], name="unique_event_membership_user"),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.event} - {self.role}"

