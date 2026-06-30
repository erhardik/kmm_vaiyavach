from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.inventory.forms import InventoryBalanceForm, InventoryTransactionForm, PurchaseEntryForm, PurchaseLotLineForm
from apps.inventory.models import InventoryBalance, InventoryTransaction, PurchaseLot
from apps.inventory.services import create_inventory_transaction, recalculate_inventory_balance
from apps.masters.models import Event


class InventoryTransactionListView(EventScopedListView):
    model = InventoryTransaction
    template_name = "inventory/transaction_list.html"
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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


class InventoryTransactionDeleteAllView(View):
    def post(self, request):
        if not request.user.is_superuser:
            messages.error(request, "Only superadmin can delete all transactions.")
            return redirect("inventory:transaction-list")
        count = InventoryTransaction.objects.count()
        InventoryTransaction.objects.all().delete()
        messages.success(request, f"Deleted {count} transaction(s). Items and balances unchanged.")
        return redirect("inventory:transaction-list")


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


class PurchaseEntryView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "inventory/purchase_entry.html"
    permission_required = "inventory.add_inventorytransaction"
    raise_exception = True
    LotLineFormset = formset_factory(PurchaseLotLineForm, extra=5, max_num=20, can_delete=True)

    def get_event(self):
        event_id = self.request.GET.get("event") or self.request.POST.get("event")
        if event_id:
            return Event.objects.filter(pk=event_id, is_active=True).first()
        return Event.objects.filter(is_current=True, is_active=True).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_event()
        context["event"] = event
        context["page_title"] = "Purchase Entry"
        context["form"] = kwargs.get("form", PurchaseEntryForm(event=event, user=self.request.user))
        context["lot_formset"] = kwargs.get("lot_formset", self.LotLineFormset(prefix="lots", form_kwargs={"event": event}))
        context["event_queryset"] = Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name")
        return context

    def post(self, request, *args, **kwargs):
        event = self.get_event()
        if event is None:
            messages.error(request, "No active event found.")
            return redirect("inventory:purchase-entry")
        form = PurchaseEntryForm(request.POST, event=event, user=request.user)
        lot_formset = self.LotLineFormset(request.POST, prefix="lots", form_kwargs={"event": event})
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, lot_formset=lot_formset))
        if not lot_formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, lot_formset=lot_formset))
        item = form.cleaned_data["item"]
        total_qty = 0
        lots_created = 0
        with transaction.atomic():
            for lot_form in lot_formset:
                if lot_form.cleaned_data.get("qty", 0) and not lot_form.cleaned_data.get("DELETE", False):
                    qty = lot_form.cleaned_data["qty"]
                    unit_rate = lot_form.cleaned_data.get("unit_rate", 0)
                    vendor = lot_form.cleaned_data.get("vendor")
                    notes = lot_form.cleaned_data.get("notes", "")
                    lot = PurchaseLot.objects.create(
                        event=event,
                        item=item,
                        qty=qty,
                        unit_rate=unit_rate,
                        vendor=vendor,
                        managed_by=request.user if request.user.is_authenticated else None,
                        notes=notes,
                        created_by=request.user if request.user.is_authenticated else None,
                        updated_by=request.user if request.user.is_authenticated else None,
                    )
                    tx = create_inventory_transaction(
                        event=event,
                        item=item,
                        transaction_type="PURCHASE",
                        qty=qty,
                        source_module="purchase_entry",
                        reference_id=str(lot.pk),
                        reference_label=f"Lot #{lot.pk}",
                        unit_rate=unit_rate,
                        remarks=notes,
                        created_by=request.user if request.user.is_authenticated else None,
                    )
                    tx.purchase_lot = lot
                    tx.save(update_fields=["purchase_lot"])
                    total_qty += qty
                    lots_created += 1
        if total_qty > 0:
            recalculate_inventory_balance(event, item)
        messages.success(request, f"Created {lots_created} purchase lot(s) for {item} (total {total_qty})")
        return redirect("inventory:purchase-entry")

