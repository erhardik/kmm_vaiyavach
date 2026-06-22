from django.conf import settings
from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class RequirementStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class PriorityLevel(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


class RequirementHeader(EventScopedModel):
    upashray = models.ForeignKey("masters.Upashray", on_delete=models.PROTECT, related_name="requirements")
    requirement_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=RequirementStatus.choices, default=RequirementStatus.DRAFT)

    class Meta:
        ordering = ["-requirement_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.upashray} - {self.requirement_date}"


class RequirementLine(EventScopedModel):
    requirement = models.ForeignKey(RequirementHeader, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="requirement_lines")
    required_qty = models.DecimalField(max_digits=12, decimal_places=3)
    remarks = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["requirement", "item"], name="unique_requirement_item"),
        ]

    def __str__(self) -> str:
        return f"{self.requirement} - {self.item}"


class SpecialRequirement(EventScopedModel):
    upashray = models.ForeignKey("masters.Upashray", on_delete=models.PROTECT, related_name="special_requirements")
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PriorityLevel.choices, default=PriorityLevel.MEDIUM)
    status = models.CharField(max_length=30, choices=RequirementStatus.choices, default=RequirementStatus.DRAFT)
    photo = models.FileField(upload_to="requirements/photos/", blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.upashray} - {self.priority}"

