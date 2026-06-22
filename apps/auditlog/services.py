
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from apps.auditlog.models import ActivityLog


def _normalize_value(value: Any):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "pk") and hasattr(value, "__class__"):
        return str(value)
    return value


def serialize_instance(instance) -> dict:
    data = {}
    for field in instance._meta.fields:
        if field.is_relation:
            data[field.name] = getattr(instance, f"{field.name}_id", None)
            continue
        data[field.name] = _normalize_value(getattr(instance, field.name))
    return data


def log_activity(*, user=None, event=None, action: str, module: str, record_id: str = "", old_value=None, new_value=None, request=None):
    old_value = old_value or {}
    new_value = new_value or {}
    ip_address = None
    user_agent = ""
    if request is not None:
        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")
    ActivityLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        event=event,
        action=action,
        module=module,
        record_id=str(record_id or ""),
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def diff_instance(before: dict, after: dict) -> dict:
    changes = {}
    keys = set(before) | set(after)
    for key in sorted(keys):
        if before.get(key) != after.get(key):
            changes[key] = {"old": before.get(key), "new": after.get(key)}
    return changes
