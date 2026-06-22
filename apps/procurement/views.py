from django.urls import reverse_lazy

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.procurement.forms import GoodsReceiptForm, PurchaseOrderForm, PurchaseOrderLineForm
from apps.procurement.models import GoodsReceipt, PurchaseOrder, PurchaseOrderLine
from apps.procurement.services import sync_goods_receipt


class PurchaseOrderListView(EventScopedListView):
    model = PurchaseOrder
    template_name = "common/list.html"
    row_fields = ("po_number", "vendor", "date", "get_status_display", "remarks")
    headers = ["PO Number", "Vendor", "Date", "Status", "Remarks"]
    search_fields = ["po_number", "vendor__vendor_name", "remarks"]
    create_url_name = "procurement:po-create"
    edit_url_name = "procurement:po-update"
    delete_url_name = "procurement:po-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Purchase Orders"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class PurchaseOrderCreateView(EventScopedCreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "common/form.html"
    success_url = reverse_lazy("procurement:po-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Purchase Order"
        context["list_url"] = self.success_url
        return context


class PurchaseOrderUpdateView(EventScopedUpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = "common/form.html"
    success_url = reverse_lazy("procurement:po-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Purchase Order"
        context["list_url"] = self.success_url
        return context


class PurchaseOrderDeleteView(EventScopedDeleteView):
    model = PurchaseOrder
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("procurement:po-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class PurchaseOrderLineListView(EventScopedListView):
    model = PurchaseOrderLine
    template_name = "common/list.html"
    row_fields = ("purchase_order", "item", "qty", "rate", "tax_amount", "line_total")
    headers = ["Purchase Order", "Item", "Qty", "Rate", "Tax", "Total"]
    search_fields = ["purchase_order__po_number", "item__item_name"]
    create_url_name = "procurement:line-create"
    edit_url_name = "procurement:line-update"
    delete_url_name = "procurement:line-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Purchase Order Lines"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class PurchaseOrderLineCreateView(EventScopedCreateView):
    model = PurchaseOrderLine
    form_class = PurchaseOrderLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("procurement:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Purchase Order Line"
        context["list_url"] = self.success_url
        return context


class PurchaseOrderLineUpdateView(EventScopedUpdateView):
    model = PurchaseOrderLine
    form_class = PurchaseOrderLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("procurement:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Purchase Order Line"
        context["list_url"] = self.success_url
        return context


class PurchaseOrderLineDeleteView(EventScopedDeleteView):
    model = PurchaseOrderLine
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("procurement:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class GoodsReceiptListView(EventScopedListView):
    model = GoodsReceipt
    template_name = "common/list.html"
    row_fields = ("purchase_order", "date", "received_by", "remarks")
    headers = ["Purchase Order", "Date", "Received By", "Remarks"]
    search_fields = ["purchase_order__po_number", "remarks"]
    create_url_name = "procurement:grn-create"
    edit_url_name = "procurement:grn-update"
    delete_url_name = "procurement:grn-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Goods Receipts"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class GoodsReceiptCreateView(EventScopedCreateView):
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = "common/form.html"
    success_url = reverse_lazy("procurement:grn-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Goods Receipt"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        sync_goods_receipt(self.object, user=self.request.user)
        return response


class GoodsReceiptUpdateView(EventScopedUpdateView):
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = "common/form.html"
    success_url = reverse_lazy("procurement:grn-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Goods Receipt"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        sync_goods_receipt(self.object, user=self.request.user)
        return response


class GoodsReceiptDeleteView(EventScopedDeleteView):
    model = GoodsReceipt
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("procurement:grn-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context
