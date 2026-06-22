from django.urls import reverse_lazy
from django.views.generic import ListView

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.inventory.forms import InventoryBalanceForm, InventoryTransactionForm
from apps.inventory.models import InventoryBalance, InventoryTransaction


class InventoryTransactionListView(EventScopedListView):
    model = InventoryTransaction
    template_name = "common/list.html"
    row_fields = ("item", "transaction_type", "qty", "source_module", "reference_id", "created_at")
    headers = ["Item", "Type", "Qty", "Source", "Reference", "Created"]
    search_fields = ["item__item_name", "source_module", "reference_id", "remarks"]
    create_url_name = "inventory:transaction-create"
    edit_url_name = "inventory:transaction-update"
    delete_url_name = "inventory:transaction-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory Transactions"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class InventoryTransactionCreateView(EventScopedCreateView):
    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = "common/form.html"
    success_url = reverse_lazy("inventory:transaction-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Inventory Transaction"
        context["list_url"] = self.success_url
        return context


class InventoryTransactionUpdateView(EventScopedUpdateView):
    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = "common/form.html"
    success_url = reverse_lazy("inventory:transaction-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Inventory Transaction"
        context["list_url"] = self.success_url
        return context


class InventoryTransactionDeleteView(EventScopedDeleteView):
    model = InventoryTransaction
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("inventory:transaction-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class InventoryBalanceListView(EventScopedListView):
    model = InventoryBalance
    template_name = "common/list.html"
    row_fields = ("item", "current_stock", "reserved_stock", "available_stock", "distributed_stock")
    headers = ["Item", "Current", "Reserved", "Available", "Distributed"]
    search_fields = ["item__item_name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Inventory Balances"
        context["page_subtitle"] = "Derived stock summary"
        context["create_url"] = "#"
        return context

