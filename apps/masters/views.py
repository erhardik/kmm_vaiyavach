from django.urls import reverse_lazy
from django.urls import reverse

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db.models import Max
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.auditlog.services import log_activity, serialize_instance
from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.masters.forms import EventCreateForm, EventManagerContactForm, EventUpdateForm, ItemForm, SponsorForm, UpashrayForm, VendorForm, VolunteerForm
from apps.masters.models import Event, EventManagerContact, Item, Sponsor, Upashray, Vendor, Volunteer


class EventContextMixin:
    def get_event(self):
        event_pk = self.kwargs.get("event_pk")
        if event_pk:
            return Event.objects.filter(pk=event_pk, is_active=True).first()
        return None


class EventListView(EventScopedListView):
    model = Event
    template_name = "masters/event_list.html"
    row_fields = ("name", "slug", "start_date", "end_date", "primary_contact_name", "primary_contact_mobile", "get_status_display", "is_current", "is_active")
    headers = ["Name", "Slug", "Start", "End", "Primary Contact", "Mobile", "Status", "Current", "Active"]
    create_url_name = "masters:event-create"
    edit_url_name = "masters:event-update"
    delete_url_name = "masters:event-delete"

    def get_row_url_kwargs(self, obj):
        return {"pk": obj.pk}

    def get_table_rows(self):
        rows = super().get_table_rows()
        for row in rows:
            obj = row["object"]
            row["contacts_url"] = reverse("masters:event-contact-list", kwargs={"event_pk": obj.pk})
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Events"
        context["page_subtitle"] = "Manage Chaturmas cycles and their manager contacts."
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventCreateForm
    template_name = "common/form.html"
    permission_required = "masters.add_event"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Event"
        context["page_subtitle"] = "Start a new cycle with the event name and date range."
        context["list_url"] = reverse_lazy("masters:event-list")
        return context

    def form_valid(self, form):
        obj = form.save()
        Event.objects.exclude(pk=obj.pk).update(is_current=False)
        if not obj.is_current:
            obj.is_current = True
            obj.save(update_fields=["is_current"])
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
        return redirect(reverse("masters:event-update", kwargs={"pk": obj.pk}))


class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Event
    form_class = EventUpdateForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:event-list")
    permission_required = "masters.change_event"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Event"
        context["list_url"] = self.success_url
        context["manager_contacts"] = self.object.masters_eventmanagercontact_records.filter(is_active=True).order_by("-is_primary", "contact_name")
        context["manager_contacts_create_url"] = reverse("masters:event-contact-create", kwargs={"event_pk": self.object.pk})
        context["manager_contacts_list_url"] = reverse("masters:event-contact-list", kwargs={"event_pk": self.object.pk})
        context["public_share_url"] = reverse("requirements:public-collect", kwargs={"event_token": self.object.public_form_token})
        context["public_share_label"] = "Public Requirement Form Link"
        return context

    def form_valid(self, form):
        before = serialize_instance(self.get_object())
        obj = form.save()
        if obj.is_current:
            Event.objects.exclude(pk=obj.pk).update(is_current=False)
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


class EventManagerContactListView(EventContextMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = EventManagerContact
    template_name = "common/list.html"
    row_fields = ("contact_name", "mobile", "email", "designation", "primary_label")
    headers = ["Name", "Mobile", "Email", "Designation", "Primary"]
    permission_required = "masters.view_eventmanagercontact"
    raise_exception = True
    create_url_name = "masters:event-contact-create"
    edit_url_name = "masters:event-contact-update"
    delete_url_name = "masters:event-contact-delete"

    def get_queryset(self):
        event = self.get_event()
        if event is None:
            return EventManagerContact.objects.none()
        return EventManagerContact.objects.filter(event=event, is_active=True).order_by("-is_primary", "contact_name")

    def get_row_url_kwargs(self, obj):
        return {"event_pk": obj.event_id, "pk": obj.pk}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_event()
        context["page_title"] = f"{event.name} Contacts" if event else "Event Contacts"
        context["page_subtitle"] = "Manage the default manager contact and any additional contacts."
        context["create_url"] = reverse("masters:event-contact-create", kwargs={"event_pk": event.pk}) if event else ""
        context["list_url"] = reverse_lazy("masters:event-list")
        context["event"] = event
        return context


class EventManagerContactCreateView(EventContextMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = EventManagerContact
    form_class = EventManagerContactForm
    template_name = "common/form.html"
    permission_required = "masters.add_eventmanagercontact"
    raise_exception = True

    def get_event(self):
        return super().get_event() or Event.objects.filter(is_current=True, is_active=True).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_event()
        context["page_title"] = "Add Event Contact"
        context["page_subtitle"] = "Add a manager contact for the selected event."
        context["list_url"] = reverse("masters:event-contact-list", kwargs={"event_pk": event.pk}) if event else reverse_lazy("masters:event-list")
        context["event"] = event
        return context

    def form_valid(self, form):
        event = self.get_event()
        if event is None:
            return redirect(reverse_lazy("masters:event-list"))
        obj = form.save(commit=False)
        obj.event = event
        if obj.is_primary:
            EventManagerContact.objects.filter(event=event, is_primary=True).update(is_primary=False)
        obj.save()
        self.object = obj
        log_activity(
            user=self.request.user,
            event=event,
            action="created",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            new_value=serialize_instance(obj),
            request=self.request,
        )
        messages.success(self.request, "Record created successfully.")
        return redirect(reverse("masters:event-contact-list", kwargs={"event_pk": event.pk}))


class EventManagerContactUpdateView(EventContextMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = EventManagerContact
    form_class = EventManagerContactForm
    template_name = "common/form.html"
    permission_required = "masters.change_eventmanagercontact"
    raise_exception = True

    def get_queryset(self):
        event_pk = self.kwargs.get("event_pk")
        return EventManagerContact.objects.filter(event_id=event_pk).select_related("event")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object.event
        context["page_title"] = "Update Event Contact"
        context["page_subtitle"] = event.name if event else None
        context["list_url"] = reverse("masters:event-contact-list", kwargs={"event_pk": event.pk}) if event else reverse_lazy("masters:event-list")
        context["event"] = event
        return context

    def form_valid(self, form):
        event = form.instance.event
        before = serialize_instance(self.get_object())
        obj = form.save(commit=False)
        if obj.is_primary:
            EventManagerContact.objects.filter(event=event, is_primary=True).exclude(pk=obj.pk).update(is_primary=False)
        obj.save()
        self.object = obj
        log_activity(
            user=self.request.user,
            event=event,
            action="updated",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            old_value=before,
            new_value=serialize_instance(obj),
            request=self.request,
        )
        messages.success(self.request, "Record updated successfully.")
        return redirect(reverse("masters:event-contact-list", kwargs={"event_pk": event.pk}))


class EventManagerContactDeleteView(EventContextMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = EventManagerContact
    template_name = "common/confirm_delete.html"
    permission_required = "masters.delete_eventmanagercontact"
    raise_exception = True

    def get_queryset(self):
        event_pk = self.kwargs.get("event_pk")
        return EventManagerContact.objects.filter(event_id=event_pk).select_related("event")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object.event
        context["list_url"] = reverse("masters:event-contact-list", kwargs={"event_pk": event.pk}) if event else reverse_lazy("masters:event-list")
        return context

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        old_value = serialize_instance(obj)
        event = obj.event
        messages.success(self.request, "Record deleted successfully.")
        response = super().delete(request, *args, **kwargs)
        log_activity(
            user=request.user,
            event=event,
            action="deleted",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            old_value=old_value,
            request=request,
        )
        return response


class ItemListView(EventScopedListView):
    model = Item
    template_name = "common/list.html"
    row_fields = ("item_code", "display_name", "get_category_display", "unit", "default_size", "estimated_rate")
    headers = ["Code", "Item", "Category", "Unit", "Size", "Rate"]
    search_fields = ["item_code", "item_name"]
    create_url_name = "masters:item-create"
    edit_url_name = "masters:item-update"
    delete_url_name = "masters:item-delete"

    def get_table_headers(self):
        headers = super().get_table_headers()
        if self.request.user.groups.filter(name="KMM Manager").exists():
            return headers[:-1]
        return headers

    def get_table_rows(self):
        rows = super().get_table_rows()
        if self.request.user.groups.filter(name="KMM Manager").exists():
            for row in rows:
                row["cells"] = row["cells"][:-1]
        return rows

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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Item"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        event = self.get_current_event()
        if event is None:
            raise Http404("No active event found.")
        obj = form.save(commit=False)
        obj.event = event
        next_serial = (Item.objects.filter(event=event).aggregate(max_serial=Max("standard_serial"))["max_serial"] or 0) + 1
        if not obj.standard_serial:
            obj.standard_serial = next_serial
        obj.is_active = bool(form.cleaned_data.get("add_to_current_form_immediately"))
        obj.save()
        self.object = obj
        if hasattr(form, "save_m2m"):
            form.save_m2m()
        log_activity(
            user=self.request.user,
            event=event,
            action="created",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            new_value=serialize_instance(obj),
            request=self.request,
        )
        messages.success(self.request, "Record created successfully.")
        return redirect(self.success_url)


class ItemUpdateView(EventScopedUpdateView):
    model = Item
    form_class = ItemForm
    template_name = "common/form.html"
    success_url = reverse_lazy("masters:item-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Item"
        context["list_url"] = self.success_url
        return context

    def form_valid(self, form):
        before = serialize_instance(self.get_object())
        obj = form.save(commit=False)
        obj.updated_by = self.request.user
        if "is_active" in form.cleaned_data:
            obj.is_active = form.cleaned_data["is_active"]
        obj.save()
        self.object = obj
        log_activity(
            user=self.request.user,
            event=obj.event,
            action="updated",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            old_value=before,
            new_value=serialize_instance(obj),
            request=self.request,
        )
        messages.success(self.request, "Record updated successfully.")
        return redirect(self.success_url)


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
    row_fields = ("name", "display_sub_area", "city", "contact_person", "mobile", "get_status_display")
    headers = ["Name", "Route", "City", "Contact", "Mobile", "Status"]
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
