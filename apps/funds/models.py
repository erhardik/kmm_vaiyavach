from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class DonationMode(models.TextChoices):
    CASH = "CASH", "Cash"
    UPI = "UPI", "UPI"
    BANK = "BANK", "Bank"
    CHEQUE = "CHEQUE", "Cheque"
    OTHER = "OTHER", "Other"


class FundTransactionType(models.TextChoices):
    INCOME = "INCOME", "Income"
    EXPENSE = "EXPENSE", "Expense"
    TRANSFER = "TRANSFER", "Transfer"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class Donation(EventScopedModel):
    donor_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    mode = models.CharField(max_length=20, choices=DonationMode.choices, default=DonationMode.CASH)
    reference_person = models.CharField(max_length=120, blank=True)
    received_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.donor_name} - {self.amount}"


class FundTransaction(EventScopedModel):
    transaction_type = models.CharField(max_length=20, choices=FundTransactionType.choices)
    category = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)
    reference_module = models.CharField(max_length=80, blank=True)
    reference_id = models.CharField(max_length=80, blank=True)

    def __str__(self) -> str:
        return f"{self.transaction_type} - {self.amount}"

