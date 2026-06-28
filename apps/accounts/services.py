import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.masters.models import Event, Item, Sponsor, Upashray, Vendor, Volunteer
from apps.requirements.models import RequirementHeader, RequirementLine, SpecialRequirement
from apps.sponsorship.models import SponsorMaterialReceipt, SponsorshipCommitment
from apps.vendors.models import VendorQuote
from apps.procurement.models import GoodsReceipt, PurchaseOrder, PurchaseOrderLine
from apps.inventory.models import InventoryBalance, InventoryTransaction
from apps.distribution.models import DistributionBatch, DistributionLine
from apps.funds.models import Donation, FundTransaction
from apps.auditlog.models import ActivityLog
from apps.accounts.models import EventMembership, UserProfile


ROLE_GROUPS = {
    "admin": "KMM Admin",
    "viewer": "KMM Viewer",
    "manager": "KMM Manager",
}

MODEL_CLASSES = [
    Event,
    Item,
    Upashray,
    Volunteer,
    Sponsor,
    Vendor,
    RequirementHeader,
    RequirementLine,
    SpecialRequirement,
    SponsorshipCommitment,
    SponsorMaterialReceipt,
    VendorQuote,
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceipt,
    InventoryTransaction,
    InventoryBalance,
    DistributionBatch,
    DistributionLine,
    Donation,
    FundTransaction,
    ActivityLog,
    UserProfile,
    EventMembership,
]

FINANCIAL_MODEL_CLASSES = [
    Donation,
    FundTransaction,
    VendorQuote,
    PurchaseOrder,
    PurchaseOrderLine,
]


def _all_permissions_for_model(model_cls):
    content_type = ContentType.objects.get_for_model(model_cls)
    return Permission.objects.filter(content_type=content_type)


def ensure_role_groups():
    admin_group, _ = Group.objects.get_or_create(name=ROLE_GROUPS["admin"])
    viewer_group, _ = Group.objects.get_or_create(name=ROLE_GROUPS["viewer"])
    manager_group, _ = Group.objects.get_or_create(name=ROLE_GROUPS["manager"])

    admin_permissions = Permission.objects.none()
    viewer_permissions = Permission.objects.none()
    manager_permissions = Permission.objects.none()

    financial_model_classes = FINANCIAL_MODEL_CLASSES

    for model_cls in MODEL_CLASSES:
        permissions = _all_permissions_for_model(model_cls)
        admin_permissions = admin_permissions | permissions
        viewer_permissions = viewer_permissions | permissions.filter(codename__startswith="view_")
        if model_cls not in financial_model_classes:
            manager_permissions = manager_permissions | permissions

    admin_group.permissions.set(admin_permissions.distinct())
    viewer_group.permissions.set(viewer_permissions.distinct())
    manager_group.permissions.set(manager_permissions.distinct())

    return admin_group, viewer_group, manager_group


def bootstrap_default_users(passwords=None, reset_passwords=False):
    User = get_user_model()
    passwords = passwords or {}
    admin_group, viewer_group, manager_group = ensure_role_groups()

    user_specs = [
        {
            "username": "systemadmin",
            "email": "systemadmin@example.com",
            "is_superuser": True,
            "is_staff": True,
            "groups": [],
        },
        {
            "username": "admin",
            "email": "admin@example.com",
            "is_superuser": False,
            "is_staff": False,
            "groups": [admin_group],
        },
        {
            "username": "viewer",
            "email": "viewer@example.com",
            "is_superuser": False,
            "is_staff": False,
            "groups": [viewer_group],
        },
        {
            "username": "manager",
            "email": "manager@example.com",
            "is_superuser": False,
            "is_staff": False,
            "groups": [manager_group],
        },
    ]

    created = []
    for spec in user_specs:
        password = passwords.get(spec["username"])
        user, created_flag = User.objects.get_or_create(
            username=spec["username"],
            defaults={
                "email": spec["email"],
                "is_superuser": spec["is_superuser"],
                "is_staff": spec["is_staff"],
            },
        )
        changed = created_flag
        if not created_flag:
            user.email = spec["email"]
            user.is_superuser = spec["is_superuser"]
            user.is_staff = spec["is_staff"]
            changed = True
        if password:
            user.set_password(password)
            changed = True
        elif (created_flag or reset_passwords) and not user.has_usable_password():
            password = secrets.token_urlsafe(10)
            user.set_password(password)
            changed = True
        if changed:
            user.save()
        if spec["groups"]:
            user.groups.set(spec["groups"])
        else:
            user.groups.clear()
        created.append(
            {
                "username": user.username,
                "created": created_flag,
                "password": password if password else None,
            }
        )
    return created
