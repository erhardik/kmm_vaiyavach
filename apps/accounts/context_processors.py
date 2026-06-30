from decimal import Decimal

from django.db.models import Sum
from django.urls import reverse

from apps.distribution.models import DistributionBatch
from apps.funds.models import Donation, FundTransaction, FundTransactionType
from apps.inventory.models import InventoryBalance
from apps.masters.models import Event, Item, Vendor
from apps.procurement.models import PurchaseOrder
from apps.requirements.models import EditRequest, RequirementHeader
from apps.sponsorship.models import SponsorshipCommitment


MANAGER_GROUP_NAME = "KMM Manager"

EVENT_MENU_ITEMS = [
    {"label": "Collect Requirements", "url_name": "requirements:collect", "permission": None, "icon": "clipboard-check"},
    {"label": "Requirement Orders", "url_name": "requirements:header-list", "permission": "requirements.view_requirementheader", "icon": "list-check"},
    {"label": "Edit Requests", "url_name": "requirements:edit-request-list", "permission": None, "icon": "pencil-square"},
    {"label": "Item Master", "url_name": "dashboard:item_control_center", "permission": None, "icon": "boxes", "manager_exclude": True},
    {"label": "Items", "url_name": "masters:item-list", "permission": "masters.view_item", "icon": "boxes", "manager_only": True},
    {"label": "Sponsorship", "url_name": "sponsorship:commitment-list", "permission": "sponsorship.view_sponsorshipcommitment", "icon": "heart"},
    {"label": "Vendors", "url_name": "vendors:quote-list", "permission": "vendors.view_vendorquote", "icon": "truck"},
    {"label": "Procurement", "url_name": "procurement:po-list", "permission": "procurement.view_purchaseorder", "icon": "cart"},
    {"label": "Inventory", "url_name": "inventory:transaction-list", "permission": "inventory.view_inventorytransaction", "icon": "archive"},
    {"label": "Purchase Entry", "url_name": "inventory:purchase-entry", "permission": "inventory.add_inventorytransaction", "icon": "cart-plus"},
    {"label": "Distribution", "url_name": "distribution:batch-list", "permission": "distribution.view_distributionbatch", "icon": "arrow-left-right"},
    {"label": "Funds", "url_name": "funds:donation-list", "permission": "funds.view_donation", "icon": "wallet2"},
    {"label": "Reports", "url_name": "reports:report-home", "permission": None, "icon": "graph-up", "manager_exclude": True},
    {"label": "Analytics", "url_name": "reports:analytics", "permission": None, "icon": "bar-chart", "manager_exclude": True},
    {"label": "Activity Log", "url_name": "auditlog:activity-list", "permission": "auditlog.view_activitylog", "icon": "journal-text"},
]

UTILITY_LINKS = [
    {"label": "Dashboard", "url_name": "dashboard:home", "permission": None, "icon": "house", "manager_exclude": True},
    {"label": "Events", "url_name": "masters:event-list", "permission": "masters.view_event", "icon": "calendar-event"},
    {"label": "User Management", "url_name": "accounts:user-list", "permission": None, "icon": "people-gear", "superadmin_only": True},
]


def _visible_links(request, links, event=None):
    visible = []
    is_manager = request.user.is_authenticated and request.user.groups.filter(name=MANAGER_GROUP_NAME).exists()
    for item in links:
        if item.get("superadmin_only") and not request.user.is_authenticated:
            continue
        if item.get("superadmin_only") and not request.user.is_superuser:
            continue
        if item["permission"] is not None and not request.user.has_perm(item["permission"]):
            continue
        if item.get("manager_exclude") and is_manager:
            continue
        if item.get("manager_only") and not is_manager:
            continue
        url = reverse(item["url_name"])
        if event is not None and item["url_name"] not in {"dashboard:home", "masters:event-list"}:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}event={event.pk}"
        visible.append({**item, "url": url})
    return visible


def _sum_amount(queryset, field_name="amount"):
    value = queryset.aggregate(total=Sum(field_name))["total"]
    return value or Decimal("0")


def _format_metric(value, prefix=""):
    if value is None:
        value = Decimal("0")
    try:
        amount = Decimal(value)
    except Exception:
        return f"{prefix}{value}"
    if amount == amount.to_integral():
        return f"{prefix}{int(amount):,}"
    return f"{prefix}{amount:,.2f}"


def _event_metrics(event):
    if event is None:
        return {}
    donation_total = _sum_amount(Donation.objects.filter(event=event))
    fund_income = _sum_amount(FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.INCOME))
    fund_expense = _sum_amount(FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.EXPENSE))
    fund_transfer = _sum_amount(FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.TRANSFER))
    fund_adjustment = _sum_amount(FundTransaction.objects.filter(event=event, transaction_type=FundTransactionType.ADJUSTMENT))
    fund_balance = donation_total + fund_income + fund_transfer + fund_adjustment - fund_expense
    stock_total = _sum_amount(InventoryBalance.objects.filter(event=event), "current_stock")
    return {
        "requirements": RequirementHeader.objects.filter(event=event, is_active=True).count(),
        "edit_requests": EditRequest.objects.filter(event=event, is_resolved=False).count(),
        "items": Item.objects.filter(event=event, is_active=True).count(),
        "sponsorship": SponsorshipCommitment.objects.filter(event=event).count(),
        "vendors": Vendor.objects.filter(event=event, is_active=True).count(),
        "procurement": PurchaseOrder.objects.filter(event=event).count(),
        "distribution": DistributionBatch.objects.filter(event=event).count(),
        "fund_balance": fund_balance,
        "stock_total": stock_total,
    }


def portal_navigation(request):
    visible_items = _visible_links(request, UTILITY_LINKS)
    active_events = Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name")
    selected_event_id = request.GET.get("event")
    selected_event = active_events.filter(pk=selected_event_id).first() if selected_event_id else active_events.filter(is_current=True).first()
    metrics = _event_metrics(selected_event)
    badge_map = {
        "masters:event-list": f"{Event.objects.filter(is_active=True).count()} Events",
        "requirements:collect": f"{metrics.get('requirements', 0)} Orders",
        "requirements:header-list": f"{metrics.get('requirements', 0)} Orders",
        "masters:item-list": f"{metrics.get('items', 0)} Items",
        "dashboard:item_control_center": f"{metrics.get('items', 0)} Items",
        "sponsorship:commitment-list": f"{metrics.get('sponsorship', 0)} Commitments",
        "vendors:quote-list": f"{metrics.get('vendors', 0)} Vendors",
        "procurement:po-list": f"{metrics.get('procurement', 0)} POs",
        "inventory:transaction-list": f"Stock {_format_metric(metrics.get('stock_total', 0))}",
        "inventory:balance-list": f"Stock {_format_metric(metrics.get('stock_total', 0))}",
        "distribution:batch-list": f"{metrics.get('distribution', 0)} Batches",
        "funds:donation-list": f"Rs. {_format_metric(metrics.get('fund_balance', 0))}",
        "funds:transaction-list": f"Rs. {_format_metric(metrics.get('fund_balance', 0))}",
        "reports:analytics": f"Rs. {_format_metric(metrics.get('fund_balance', 0))}",
        "requirements:edit-request-list": f"{metrics.get('edit_requests', 0)} Pending",
    }
    sidebar_events = []
    for event in active_events:
        sidebar_events.append(
            {
                "event": event,
                "is_selected": selected_event.pk == event.pk if selected_event else event.is_current,
                "menu_items": [
                    {**item, "badge": badge_map.get(item["url_name"], "")}
                    for item in _visible_links(request, EVENT_MENU_ITEMS, event=event)
                ],
            }
        )
    if request.user.is_authenticated:
        if request.user.is_superuser:
            role_label = "systemadmin"
        elif request.user.groups.filter(name="KMM Admin").exists():
            role_label = "admin"
        elif request.user.groups.filter(name=MANAGER_GROUP_NAME).exists():
            role_label = "manager"
        elif request.user.groups.filter(name="KMM Viewer").exists():
            role_label = "viewer"
        else:
            role_label = "user"
    else:
        role_label = "guest"
    resolver_match = getattr(request, "resolver_match", None)
    current_view_name = getattr(resolver_match, "view_name", "") or ""
    current_badge = badge_map.get(current_view_name, "")
    return {
        "portal_nav_items": visible_items,
        "sidebar_events": sidebar_events,
        "sidebar_selected_event": selected_event,
        "sidebar_headline": "Chaturmas Vaiyavachch",
        "current_role_label": role_label,
        "menu_badges": badge_map,
        "page_live_badge": current_badge,
    }
