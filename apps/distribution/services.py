from decimal import Decimal

from django.db import transaction

from apps.distribution.models import DistributionBatch, DistributionLine, DistributionBatchStatus
from apps.inventory.models import InventoryTransactionType
from apps.inventory.services import create_inventory_transaction


@transaction.atomic
def sync_distribution_line(line: DistributionLine, user=None):
    tx = line.inventory_transaction
    qty = line.delivered_qty or Decimal("0")
    if tx is None:
        tx = create_inventory_transaction(
            event=line.event,
            item=line.item,
            transaction_type=InventoryTransactionType.DISTRIBUTION,
            qty=qty,
            source_module="distribution",
            reference_id=f"{line.distribution_batch_id}:{line.pk}",
            reference_label=f"Distribution line #{line.pk}",
            remarks=line.distribution_batch.remarks,
            created_by=user,
        )
        line.inventory_transaction = tx
    else:
        tx.qty = qty
        tx.remarks = line.distribution_batch.remarks
        tx.updated_by = user
        tx.save()
    line.balance_qty = max((line.required_qty or Decimal("0")) - qty, Decimal("0"))
    if qty <= 0:
        line.status = DistributionBatchStatus.PENDING
    elif line.balance_qty > 0:
        line.status = DistributionBatchStatus.PARTIAL
    else:
        line.status = DistributionBatchStatus.DELIVERED
    line.save(update_fields=["inventory_transaction", "balance_qty", "status", "updated_at"])
    batch = line.distribution_batch
    if batch.lines.filter(status=DistributionBatchStatus.PARTIAL).exists():
        batch.status = DistributionBatchStatus.PARTIAL
    elif batch.lines.filter(status=DistributionBatchStatus.DISPATCHED).exists():
        batch.status = DistributionBatchStatus.DISPATCHED
    elif batch.lines.filter(status=DistributionBatchStatus.DELIVERED).exists():
        batch.status = DistributionBatchStatus.DELIVERED
    else:
        batch.status = DistributionBatchStatus.PENDING
    batch.save(update_fields=["status", "updated_at"])
    return tx

