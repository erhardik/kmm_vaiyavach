from django.urls import reverse_lazy

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.requirements.forms import RequirementHeaderForm, RequirementLineForm, SpecialRequirementForm
from apps.requirements.models import RequirementHeader, RequirementLine, SpecialRequirement


class RequirementHeaderListView(EventScopedListView):
    model = RequirementHeader
    template_name = "common/list.html"
    row_fields = ("upashray", "requirement_date", "get_status_display", "remarks")
    headers = ["Upashray", "Date", "Status", "Remarks"]
    search_fields = ["upashray__name", "remarks"]
    create_url_name = "requirements:header-create"
    edit_url_name = "requirements:header-update"
    delete_url_name = "requirements:header-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Requirements"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class RequirementHeaderCreateView(EventScopedCreateView):
    model = RequirementHeader
    form_class = RequirementHeaderForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:header-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Requirement"
        context["list_url"] = self.success_url
        return context


class RequirementHeaderUpdateView(EventScopedUpdateView):
    model = RequirementHeader
    form_class = RequirementHeaderForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:header-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Requirement"
        context["list_url"] = self.success_url
        return context


class RequirementHeaderDeleteView(EventScopedDeleteView):
    model = RequirementHeader
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("requirements:header-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class RequirementLineListView(EventScopedListView):
    model = RequirementLine
    template_name = "common/list.html"
    row_fields = ("requirement", "item", "required_qty", "remarks")
    headers = ["Requirement", "Item", "Required Qty", "Remarks"]
    search_fields = ["requirement__upashray__name", "item__item_name", "remarks"]
    create_url_name = "requirements:line-create"
    edit_url_name = "requirements:line-update"
    delete_url_name = "requirements:line-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Requirement Lines"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class RequirementLineCreateView(EventScopedCreateView):
    model = RequirementLine
    form_class = RequirementLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Requirement Line"
        context["list_url"] = self.success_url
        return context


class RequirementLineUpdateView(EventScopedUpdateView):
    model = RequirementLine
    form_class = RequirementLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Requirement Line"
        context["list_url"] = self.success_url
        return context


class RequirementLineDeleteView(EventScopedDeleteView):
    model = RequirementLine
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("requirements:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class SpecialRequirementListView(EventScopedListView):
    model = SpecialRequirement
    template_name = "common/list.html"
    row_fields = ("upashray", "get_priority_display", "get_status_display", "description")
    headers = ["Upashray", "Priority", "Status", "Description"]
    search_fields = ["upashray__name", "description"]
    create_url_name = "requirements:special-create"
    edit_url_name = "requirements:special-update"
    delete_url_name = "requirements:special-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Special Requirements"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class SpecialRequirementCreateView(EventScopedCreateView):
    model = SpecialRequirement
    form_class = SpecialRequirementForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:special-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Special Requirement"
        context["list_url"] = self.success_url
        return context


class SpecialRequirementUpdateView(EventScopedUpdateView):
    model = SpecialRequirement
    form_class = SpecialRequirementForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:special-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Special Requirement"
        context["list_url"] = self.success_url
        return context


class SpecialRequirementDeleteView(EventScopedDeleteView):
    model = SpecialRequirement
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("requirements:special-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context
