from django.urls import path

from apps.inventory.views import (
    InventoryBalanceListView,
    InventoryTransactionCreateView,
    InventoryTransactionDeleteAllView,
    InventoryTransactionDeleteView,
    InventoryTransactionListView,
    InventoryTransactionUpdateView,
    PurchaseEntryView,
)

app_name = "inventory"

urlpatterns = [
    path("transactions/", InventoryTransactionListView.as_view(), name="transaction-list"),
    path("transactions/add/", InventoryTransactionCreateView.as_view(), name="transaction-create"),
    path("transactions/<int:pk>/edit/", InventoryTransactionUpdateView.as_view(), name="transaction-update"),
    path("transactions/<int:pk>/delete/", InventoryTransactionDeleteView.as_view(), name="transaction-delete"),
    path("transactions/delete-all/", InventoryTransactionDeleteAllView.as_view(), name="transaction-delete-all"),
    path("balances/", InventoryBalanceListView.as_view(), name="balance-list"),
    path("purchase-entry/", PurchaseEntryView.as_view(), name="purchase-entry"),
]

