NAV_ITEMS = [
    {"label": "Dashboard", "url_name": "dashboard:home", "permission": None},
    {"label": "Item Control Center", "url_name": "dashboard:item_control_center", "permission": None},
    {"label": "Masters", "url_name": "masters:item-list", "permission": "masters.view_item"},
    {"label": "Requirements", "url_name": "requirements:header-list", "permission": "requirements.view_requirementheader"},
    {"label": "Sponsorship", "url_name": "sponsorship:commitment-list", "permission": "sponsorship.view_sponsorshipcommitment"},
    {"label": "Vendors", "url_name": "vendors:quote-list", "permission": "vendors.view_vendorquote"},
    {"label": "Procurement", "url_name": "procurement:po-list", "permission": "procurement.view_purchaseorder"},
    {"label": "Inventory", "url_name": "inventory:transaction-list", "permission": "inventory.view_inventorytransaction"},
    {"label": "Distribution", "url_name": "distribution:batch-list", "permission": "distribution.view_distributionbatch"},
    {"label": "Funds", "url_name": "funds:donation-list", "permission": "funds.view_donation"},
    {"label": "Reports", "url_name": "reports:report-home", "permission": None},
    {"label": "Analytics", "url_name": "reports:analytics", "permission": None},
    {"label": "Activity Log", "url_name": "auditlog:activity-list", "permission": "auditlog.view_activitylog"},
]


def portal_navigation(request):
    visible_items = []
    for item in NAV_ITEMS:
        if item["permission"] is None or request.user.has_perm(item["permission"]):
            visible_items.append(item)
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
    return {"portal_nav_items": visible_items, "current_role_label": role_label}
