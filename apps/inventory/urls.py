from django.urls import path

from apps.inventory.views import (
    InventoryBalanceListView,
    InventoryTransactionCreateView,
    InventoryTransactionDeleteAllView,
    InventoryTransactionDeleteView,
    InventoryTransactionListView,
    InventoryTransactionUpdateView,
    PurchaseEntryView,
    PurchaseHistoryView,
    RemainingExtraItemDeleteView,
    RemainingExtraItemView,
    RemainingStockCarryForwardView,
    RemainingStockDeleteView,
    RemainingStockExportView,
    RemainingStockListView,
    RemainingStockRegisterView,
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
    path("purchase-history/", PurchaseHistoryView.as_view(), name="purchase-history"),
    path("remaining-stock/", RemainingStockListView.as_view(), name="remaining-stock-list"),
    path("remaining-stock/export/", RemainingStockExportView.as_view(), name="remaining-stock-export"),
    path("remaining-stock/register/", RemainingStockRegisterView.as_view(), name="remaining-stock-register"),
    path("remaining-stock/extra/", RemainingExtraItemView.as_view(), name="remaining-stock-extra"),
    path("remaining-stock/extra/<int:pk>/delete/", RemainingExtraItemDeleteView.as_view(), name="remaining-stock-extra-delete"),
    path("remaining-stock/<int:pk>/carry-forward/", RemainingStockCarryForwardView.as_view(), name="remaining-stock-carry-forward"),
    path("remaining-stock/<int:pk>/delete/", RemainingStockDeleteView.as_view(), name="remaining-stock-delete"),
]

