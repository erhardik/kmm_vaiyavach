from django.contrib import admin
from .models import InventoryBalance, InventoryTransaction, PurchaseLot

admin.site.register(InventoryTransaction)
admin.site.register(InventoryBalance)
admin.site.register(PurchaseLot)
