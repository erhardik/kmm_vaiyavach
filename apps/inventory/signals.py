from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.inventory.models import InventoryTransaction
from apps.inventory.services import on_inventory_transaction_changed


@receiver(post_save, sender=InventoryTransaction)
def inventory_transaction_saved(sender, instance, **kwargs):
    on_inventory_transaction_changed(instance)


@receiver(post_delete, sender=InventoryTransaction)
def inventory_transaction_deleted(sender, instance, **kwargs):
    on_inventory_transaction_changed(instance)

