from __future__ import annotations

import csv
from collections import OrderedDict
from decimal import Decimal
from io import BytesIO, StringIO

from django.db.models import Sum
from openpyxl import Workbook

from apps.auditlog.models import ActivityLog
from apps.dashboard.services import build_item_control_center, get_dashboard_event_queryset
from apps.inventory.models import InventoryTransaction
from apps.masters.models import Event
from apps.funds.models import Donation, FundTransaction, FundTransactionType
from apps.requirements.models import RequirementLine
from apps.sponsorship.models import SponsorMaterialReceipt, SponsorshipCommitment


def _to_text(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    return value if value is not None else ""


def build_report_home_summary(event: Event | None) -> dict:
    if event is None:
        return {
            "requirement_total": Decimal("0"),
            "sponsorship_total": Decimal("0"),
            "received_total": Decimal("0"),
            "transaction_total": 0,
            "donation_total": Decimal("0"),
            "expense_total": Decimal("0"),
            "net_fund_total": Decimal("0"),
        }

    requirement_total = RequirementLine.objects.filter(event=event).count()
    sponsorship_total = SponsorshipCommitment.objects.filter(event=event).count()
    received_total = SponsorMaterialReceipt.objects.filter(event=event).count()
    transaction_total = InventoryTransaction.objects.filter(event=event).count()
    donation_total = Donation.objects.filter(event=event).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expense_total = (
        FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.EXPENSE).aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )
    return {
        "requirement_total": requirement_total,
        "sponsorship_total": sponsorship_total,
        "received_total": received_total,
        "transaction_total": transaction_total,
        "donation_total": donation_total,
        "expense_total": expense_total,
        "net_fund_total": _fund_net_total(event),
    }


def _fund_net_total(event: Event) -> Decimal:
    income = FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.INCOME).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expense = FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.EXPENSE).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    transfer = FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.TRANSFER).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    adjustment = FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.ADJUSTMENT).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return income - expense + adjustment - transfer


def build_item_control_export(event, category=None, pending_only=False, fully_covered=False, shortage=False):
    rows, summary = build_item_control_center(
        event,
        category=category,
        pending_only=pending_only,
        fully_covered=fully_covered,
        shortage=shortage,
    )
    export_rows = []
    for row in rows:
        export_rows.append(
            OrderedDict(
                [
                    ("Item", row["item"].display_name()),
                    ("Category", row["item"].get_category_display()),
                    ("Rate", row["rate"]),
                    ("Required", row["required"]),
                    ("Acquired", row["acquired"]),
                    ("Sponsored", row["sponsored"]),
                    ("Received", row["received"]),
                    ("Purchased Qty", row["purchased_qty"]),
                    ("Purchase Needed", row["purchase_needed"]),
                    ("Remaining", row["remaining"]),
                    ("Shortage", row["shortage"]),
                    ("Stock", row["stock"]),
                    ("Distributed", row["distributed"]),
                    ("Balance", row["balance"]),
                    ("Required Cost", row["required_cost"]),
                    ("Purchase Cost", row["actual_purchase_cost"]),
                    ("Source", row["source_type"]),
                ]
            )
        )
    return export_rows, summary


def build_inventory_ledger_export(event):
    rows = []
    transactions = (
        InventoryTransaction.objects.filter(event=event)
        .select_related("item", "created_by", "updated_by")
        .order_by("-created_at", "-id")
    )
    for tx in transactions:
        rows.append(
            OrderedDict(
                [
                    ("Timestamp", tx.created_at),
                    ("Item", tx.item.display_name() if hasattr(tx.item, "display_name") else str(tx.item)),
                    ("Type", tx.get_transaction_type_display()),
                    ("Qty", tx.qty),
                    ("Source Module", tx.source_module),
                    ("Reference", tx.reference_label or tx.reference_id),
                    ("Unit Rate", tx.unit_rate),
                    ("Remarks", tx.remarks),
                    ("Created By", tx.created_by.get_username() if tx.created_by_id else ""),
                ]
            )
        )
    return rows


def build_fund_ledger_export(event):
    rows = []
    transactions = FundTransaction.objects.filter(event=event).order_by("-date", "-id")
    for tx in transactions:
        rows.append(
            OrderedDict(
                [
                    ("Date", tx.date),
                    ("Type", tx.get_transaction_type_display()),
                    ("Category", tx.category),
                    ("Amount", tx.amount),
                    ("Reference Module", tx.reference_module),
                    ("Reference ID", tx.reference_id),
                    ("Remarks", tx.remarks),
                ]
            )
        )
    return rows


def build_requirement_export(event):
    rows = []
    lines = RequirementLine.objects.filter(event=event).select_related("requirement", "item").order_by("requirement__requirement_date", "id")
    for line in lines:
        rows.append(
            OrderedDict(
                [
                    ("Requirement", str(line.requirement)),
                    ("Upashray", line.requirement.upashray.name),
                    ("Item", line.item.display_name()),
                    ("Required Qty", int(line.required_qty) if line.required_qty == int(line.required_qty) else line.required_qty),
                    ("Remarks", line.remarks),
                ]
            )
        )
    return rows


def build_sponsorship_export(event):
    rows = []
    commitments = SponsorshipCommitment.objects.filter(event=event).select_related("sponsor", "item").order_by("sponsor__sponsor_name", "item__item_name")
    for commitment in commitments:
        rows.append(
            OrderedDict(
                [
                    ("Sponsor", commitment.sponsor.sponsor_name),
                    ("Item", commitment.item.display_name()),
                    ("Committed Qty", commitment.committed_qty),
                    ("Received Qty", commitment.received_qty),
                    ("Status", commitment.get_status_display()),
                    ("Expected Date", commitment.expected_date),
                ]
            )
        )
    return rows


def build_analytics_summary(event: Event | None) -> dict:
    if event is None:
        return {
            "pending_items": 0,
            "shortage_items": 0,
            "activity_count": 0,
            "donation_total": Decimal("0"),
            "expense_total": Decimal("0"),
            "net_fund_total": Decimal("0"),
        }

    rows, summary = build_item_control_center(event)
    shortage_items = sum(1 for row in rows if row["purchase_needed"] > 0)
    activity_count = ActivityLog.objects.filter(event=event).count()
    donation_total = Donation.objects.filter(event=event).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expense_total = FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.EXPENSE).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return {
        "pending_items": summary["pending_items"],
        "shortage_items": shortage_items,
        "activity_count": activity_count,
        "donation_total": donation_total,
        "expense_total": expense_total,
        "net_fund_total": _fund_net_total(event),
    }


def build_top_shortage_items(event, limit=10):
    rows, _summary = build_item_control_center(event, shortage=True)
    return sorted(rows, key=lambda row: row["purchase_needed"], reverse=True)[:limit]


def build_recent_activity(event, limit=20):
    return ActivityLog.objects.filter(event=event).select_related("user").order_by("-timestamp")[:limit]


def export_rows_to_csv(rows, headers):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_to_text(row.get(header, "")) for header in headers])
    return buffer.getvalue()


def export_rows_to_xlsx(rows, headers, sheet_title="Report"):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title[:31]
    sheet.append(list(headers))
    for row in rows:
        sheet.append([_to_text(row.get(header, "")) for header in headers])
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def get_default_event():
    return get_dashboard_event_queryset().first()
