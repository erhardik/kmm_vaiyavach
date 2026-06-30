from django.conf import settings
from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class InventoryTransactionType(models.TextChoices):
    PURCHASE = "PURCHASE", "Purchase"
    DONATION = "DONATION", "Donation"
    SPONSORSHIP_RECEIPT = "SPONSORSHIP_RECEIPT", "Sponsorship Receipt"
    DISTRIBUTION = "DISTRIBUTION", "Distribution"
    RETURN = "RETURN", "Return"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"
    DAMAGE = "DAMAGE", "Damage"
    RESERVATION = "RESERVATION", "Reservation"
    RELEASE = "RELEASE", "Release"


class PurchaseLot(EventScopedModel):
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="purchase_lots")
    qty = models.DecimalField(max_digits=12, decimal_places=3)
    unit_rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    vendor = models.ForeignKey("masters.Vendor", on_delete=models.PROTECT, null=True, blank=True)
    managed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_purchase_lots")
    notes = models.TextField(blank=True)
    transaction_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["event", "item"]),
        ]

    def __str__(self) -> str:
        qty = self.qty
        if qty == int(qty):
            qty = int(qty)
        return f"{self.item} - {qty} @ {self.unit_rate}"


class InventoryTransaction(EventScopedModel):
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="inventory_transactions")
    transaction_type = models.CharField(max_length=40, choices=InventoryTransactionType.choices)
    qty = models.DecimalField(max_digits=12, decimal_places=3)
    source_module = models.CharField(max_length=80, blank=True)
    reference_id = models.CharField(max_length=80, blank=True)
    reference_label = models.CharField(max_length=120, blank=True)
    unit_rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    reversal_of = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="reversals")
    purchase_lot = models.ForeignKey(PurchaseLot, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["event", "item", "transaction_type"]),
        ]

    def __str__(self) -> str:
        qty = self.qty
        if qty == int(qty):
            qty = int(qty)
        return f"{self.transaction_type} - {self.item} - {qty}"


class InventoryBalance(EventScopedModel):
    item = models.ForeignKey("masters.Item", on_delete=models.CASCADE, related_name="inventory_balances")
    current_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    reserved_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    available_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    distributed_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "item"], name="unique_inventory_balance_item"),
        ]

    def __str__(self) -> str:
        return f"{self.item} - {self.current_stock}"
