from decimal import Decimal

from django.utils import timezone

from django.db import transaction

from apps.inventory.models import InventoryBalance, InventoryTransaction, InventoryTransactionType
from apps.masters.models import Item


POSITIVE_TYPES = {
    InventoryTransactionType.PURCHASE,
    InventoryTransactionType.DONATION,
    InventoryTransactionType.SPONSORSHIP_RECEIPT,
    InventoryTransactionType.RETURN,
    InventoryTransactionType.ADJUSTMENT,
}

NEGATIVE_TYPES = {
    InventoryTransactionType.DISTRIBUTION,
    InventoryTransactionType.DAMAGE,
    InventoryTransactionType.RESERVATION,
    InventoryTransactionType.RELEASE,
}


def transaction_effect(tx: InventoryTransaction) -> Decimal:
    qty = tx.qty or Decimal("0")
    if tx.transaction_type in POSITIVE_TYPES:
        return qty
    if tx.transaction_type in NEGATIVE_TYPES:
        return -qty
    return Decimal("0")


@transaction.atomic
def recalculate_inventory_balance(event, item):
    qs = InventoryTransaction.objects.filter(event=event, item=item)
    current_stock = Decimal("0")
    reserved_stock = Decimal("0")
    distributed_stock = Decimal("0")

    for tx in qs:
        effect = transaction_effect(tx)
        current_stock += effect
        if tx.transaction_type == InventoryTransactionType.RESERVATION:
            reserved_stock += tx.qty
        if tx.transaction_type == InventoryTransactionType.DISTRIBUTION:
            distributed_stock += tx.qty

    available_stock = current_stock - reserved_stock
    InventoryBalance.objects.update_or_create(
        event=event,
        item=item,
        defaults={
            "current_stock": current_stock,
            "reserved_stock": reserved_stock,
            "available_stock": available_stock,
            "distributed_stock": distributed_stock,
        },
    )


def recalculate_inventory_balances(event, item=None):
    if item is not None:
        recalculate_inventory_balance(event, item)
        return
    items = InventoryTransaction.objects.filter(event=event).values_list("item_id", flat=True).distinct()
    for item_id in items:
        recalculate_inventory_balance(event, Item.objects.get(pk=item_id))


@transaction.atomic
def create_inventory_transaction(*, event, item, transaction_type, qty, source_module="", reference_id="", reference_label="", unit_rate=0, remarks="", created_by=None, reversal_of=None):
    tx = InventoryTransaction.objects.create(
        event=event,
        item=item,
        transaction_type=transaction_type,
        qty=qty,
        source_module=source_module,
        reference_id=reference_id,
        reference_label=reference_label,
        unit_rate=unit_rate,
        remarks=remarks,
        created_by=created_by,
        updated_by=created_by,
        reversal_of=reversal_of,
    )
    recalculate_inventory_balance(event, item)
    return tx


def on_inventory_transaction_changed(instance):
    recalculate_inventory_balance(instance.event, instance.item)


@transaction.atomic
def apply_requirement_packing(requirement, *, created_by=None):
    if getattr(requirement, "packing_stock_applied_at", None):
        return False
    if not getattr(requirement, "order_number", None):
        return False
    lines = list(requirement.lines.select_related("item").order_by("item__standard_serial", "item__pk"))
    for line in lines:
        create_inventory_transaction(
            event=requirement.event,
            item=line.item,
            transaction_type=InventoryTransactionType.DISTRIBUTION,
            qty=line.required_qty,
            source_module="requirements",
            reference_id=requirement.order_number or str(requirement.pk),
            reference_label="Packing",
            remarks=f"Packed against requirement {requirement.order_number or requirement.pk}",
            created_by=created_by,
        )
    requirement.packing_stock_applied_at = timezone.now()
    requirement.save(update_fields=["packing_stock_applied_at", "updated_at"])
    return True
