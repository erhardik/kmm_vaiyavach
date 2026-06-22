from django.urls import reverse_lazy

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.sponsorship.forms import SponsorMaterialReceiptForm, SponsorshipCommitmentForm
from apps.sponsorship.models import SponsorMaterialReceipt, SponsorshipCommitment
from apps.sponsorship.services import sync_sponsor_receipt


class SponsorshipCommitmentListView(EventScopedListView):
    model = SponsorshipCommitment
    template_name = "common/list.html"
    row_fields = ("sponsor", "item", "committed_qty", "received_qty", "expected_date", "get_status_display")
    headers = ["Sponsor", "Item", "Committed", "Received", "Expected", "Status"]
    search_fields = ["sponsor__sponsor_name", "item__item_name", "remarks"]
    create_url_name = "sponsorship:commitment-create"
    edit_url_name = "sponsorship:commitment-update"
    delete_url_name = "sponsorship:commitment-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sponsorship Commitments"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class SponsorshipCommitmentCreateView(EventScopedCreateView):
    model = SponsorshipCommitment
    form_class = SponsorshipCommitmentForm
    template_name = "common/form.html"
    success_url = reverse_lazy("sponsorship:commitment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Sponsorship Commitment"
        context["list_url"] = self.success_url
        return context


class SponsorshipCommitmentUpdateView(EventScopedUpdateView):
    model = SponsorshipCommitment
    form_class = SponsorshipCommitmentForm
    template_name = "common/form.html"
    success_url = reverse_lazy("sponsorship:commitment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Sponsorship Commitment"
        context["list_url"] = self.success_url
        return context


class SponsorshipCommitmentDeleteView(EventScopedDeleteView):
    model = SponsorshipCommitment
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("sponsorship:commitment-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class SponsorMaterialReceiptListView(EventScopedListView):
    model = SponsorMaterialReceipt
    template_name = "common/list.html"
    row_fields = ("commitment", "item", "received_qty", "received_date", "received_by")
    headers = ["Commitment", "Item", "Received Qty", "Date", "Received By"]
    search_fields = ["commitment__sponsor__sponsor_name", "item__item_name", "remarks"]
    create_url_name = "sponsorship:receipt-create"
    edit_url_name = "sponsorship:receipt-update"
    delete_url_name = "sponsorship:receipt-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sponsor Material Receipts"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class SponsorMaterialReceiptCreateView(EventScopedCreateView):
    model = SponsorMaterialReceipt
    form_class = SponsorMaterialReceiptForm
    template_name = "common/form.html"
    success_url = reverse_lazy("sponsorship:receipt-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Sponsor Material Receipt"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        sync_sponsor_receipt(self.object, user=self.request.user)
        return response


class SponsorMaterialReceiptUpdateView(EventScopedUpdateView):
    model = SponsorMaterialReceipt
    form_class = SponsorMaterialReceiptForm
    template_name = "common/form.html"
    success_url = reverse_lazy("sponsorship:receipt-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Sponsor Material Receipt"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        sync_sponsor_receipt(self.object, user=self.request.user)
        return response


class SponsorMaterialReceiptDeleteView(EventScopedDeleteView):
    model = SponsorMaterialReceipt
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("sponsorship:receipt-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context
