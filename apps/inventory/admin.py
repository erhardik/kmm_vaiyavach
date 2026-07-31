from django.contrib import admin
from .models import InventoryBalance, InventoryTransaction, PurchaseLot, RemainingStock, RemainingExtraItem

admin.site.register(InventoryTransaction)
admin.site.register(InventoryBalance)
admin.site.register(PurchaseLot)
admin.site.register(RemainingStock)
admin.site.register(RemainingExtraItem)
