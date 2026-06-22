from django.contrib import admin
from .models import InventoryBalance, InventoryTransaction

admin.site.register(InventoryTransaction)
admin.site.register(InventoryBalance)
