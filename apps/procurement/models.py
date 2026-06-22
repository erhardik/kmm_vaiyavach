from django.conf import settings
from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SENT = "SENT", "Sent"
    PARTIAL = "PARTIAL", "Partial"
    RECEIVED = "RECEIVED", "Received"
    CANCELLED = "CANCELLED", "Cancelled"


class PurchaseOrder(EventScopedModel):
    vendor = models.ForeignKey("masters.Vendor", on_delete=models.PROTECT, related_name="purchase_orders")
    po_number = models.CharField(max_length=50)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.DRAFT)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "po_number"], name="unique_purchase_order_number"),
        ]

    def __str__(self) -> str:
        return self.po_number


class PurchaseOrderLine(EventScopedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="purchase_order_lines")
    qty = models.DecimalField(max_digits=12, decimal_places=3)
    rate = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    inventory_transaction = models.OneToOneField("inventory.InventoryTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_order_line")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["purchase_order", "item"], name="unique_purchase_order_item"),
        ]

    def __str__(self) -> str:
        return f"{self.purchase_order} - {self.item}"


class GoodsReceipt(EventScopedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="goods_receipts")
    date = models.DateField(default=timezone.now)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="goods_receipts")
    remarks = models.TextField(blank=True)
    inventory_transaction = models.OneToOneField("inventory.InventoryTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="goods_receipt")

    def __str__(self) -> str:
        return f"GRN {self.id or ''}".strip()
