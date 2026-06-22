from django.conf import settings
from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class SponsorshipStatus(models.TextChoices):
    DISCUSSION = "DISCUSSION", "Discussion"
    COMMITTED = "COMMITTED", "Committed"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially Received"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class SponsorshipCommitment(EventScopedModel):
    sponsor = models.ForeignKey("masters.Sponsor", on_delete=models.PROTECT, related_name="commitments")
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="sponsorship_commitments")
    committed_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    received_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=SponsorshipStatus.choices, default=SponsorshipStatus.DISCUSSION)
    remarks = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "sponsor", "item"], name="unique_sponsorship_commitment"),
        ]

    def __str__(self) -> str:
        return f"{self.sponsor} - {self.item}"


class SponsorMaterialReceipt(EventScopedModel):
    commitment = models.ForeignKey(SponsorshipCommitment, on_delete=models.CASCADE, related_name="receipts")
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="sponsorship_receipts")
    received_qty = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    received_date = models.DateField(default=timezone.now)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="sponsorship_receipts")
    inventory_transaction = models.OneToOneField("inventory.InventoryTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="sponsorship_receipt")
    remarks = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.commitment} - {self.received_qty}"

