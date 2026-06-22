from django.urls import reverse

from apps.masters.models import Event


EVENT_MENU_ITEMS = [
    {"label": "Collect Requirements", "url_name": "requirements:collect", "permission": None, "icon": "clipboard-check"},
    {"label": "Requirement Orders", "url_name": "requirements:header-list", "permission": "requirements.view_requirementheader", "icon": "list-check"},
    {"label": "Item Master", "url_name": "dashboard:item_control_center", "permission": None, "icon": "boxes"},
    {"label": "Sponsorship", "url_name": "sponsorship:commitment-list", "permission": "sponsorship.view_sponsorshipcommitment", "icon": "heart"},
    {"label": "Vendors", "url_name": "vendors:quote-list", "permission": "vendors.view_vendorquote", "icon": "truck"},
    {"label": "Procurement", "url_name": "procurement:po-list", "permission": "procurement.view_purchaseorder", "icon": "cart"},
    {"label": "Inventory", "url_name": "inventory:transaction-list", "permission": "inventory.view_inventorytransaction", "icon": "archive"},
    {"label": "Distribution", "url_name": "distribution:batch-list", "permission": "distribution.view_distributionbatch", "icon": "arrow-left-right"},
    {"label": "Funds", "url_name": "funds:donation-list", "permission": "funds.view_donation", "icon": "wallet2"},
    {"label": "Reports", "url_name": "reports:report-home", "permission": None, "icon": "graph-up"},
    {"label": "Analytics", "url_name": "reports:analytics", "permission": None, "icon": "bar-chart"},
    {"label": "Activity Log", "url_name": "auditlog:activity-list", "permission": "auditlog.view_activitylog", "icon": "journal-text"},
]

UTILITY_LINKS = [
    {"label": "Dashboard", "url_name": "dashboard:home", "permission": None, "icon": "house"},
    {"label": "Events", "url_name": "masters:event-list", "permission": "masters.view_event", "icon": "calendar-event"},
]


def _visible_links(request, links, event=None):
    visible = []
    for item in links:
        if item["permission"] is not None and not request.user.has_perm(item["permission"]):
            continue
        url = reverse(item["url_name"])
        if event is not None and item["url_name"] not in {"dashboard:home", "masters:event-list"}:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}event={event.pk}"
        visible.append({**item, "url": url})
    return visible


def portal_navigation(request):
    visible_items = _visible_links(request, UTILITY_LINKS)
    active_events = Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name")
    selected_event_id = request.GET.get("event")
    selected_event = active_events.filter(pk=selected_event_id).first() if selected_event_id else active_events.filter(is_current=True).first()
    sidebar_events = []
    for event in active_events:
        sidebar_events.append(
            {
                "event": event,
                "is_selected": selected_event.pk == event.pk if selected_event else event.is_current,
                "menu_items": _visible_links(request, EVENT_MENU_ITEMS, event=event),
            }
        )
    if request.user.is_authenticated:
        if request.user.is_superuser:
            role_label = "systemadmin"
        elif request.user.groups.filter(name="KMM Admin").exists():
            role_label = "admin"
        elif request.user.groups.filter(name="KMM Viewer").exists():
            role_label = "viewer"
        else:
            role_label = "user"
    else:
        role_label = "guest"
    return {
        "portal_nav_items": visible_items,
        "sidebar_events": sidebar_events,
        "sidebar_selected_event": selected_event,
        "sidebar_headline": "Chaturmas Vaiyavach",
        "current_role_label": role_label,
    }
