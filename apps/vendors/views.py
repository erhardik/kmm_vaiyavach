from django.urls import reverse_lazy

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.vendors.forms import VendorQuoteForm
from apps.vendors.models import VendorQuote


class VendorQuoteListView(EventScopedListView):
    model = VendorQuote
    template_name = "common/list.html"
    row_fields = ("vendor", "item", "rate", "quote_date", "home_delivery", "pickup_available", "return_unused")
    headers = ["Vendor", "Item", "Rate", "Date", "Home Delivery", "Pickup", "Return"]
    search_fields = ["vendor__vendor_name", "item__item_name", "remarks"]
    create_url_name = "vendors:quote-create"
    edit_url_name = "vendors:quote-update"
    delete_url_name = "vendors:quote-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Vendor Quotes"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class VendorQuoteCreateView(EventScopedCreateView):
    model = VendorQuote
    form_class = VendorQuoteForm
    template_name = "common/form.html"
    success_url = reverse_lazy("vendors:quote-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Vendor Quote"
        context["list_url"] = self.success_url
        return context


class VendorQuoteUpdateView(EventScopedUpdateView):
    model = VendorQuote
    form_class = VendorQuoteForm
    template_name = "common/form.html"
    success_url = reverse_lazy("vendors:quote-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Vendor Quote"
        context["list_url"] = self.success_url
        return context


class VendorQuoteDeleteView(EventScopedDeleteView):
    model = VendorQuote
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("vendors:quote-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context

