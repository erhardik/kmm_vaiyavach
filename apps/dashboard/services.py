from decimal import Decimal

from django.db.models import Sum

from apps.distribution.models import DistributionLine
from apps.inventory.models import InventoryBalance
from apps.masters.models import Event, Item, Upashray
from apps.requirements.models import RequirementLine
from apps.sponsorship.models import SponsorMaterialReceipt, SponsorshipCommitment


def _sum_by_item(queryset, item_field: str, value_field: str):
    totals = {}
    for row in queryset.values(item_field).annotate(total=Sum(value_field)):
        totals[row[item_field]] = row["total"] or Decimal("0")
    return totals


def get_dashboard_event_queryset():
    return Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name")


def build_item_control_center(event, category=None, pending_only=False, fully_covered=False, shortage=False):
    items = Item.objects.filter(event=event, is_active=True).order_by("category", "item_name")
    if category:
        items = items.filter(category=category)

    required_map = _sum_by_item(
        RequirementLine.objects.filter(event=event),
        "item_id",
        "required_qty",
    )
    committed_map = _sum_by_item(
        SponsorshipCommitment.objects.filter(event=event),
        "item_id",
        "committed_qty",
    )
    received_map = _sum_by_item(
        SponsorMaterialReceipt.objects.filter(event=event),
        "item_id",
        "received_qty",
    )
    stock_map = _sum_by_item(
        InventoryBalance.objects.filter(event=event),
        "item_id",
        "current_stock",
    )
    distributed_map = _sum_by_item(
        DistributionLine.objects.filter(event=event),
        "item_id",
        "delivered_qty",
    )

    rows = []
    for item in items:
        required = required_map.get(item.id, Decimal("0"))
        sponsored = committed_map.get(item.id, Decimal("0"))
        received = received_map.get(item.id, Decimal("0"))
        stock = stock_map.get(item.id, Decimal("0"))
        distributed = distributed_map.get(item.id, Decimal("0"))
        purchase_needed = max(required - received - stock, Decimal("0"))
        balance = max(required - received - stock - distributed, Decimal("0"))

        row = {
            "item": item,
            "required": required,
            "sponsored": sponsored,
            "received": received,
            "purchase_needed": purchase_needed,
            "stock": stock,
            "distributed": distributed,
            "balance": balance,
        }
        if pending_only and balance <= 0:
            continue
        if fully_covered and balance > 0:
            continue
        if shortage and purchase_needed <= 0:
            continue
        rows.append(row)

    summary = {
        "required_total": sum((row["required"] for row in rows), Decimal("0")),
        "sponsored_total": sum((row["sponsored"] for row in rows), Decimal("0")),
        "received_total": sum((row["received"] for row in rows), Decimal("0")),
        "purchase_needed_total": sum((row["purchase_needed"] for row in rows), Decimal("0")),
        "stock_total": sum((row["stock"] for row in rows), Decimal("0")),
        "distributed_total": sum((row["distributed"] for row in rows), Decimal("0")),
        "balance_total": sum((row["balance"] for row in rows), Decimal("0")),
        "pending_items": sum(1 for row in rows if row["balance"] > 0),
    }
    return rows, summary


def build_home_summary(event):
    requirement_total = RequirementLine.objects.filter(event=event).aggregate(total=Sum("required_qty"))["total"] or Decimal("0")
    sponsorship_total = SponsorshipCommitment.objects.filter(event=event).aggregate(total=Sum("committed_qty"))["total"] or Decimal("0")
    received_total = SponsorMaterialReceipt.objects.filter(event=event).aggregate(total=Sum("received_qty"))["total"] or Decimal("0")
    stock_total = InventoryBalance.objects.filter(event=event).aggregate(total=Sum("current_stock"))["total"] or Decimal("0")
    distributed_total = DistributionLine.objects.filter(event=event).aggregate(total=Sum("delivered_qty"))["total"] or Decimal("0")
    pending_procurement = max(requirement_total - received_total - stock_total, Decimal("0"))
    pending_distribution = max(requirement_total - distributed_total, Decimal("0"))
    return {
        "total_upashray": Upashray.objects.filter(event=event).count(),
        "requirement_total": requirement_total,
        "sponsorship_total": sponsorship_total,
        "stock_total": stock_total,
        "pending_procurement": pending_procurement,
        "pending_distribution": pending_distribution,
        "pending_alerts": int((pending_procurement > 0) + (pending_distribution > 0)),
    }
