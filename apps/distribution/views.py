from django.urls import reverse_lazy

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.distribution.forms import DistributionBatchForm, DistributionLineForm
from apps.distribution.models import DistributionBatch, DistributionLine
from apps.distribution.services import sync_distribution_line


class DistributionBatchListView(EventScopedListView):
    model = DistributionBatch
    template_name = "common/list.html"
    row_fields = ("batch_name", "date", "assigned_volunteer", "get_status_display", "remarks")
    headers = ["Batch", "Date", "Volunteer", "Status", "Remarks"]
    search_fields = ["batch_name", "assigned_volunteer__name", "remarks"]
    create_url_name = "distribution:batch-create"
    edit_url_name = "distribution:batch-update"
    delete_url_name = "distribution:batch-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Distribution Batches"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class DistributionBatchCreateView(EventScopedCreateView):
    model = DistributionBatch
    form_class = DistributionBatchForm
    template_name = "common/form.html"
    success_url = reverse_lazy("distribution:batch-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Distribution Batch"
        context["list_url"] = self.success_url
        return context


class DistributionBatchUpdateView(EventScopedUpdateView):
    model = DistributionBatch
    form_class = DistributionBatchForm
    template_name = "common/form.html"
    success_url = reverse_lazy("distribution:batch-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Distribution Batch"
        context["list_url"] = self.success_url
        return context


class DistributionBatchDeleteView(EventScopedDeleteView):
    model = DistributionBatch
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("distribution:batch-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class DistributionLineListView(EventScopedListView):
    model = DistributionLine
    template_name = "common/list.html"
    row_fields = ("distribution_batch", "upashray", "item", "required_qty", "dispatched_qty", "delivered_qty", "balance_qty", "get_status_display")
    headers = ["Batch", "Upashray", "Item", "Required", "Dispatched", "Delivered", "Balance", "Status"]
    search_fields = ["distribution_batch__batch_name", "upashray__name", "item__item_name"]
    create_url_name = "distribution:line-create"
    edit_url_name = "distribution:line-update"
    delete_url_name = "distribution:line-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Distribution Lines"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class DistributionLineCreateView(EventScopedCreateView):
    model = DistributionLine
    form_class = DistributionLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("distribution:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Distribution Line"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        sync_distribution_line(self.object, user=self.request.user)
        return response


class DistributionLineUpdateView(EventScopedUpdateView):
    model = DistributionLine
    form_class = DistributionLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("distribution:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Distribution Line"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        sync_distribution_line(self.object, user=self.request.user)
        return response


class DistributionLineDeleteView(EventScopedDeleteView):
    model = DistributionLine
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("distribution:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context
