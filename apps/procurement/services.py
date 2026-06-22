from decimal import Decimal

from django.db import transaction

from apps.inventory.models import InventoryTransactionType
from apps.inventory.services import create_inventory_transaction
from apps.procurement.models import GoodsReceipt, PurchaseOrder


@transaction.atomic
def sync_goods_receipt(goods_receipt: GoodsReceipt, user=None):
    purchase_order = goods_receipt.purchase_order
    created_transactions = []
    for line in purchase_order.lines.select_related("item").all():
        tx = line.inventory_transaction
        if tx is None:
            tx = create_inventory_transaction(
                event=purchase_order.event,
                item=line.item,
                transaction_type=InventoryTransactionType.PURCHASE,
                qty=line.qty or Decimal("0"),
                source_module="procurement",
                reference_id=purchase_order.po_number,
                reference_label=f"PO {purchase_order.po_number}",
                unit_rate=line.rate,
                remarks=goods_receipt.remarks,
                created_by=user,
            )
            line.inventory_transaction = tx
            line.save(update_fields=["inventory_transaction", "updated_at"])
        else:
            tx.qty = line.qty or Decimal("0")
            tx.remarks = goods_receipt.remarks
            tx.unit_rate = line.rate
            tx.updated_by = user
            tx.save()
        created_transactions.append(tx)
    purchase_order.status = "RECEIVED"
    purchase_order.save(update_fields=["status", "updated_at"])
    return created_transactions

