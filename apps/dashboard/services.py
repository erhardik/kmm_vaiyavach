from decimal import Decimal

from django.db.models import Sum

from apps.distribution.models import DistributionLine
from apps.inventory.models import InventoryBalance, InventoryTransaction, InventoryTransactionType
from apps.masters.models import Event, Item, Upashray
from apps.procurement.models import PurchaseOrderLine
from apps.requirements.models import RequirementHeader, RequirementLine, RequirementStatus
from apps.sponsorship.models import SponsorMaterialReceipt, SponsorshipCommitment


def _sum_by_item(queryset, item_field: str, value_field: str):
    totals = {}
    for row in queryset.values(item_field).annotate(total=Sum(value_field)):
        totals[row[item_field]] = row["total"] or Decimal("0")
    return totals


def _first_value_by_item(queryset, item_attr: str, value_getter):
    result = {}
    for obj in queryset:
        item_id = getattr(obj, f"{item_attr}_id")
        if item_id in result:
            continue
        result[item_id] = value_getter(obj)
    return result


def get_dashboard_event_queryset():
    return Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name")


def build_item_control_center(event, category=None, pending_only=False, fully_covered=False, shortage=False):
    items = Item.objects.filter(event=event, is_active=True).order_by("standard_serial", "pk")
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
    donated_map = _sum_by_item(
        InventoryTransaction.objects.filter(event=event, transaction_type=InventoryTransactionType.DONATION),
        "item_id",
        "qty",
    )
    purchase_qty_map = _sum_by_item(
        PurchaseOrderLine.objects.filter(event=event),
        "item_id",
        "qty",
    )
    purchase_cost_map = _sum_by_item(
        PurchaseOrderLine.objects.filter(event=event),
        "item_id",
        "line_total",
    )
    vendor_map = _first_value_by_item(
        PurchaseOrderLine.objects.filter(event=event).select_related("purchase_order__vendor").order_by("item_id", "-purchase_order__date", "-created_at", "-pk"),
        "item",
        lambda row: row.purchase_order.vendor.vendor_name if row.purchase_order and row.purchase_order.vendor else "",
    )
    ref_volunteer_map = _first_value_by_item(
        SponsorshipCommitment.objects.filter(event=event)
        .select_related("sponsor__reference_volunteer")
        .order_by("item_id", "-created_at", "-pk"),
        "item",
        lambda row: row.sponsor.reference_volunteer.name if row.sponsor and row.sponsor.reference_volunteer else "",
    )
    acquired_map = _sum_by_item(
        InventoryTransaction.objects.filter(
            event=event,
            transaction_type__in=[
                InventoryTransactionType.PURCHASE,
                InventoryTransactionType.DONATION,
                InventoryTransactionType.SPONSORSHIP_RECEIPT,
                InventoryTransactionType.RETURN,
                InventoryTransactionType.ADJUSTMENT,
            ],
        ),
        "item_id",
        "qty",
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
        donated = donated_map.get(item.id, Decimal("0"))
        purchased_qty = purchase_qty_map.get(item.id, Decimal("0"))
        acquired = acquired_map.get(item.id, Decimal("0"))
        stock = stock_map.get(item.id, Decimal("0"))
        distributed = distributed_map.get(item.id, Decimal("0"))
        shortage_qty = max(required - acquired, Decimal("0"))
        remaining = stock
        surplus = max(acquired - required, Decimal("0"))
        short = max(required - acquired, Decimal("0"))
        rate = item.estimated_rate or Decimal("0")
        required_cost = required * rate
        actual_purchase_cost = purchase_cost_map.get(item.id, Decimal("0"))
        if donated > 0 and purchased_qty > 0:
            source_type = "Donor + Fund"
        elif donated > 0:
            source_type = "Donor"
        elif purchased_qty > 0:
            source_type = "Fund"
        else:
            source_type = ""

        row = {
            "item": item,
            "serial": item.standard_serial or item.pk,
            "rate": rate,
            "required": required,
            "sponsored": sponsored,
            "received": received,
            "donated": donated,
            "purchased_qty": purchased_qty,
            "acquired": acquired if acquired > 0 else donated + purchased_qty + received,
            "purchase_needed": shortage_qty,
            "stock": stock,
            "remaining": remaining,
            "distributed": distributed,
            "shortage": shortage_qty,
            "surplus": surplus,
            "short": short,
            "final_stock": stock,
            "balance": shortage_qty,
            "required_cost": required_cost,
            "actual_purchase_cost": actual_purchase_cost,
            "source_type": source_type,
            "vendor_name": vendor_map.get(item.id, ""),
            "ref_volunteer_name": ref_volunteer_map.get(item.id, ""),
        }
        if pending_only and shortage_qty <= 0:
            continue
        if fully_covered and shortage_qty > 0:
            continue
        if shortage and shortage_qty <= 0:
            continue
        rows.append(row)

    summary = {
        "required_total": sum((row["required"] for row in rows), Decimal("0")),
        "sponsored_total": sum((row["sponsored"] for row in rows), Decimal("0")),
        "received_total": sum((row["received"] for row in rows), Decimal("0")),
        "acquired_total": sum((row["acquired"] for row in rows), Decimal("0")),
        "purchase_needed_total": sum((row["purchase_needed"] for row in rows), Decimal("0")),
        "stock_total": sum((row["stock"] for row in rows), Decimal("0")),
        "remaining_total": sum((row["remaining"] for row in rows), Decimal("0")),
        "distributed_total": sum((row["distributed"] for row in rows), Decimal("0")),
        "balance_total": sum((row["balance"] for row in rows), Decimal("0")),
        "shortage_total": sum((row["shortage"] for row in rows), Decimal("0")),
        "required_cost_total": sum((row["required_cost"] for row in rows), Decimal("0")),
        "actual_purchase_cost_total": sum((row["actual_purchase_cost"] for row in rows), Decimal("0")),
        "pending_items": sum(1 for row in rows if row["shortage"] > 0),
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


def build_public_status_summary(event):
    statuses = [
        RequirementStatus.DRAFT,
        RequirementStatus.SUBMITTED,
        RequirementStatus.IN_PROGRESS,
        RequirementStatus.CLOSED,
        RequirementStatus.CANCELLED,
        RequirementStatus.RETURN_REQUESTED,
        RequirementStatus.RETURN_DONE,
        RequirementStatus.RECEIVED_BY_MS,
    ]
    qs = RequirementHeader.objects.filter(event=event)
    summary = {
        "total_requests": qs.count(),
    }
    for status in statuses:
        summary[f"status_{status}"] = qs.filter(status=status).count()
    summary["open_requests"] = qs.filter(status__in=[RequirementStatus.DRAFT, RequirementStatus.SUBMITTED]).count()
    summary["packing_requests"] = qs.filter(status=RequirementStatus.IN_PROGRESS).count()
    summary["on_route_requests"] = qs.filter(status=RequirementStatus.CLOSED).count()
    summary["received_requests"] = qs.filter(status=RequirementStatus.RECEIVED_BY_MS).count()
    summary["return_requests"] = qs.filter(status=RequirementStatus.RETURN_REQUESTED).count()
    summary["return_done_requests"] = qs.filter(status=RequirementStatus.RETURN_DONE).count()
    summary["rejected_requests"] = qs.filter(status=RequirementStatus.CANCELLED).count()
    return summary


def build_public_item_preview(event):
    rows = []
    balances = {balance.item_id: balance for balance in InventoryBalance.objects.filter(event=event).select_related("item")}
    items = Item.objects.filter(event=event).order_by("standard_serial", "pk")
    for item in items:
        balance = balances.get(item.pk)
        rows.append(
            {
                "item": item,
                "serial": item.standard_serial or item.pk,
                "stock": balance.current_stock if balance else Decimal("0"),
                "category": item.get_category_display(),
                "is_active": item.is_active,
            }
        )
    return rows
