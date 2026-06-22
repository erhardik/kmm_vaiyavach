import uuid

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
    class StayType(models.TextChoices):
        SANGH_UPASHRAY = "SANGH_UPASHRAY", "Sangh Upashray"
        STHIRVAS = "STHIRVAS", "Sthirvas"

    order_number = models.CharField(max_length=24, unique=True, editable=False, null=True, blank=True)
    upashray = models.ForeignKey("masters.Upashray", on_delete=models.PROTECT, related_name="requirements")
    requirement_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)
    volunteer_name = models.CharField(max_length=120, blank=True, default="")
    pujya_shri_name = models.CharField(max_length=120, blank=True, default="")
    pujya_shri_mobile = models.CharField(max_length=20, blank=True, default="")
    current_address = models.TextField(blank=True, default="")
    thana_count = models.PositiveIntegerField(null=True, blank=True)
    area = models.CharField(max_length=120, blank=True, default="")
    chaturmas_place_address = models.TextField(blank=True, default="")
    chaturmas_entry_date = models.DateField(null=True, blank=True)
    caretaker_name = models.CharField(max_length=120, blank=True, default="")
    caretaker_mobile = models.CharField(max_length=20, blank=True, default="")
    stay_type = models.CharField(max_length=20, choices=StayType.choices, blank=True, default=StayType.STHIRVAS)
    status = models.CharField(max_length=30, choices=RequirementStatus.choices, default=RequirementStatus.DRAFT)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    packed_by_name = models.CharField(max_length=120, blank=True, default="")
    checked_by_name = models.CharField(max_length=120, blank=True, default="")
    distributed_to_ms_by_name = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self) -> str:
        if self.order_number:
            return f"{self.order_number} - {self.upashray}"
        return f"{self.upashray} - {self.requirement_date}"

    def save(self, *args, **kwargs):
        if not self.order_number and self.status == RequirementStatus.SUBMITTED:
            token = uuid.uuid4().hex[:8].upper()
            date_token = timezone.localdate().strftime("%Y%m%d")
            base_number = f"REQ-{date_token}-{token}"
            while RequirementHeader.objects.filter(order_number=base_number).exists():
                token = uuid.uuid4().hex[:8].upper()
                base_number = f"REQ-{date_token}-{token}"
            self.order_number = base_number
        super().save(*args, **kwargs)


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

