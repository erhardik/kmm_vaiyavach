from decimal import Decimal

from django.db import transaction

from apps.inventory.models import InventoryTransactionType
from apps.inventory.services import create_inventory_transaction
from apps.sponsorship.models import SponsorMaterialReceipt


@transaction.atomic
def sync_sponsor_receipt(receipt: SponsorMaterialReceipt, user=None):
    tx = receipt.inventory_transaction
    if tx is None:
        tx = create_inventory_transaction(
            event=receipt.event,
            item=receipt.item,
            transaction_type=InventoryTransactionType.SPONSORSHIP_RECEIPT,
            qty=receipt.received_qty or Decimal("0"),
            source_module="sponsorship",
            reference_id=str(receipt.pk),
            reference_label=f"Sponsor receipt #{receipt.pk}",
            remarks=receipt.remarks,
            created_by=user,
        )
        receipt.inventory_transaction = tx
    else:
        tx.qty = receipt.received_qty or Decimal("0")
        tx.remarks = receipt.remarks
        tx.updated_by = user
        tx.save()
    commitment = receipt.commitment
    commitment.received_qty = (commitment.received_qty or Decimal("0")) + (receipt.received_qty or Decimal("0"))
    if commitment.received_qty >= commitment.committed_qty:
        commitment.status = "COMPLETED"
    elif commitment.received_qty > 0:
        commitment.status = "PARTIALLY_RECEIVED"
    commitment.save(update_fields=["received_qty", "status", "updated_at"])
    receipt.save(update_fields=["inventory_transaction", "updated_at"])
    return tx

