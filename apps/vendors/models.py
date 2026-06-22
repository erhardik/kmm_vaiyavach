from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class VendorQuote(EventScopedModel):
    vendor = models.ForeignKey("masters.Vendor", on_delete=models.PROTECT, related_name="quotes")
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="vendor_quotes")
    rate = models.DecimalField(max_digits=14, decimal_places=2)
    home_delivery = models.BooleanField(default=False)
    pickup_available = models.BooleanField(default=False)
    return_unused = models.BooleanField(default=False)
    credit_days = models.PositiveIntegerField(default=0)
    gst_included = models.BooleanField(default=False)
    quote_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["rate", "quote_date"]
        indexes = [
            models.Index(fields=["event", "item", "rate"]),
        ]

    def __str__(self) -> str:
        return f"{self.vendor} - {self.item} - {self.rate}"

