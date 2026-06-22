from django.urls import reverse_lazy

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView, UpdateView

from apps.auditlog.services import log_activity, serialize_instance
from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.masters.forms import EventForm, ItemForm, SponsorForm, UpashrayForm, VendorForm, VolunteerForm
from apps.masters.models import Event, Item, Sponsor, Upashray, Vendor, Volunteer


class EventListView(EventScopedListView):
    model = Event
    template_name = "common/list.html"
    row_fields = ("name", "slug", "start_date", "end_date", "get_status_display", "is_current", "is_active")
    headers = ["Name", "Slug", "Start", "End", "Status", "Current", "Active"]
    create_url_name = "masters:event-create"
    edit_url_name = "masters:event-update"
    delete_url_name = "masters:event-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Events"
        context["page_subtitle"] = "Manage Chaturmas cycles"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:event-list")
    permission_required = "masters.add_event"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Event"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        obj = form.save()
        self.object = obj
        log_activity(
            user=self.request.user,
            event=obj,
            action="created",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            new_value=serialize_instance(obj),
            request=self.request,
        )
        messages.success(self.request, "Record created successfully.")
        return redirect(self.success_url)


class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:event-list")
    permission_required = "masters.change_event"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Event"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        before = serialize_instance(self.get_object())
        obj = form.save()
        self.object = obj
        log_activity(
            user=self.request.user,
            event=obj,
            action="updated",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            old_value=before,
            new_value=serialize_instance(obj),
            request=self.request,
        )
        messages.success(self.request, "Record updated successfully.")
        return redirect(self.success_url)


class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Event
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("masters:event-list")
    permission_required = "masters.delete_event"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        old_value = serialize_instance(obj)
        log_activity(
            user=request.user,
            event=obj,
            action="deleted",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            old_value=old_value,
            request=request,
        )
        messages.success(self.request, "Record deleted successfully.")
        return super().delete(request, *args, **kwargs)


class ItemListView(EventScopedListView):
    model = Item
    template_name = "common/list.html"
    row_fields = ("item_code", "display_name", "get_category_display", "unit", "default_size", "estimated_rate")
    headers = ["Code", "Item", "Category", "Unit", "Size", "Rate"]
    search_fields = ["item_code", "item_name"]
    create_url_name = "masters:item-create"
    edit_url_name = "masters:item-update"
    delete_url_name = "masters:item-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Items"
        context["page_subtitle"] = "Event-scoped item master"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class ItemCreateView(EventScopedCreateView):
    model = Item
    form_class = ItemForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:item-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Item"
        context["list_url"] = self.success_url
        return context


class ItemUpdateView(EventScopedUpdateView):
    model = Item
    form_class = ItemForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:item-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Item"
        context["list_url"] = self.success_url
        return context


class ItemDeleteView(EventScopedDeleteView):
    model = Item
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("masters:item-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class UpashrayListView(EventScopedListView):
    model = Upashray
    template_name = "common/list.html"
    row_fields = ("name", "area", "city", "contact_person", "mobile", "get_status_display")
    headers = ["Name", "Area", "City", "Contact", "Mobile", "Status"]
    search_fields = ["name", "area", "city", "mobile"]
    create_url_name = "masters:upashray-create"
    edit_url_name = "masters:upashray-update"
    delete_url_name = "masters:upashray-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Upashrays"
        context["page_subtitle"] = "Event-wise upashray master"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class UpashrayCreateView(EventScopedCreateView):
    model = Upashray
    form_class = UpashrayForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:upashray-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Upashray"
        context["list_url"] = self.success_url
        return context


class UpashrayUpdateView(EventScopedUpdateView):
    model = Upashray
    form_class = UpashrayForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:upashray-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Upashray"
        context["list_url"] = self.success_url
        return context


class UpashrayDeleteView(EventScopedDeleteView):
    model = Upashray
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("masters:upashray-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class VolunteerListView(EventScopedListView):
    model = Volunteer
    template_name = "common/list.html"
    row_fields = ("name", "mobile", "email", "area", "vehicle_available")
    headers = ["Name", "Mobile", "Email", "Area", "Vehicle"]
    search_fields = ["name", "mobile", "email", "area"]
    create_url_name = "masters:volunteer-create"
    edit_url_name = "masters:volunteer-update"
    delete_url_name = "masters:volunteer-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Volunteers"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class VolunteerCreateView(EventScopedCreateView):
    model = Volunteer
    form_class = VolunteerForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:volunteer-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Volunteer"
        context["list_url"] = self.success_url
        return context


class VolunteerUpdateView(EventScopedUpdateView):
    model = Volunteer
    form_class = VolunteerForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:volunteer-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Volunteer"
        context["list_url"] = self.success_url
        return context


class VolunteerDeleteView(EventScopedDeleteView):
    model = Volunteer
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("masters:volunteer-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class SponsorListView(EventScopedListView):
    model = Sponsor
    template_name = "common/list.html"
    row_fields = ("sponsor_name", "mobile", "organization", "reference_volunteer")
    headers = ["Sponsor", "Mobile", "Organization", "Reference Volunteer"]
    search_fields = ["sponsor_name", "mobile", "organization"]
    create_url_name = "masters:sponsor-create"
    edit_url_name = "masters:sponsor-update"
    delete_url_name = "masters:sponsor-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sponsors"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class SponsorCreateView(EventScopedCreateView):
    model = Sponsor
    form_class = SponsorForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:sponsor-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Sponsor"
        context["list_url"] = self.success_url
        return context


class SponsorUpdateView(EventScopedUpdateView):
    model = Sponsor
    form_class = SponsorForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:sponsor-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Sponsor"
        context["list_url"] = self.success_url
        return context


class SponsorDeleteView(EventScopedDeleteView):
    model = Sponsor
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("masters:sponsor-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class VendorListView(EventScopedListView):
    model = Vendor
    template_name = "common/list.html"
    row_fields = ("vendor_name", "contact_person", "mobile", "gst_no")
    headers = ["Vendor", "Contact", "Mobile", "GST No"]
    search_fields = ["vendor_name", "contact_person", "mobile", "gst_no"]
    create_url_name = "masters:vendor-create"
    edit_url_name = "masters:vendor-update"
    delete_url_name = "masters:vendor-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Vendors"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class VendorCreateView(EventScopedCreateView):
    model = Vendor
    form_class = VendorForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:vendor-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Vendor"
        context["list_url"] = self.success_url
        return context


class VendorUpdateView(EventScopedUpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:vendor-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Vendor"
        context["list_url"] = self.success_url
        return context


class VendorDeleteView(EventScopedDeleteView):
    model = Vendor
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("masters:vendor-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context
