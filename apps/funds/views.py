from django.urls import reverse_lazy

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.funds.forms import DonationForm, FundTransactionForm
from apps.funds.models import Donation, FundTransaction


class DonationListView(EventScopedListView):
    model = Donation
    template_name = "common/list.html"
    row_fields = ("donor_name", "mobile", "amount", "mode", "received_date", "reference_person")
    headers = ["Donor", "Mobile", "Amount", "Mode", "Date", "Reference"]
    search_fields = ["donor_name", "mobile", "reference_person", "remarks"]
    create_url_name = "funds:donation-create"
    edit_url_name = "funds:donation-update"
    delete_url_name = "funds:donation-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Donations"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class DonationCreateView(EventScopedCreateView):
    model = Donation
    form_class = DonationForm
    template_name = "common/form.html"
    success_url = reverse_lazy("funds:donation-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Donation"
        context["list_url"] = self.success_url
        return context


class DonationUpdateView(EventScopedUpdateView):
    model = Donation
    form_class = DonationForm
    template_name = "common/form.html"
    success_url = reverse_lazy("funds:donation-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Donation"
        context["list_url"] = self.success_url
        return context


class DonationDeleteView(EventScopedDeleteView):
    model = Donation
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("funds:donation-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class FundTransactionListView(EventScopedListView):
    model = FundTransaction
    template_name = "common/list.html"
    row_fields = ("transaction_type", "category", "amount", "date", "reference_module", "reference_id")
    headers = ["Type", "Category", "Amount", "Date", "Ref Module", "Ref ID"]
    search_fields = ["category", "reference_module", "reference_id", "remarks"]
    create_url_name = "funds:transaction-create"
    edit_url_name = "funds:transaction-update"
    delete_url_name = "funds:transaction-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Fund Transactions"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class FundTransactionCreateView(EventScopedCreateView):
    model = FundTransaction
    form_class = FundTransactionForm
    template_name = "common/form.html"
    success_url = reverse_lazy("funds:transaction-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Fund Transaction"
        context["list_url"] = self.success_url
        return context


class FundTransactionUpdateView(EventScopedUpdateView):
    model = FundTransaction
    form_class = FundTransactionForm
    template_name = "common/form.html"
    success_url = reverse_lazy("funds:transaction-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Fund Transaction"
        context["list_url"] = self.success_url
        return context


class FundTransactionDeleteView(EventScopedDeleteView):
    model = FundTransaction
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("funds:transaction-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context

