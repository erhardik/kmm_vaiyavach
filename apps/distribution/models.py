from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class DistributionBatchStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    DISPATCHED = "DISPATCHED", "Dispatched"
    DELIVERED = "DELIVERED", "Delivered"
    PARTIAL = "PARTIAL", "Partial"


class DistributionBatch(EventScopedModel):
    batch_name = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)
    assigned_volunteer = models.ForeignKey("masters.Volunteer", on_delete=models.SET_NULL, null=True, blank=True, related_name="distribution_batches")
    status = models.CharField(max_length=20, choices=DistributionBatchStatus.choices, default=DistributionBatchStatus.PENDING)
    remarks = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.batch_name


class DistributionLine(EventScopedModel):
    distribution_batch = models.ForeignKey(DistributionBatch, on_delete=models.CASCADE, related_name="lines")
    upashray = models.ForeignKey("masters.Upashray", on_delete=models.PROTECT, related_name="distribution_lines")
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="distribution_lines")
    required_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    dispatched_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    delivered_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    balance_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    status = models.CharField(max_length=20, choices=DistributionBatchStatus.choices, default=DistributionBatchStatus.PENDING)
    inventory_transaction = models.OneToOneField("inventory.InventoryTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="distribution_line")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["distribution_batch", "upashray", "item"], name="unique_distribution_line"),
        ]

    def __str__(self) -> str:
        return f"{self.distribution_batch} - {self.upashray} - {self.item}"
