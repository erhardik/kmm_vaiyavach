from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Max, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from apps.auditlog.services import log_activity, serialize_instance
from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.inventory.models import InventoryBalance, InventoryTransaction, InventoryTransactionType, PurchaseLot
from apps.masters.forms import EventCreateForm, EventManagerContactForm, EventUpdateForm, ItemForm, SponsorForm, UpashrayForm, VendorForm, VolunteerForm
from apps.requirements.models import RequirementHeader, RequirementLine, RequirementStatus
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


class ItemListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Item
    template_name = "masters/item_list.html"
    paginate_by = 50
    permission_required = "masters.view_item"
    raise_exception = True
    create_url_name = "masters:item-create"
    edit_url_name = "masters:item-update"
    delete_url_name = "masters:item-delete"

    def _perm(self, action):
        meta = self.model._meta
        return f"{meta.app_label}.{action}_{meta.model_name}"

    def get_queryset(self):
        qs = Item.objects.filter(event=self._get_event(), is_active=True)
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(item_code__icontains=search) | Q(item_name__icontains=search) | Q(item_name_gu__icontains=search)
            )
        return qs.select_related("parent_item")

    def _get_event(self):
        event_id = self.request.GET.get("event")
        if event_id:
            return Event.objects.filter(pk=event_id, is_active=True).first()
        return Event.objects.filter(is_current=True, is_active=True).first()

    def _expand_items(self, event):
        base_items = (
            Item.objects.filter(event=event, is_active=True, parent_item__isnull=True)
            .prefetch_related("variants")
            .order_by("standard_serial", "pk")
        )
        items = []
        for base in base_items:
            variants = list(base.variants.filter(is_active=True).order_by("variant_name", "pk"))
            if variants:
                items.extend(variants)
            else:
                items.append(base)
        return items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self._get_event()
        all_items = self._expand_items(event)
        search = self.request.GET.get("q", "").lower()
        if search:
            all_items = [i for i in all_items if search in i.item_code.lower() or search in i.item_name.lower() or search in i.item_name_gu.lower()]

        item_ids = [i.pk for i in all_items]
        balances = {
            b.item_id: b
            for b in InventoryBalance.objects.filter(event=event, item_id__in=item_ids)
        }
        pos_types = [InventoryTransactionType.PURCHASE, InventoryTransactionType.DONATION, InventoryTransactionType.SPONSORSHIP_RECEIPT, InventoryTransactionType.RETURN, InventoryTransactionType.ADJUSTMENT]
        acquired_qs = InventoryTransaction.objects.filter(event=event, item_id__in=item_ids, transaction_type__in=pos_types).values("item_id").annotate(total=Sum("qty"))
        acquired_map = {a["item_id"]: a["total"] for a in acquired_qs}
        distributed_qs = InventoryTransaction.objects.filter(event=event, item_id__in=item_ids, transaction_type=InventoryTransactionType.DISTRIBUTION).values("item_id").annotate(total=Sum("qty"))
        distributed_map = {d["item_id"]: d["total"] for d in distributed_qs}
        req_header_ids = RequirementHeader.objects.filter(event=event, is_active=True).exclude(status=RequirementStatus.DRAFT).values_list("pk", flat=True)
        current_req_qs = RequirementLine.objects.filter(event=event, requirement_id__in=req_header_ids, item_id__in=item_ids).values("item_id").annotate(total=Sum("required_qty"))
        current_req_map = {r["item_id"]: r["total"] for r in current_req_qs}
        latest_lots = {}
        for item_id in item_ids:
            lot = PurchaseLot.objects.filter(event=event, item_id=item_id).order_by("-transaction_date", "-created_at").first()
            if lot:
                latest_lots[item_id] = lot

        table_rows = []
        for item in all_items:
            bal = balances.get(item.pk)
            current_stock = int(bal.current_stock) if bal and bal.current_stock == int(bal.current_stock) else (bal.current_stock if bal else 0)
            qty_acquired = int(acquired_map.get(item.pk, 0)) if acquired_map.get(item.pk, 0) == int(acquired_map.get(item.pk, 0)) else acquired_map.get(item.pk, 0)
            qty_distributed = int(distributed_map.get(item.pk, 0)) if distributed_map.get(item.pk, 0) == int(distributed_map.get(item.pk, 0)) else distributed_map.get(item.pk, 0)
            lot = latest_lots.get(item.pk)
            cost = lot.unit_rate if lot else Decimal(item.estimated_rate or 0)
            if cost == int(cost):
                cost = int(cost)
            vendor = str(lot.vendor) if lot and lot.vendor else ""
            manager = lot.managed_by.get_full_name() if lot and lot.managed_by else (str(lot.managed_by) if lot and lot.managed_by else "")
            table_rows.append({
                "item_code": item.item_code,
                "display_name": item.display_name(),
                "type_size": item.variant_name_gu or item.variant_name or item.default_size_gu or item.default_size or "",
                "current_req": int(current_req_map.get(item.pk, 0)),
                "current_stock": current_stock,
                "qty_acquired": qty_acquired,
                "qty_distributed": qty_distributed,
                "cost": cost,
                "vendor": vendor,
                "manager": manager,
                "edit_url": reverse(self.edit_url_name, kwargs={"pk": item.pk}) if self.edit_url_name else "",
                "delete_url": reverse(self.delete_url_name, kwargs={"pk": item.pk}) if self.delete_url_name else "",
            })

        paginator = Paginator(table_rows, self.paginate_by)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context["page_title"] = "Items"
        context["page_subtitle"] = "Event-scoped item master"
        context["create_url"] = reverse_lazy(self.create_url_name)
        context["table_rows"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["event_queryset"] = Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name")
        context["can_add"] = self.request.user.has_perm(self._perm("add"))
        context["can_change"] = self.request.user.has_perm(self._perm("change"))
        context["can_delete"] = self.request.user.has_perm(self._perm("delete"))
        return context


class ItemListExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        event_id = request.GET.get("event")
        event = Event.objects.filter(pk=event_id, is_active=True).first() if event_id else Event.objects.filter(is_current=True, is_active=True).first()
        if event is None:
            return HttpResponse("No active event found.", status=404)

        item_ids = set()
        base_items = Item.objects.filter(event=event, is_active=True, parent_item__isnull=True).prefetch_related("variants").order_by("standard_serial", "pk")
        all_items = []
        for base in base_items:
            variants = list(base.variants.filter(is_active=True).order_by("variant_name", "pk"))
            if variants:
                all_items.extend(variants)
            else:
                all_items.append(base)

        item_ids = [i.pk for i in all_items]
        balances = {b.item_id: b for b in InventoryBalance.objects.filter(event=event, item_id__in=item_ids)}
        pos_types = [InventoryTransactionType.PURCHASE, InventoryTransactionType.DONATION, InventoryTransactionType.SPONSORSHIP_RECEIPT, InventoryTransactionType.RETURN, InventoryTransactionType.ADJUSTMENT]
        acquired_map = {a["item_id"]: a["total"] for a in InventoryTransaction.objects.filter(event=event, item_id__in=item_ids, transaction_type__in=pos_types).values("item_id").annotate(total=Sum("qty"))}
        distributed_map = {d["item_id"]: d["total"] for d in InventoryTransaction.objects.filter(event=event, item_id__in=item_ids, transaction_type=InventoryTransactionType.DISTRIBUTION).values("item_id").annotate(total=Sum("qty"))}
        req_header_ids = RequirementHeader.objects.filter(event=event, is_active=True).exclude(status=RequirementStatus.DRAFT).values_list("pk", flat=True)
        current_req_map = {r["item_id"]: r["total"] for r in RequirementLine.objects.filter(event=event, requirement_id__in=req_header_ids, item_id__in=item_ids).values("item_id").annotate(total=Sum("required_qty"))}
        latest_lots = {}
        for item_id in item_ids:
            lot = PurchaseLot.objects.filter(event=event, item_id=item_id).order_by("-transaction_date", "-created_at").first()
            if lot:
                latest_lots[item_id] = lot

        workbook = Workbook()

        # --- Sheet 1: Order Summary (pivot) ---
        ws_summary = workbook.active
        ws_summary.title = "Order Summary"

        summary_headers = ["Item Code", "Item Name / Variant", "Type / Size", "Total Required"]
        for col, h in enumerate(summary_headers, 1):
            cell = ws_summary.cell(row=1, column=col, value=h)
            cell.fill = PatternFill("solid", fgColor="DCE9F5")
            cell.font = Font(bold=True)
            cell.alignment = center

        for i, item in enumerate(all_items, 2):
            ws_summary.cell(row=i, column=1, value=item.item_code)
            ws_summary.cell(row=i, column=2, value=item.display_name())
            ws_summary.cell(row=i, column=3, value=item.variant_name_gu or item.variant_name or item.default_size_gu or item.default_size or "")
            ws_summary.cell(row=i, column=4, value=int(current_req_map.get(item.pk, 0)))

        ws_summary.freeze_panes = "A2"
        for col in range(1, 5):
            max_len = 0
            for row in ws_summary.iter_rows(min_row=1, max_row=ws_summary.max_row, min_col=col, max_col=col):
                for cell in row:
                    try:
                        text = str(cell.value or "")
                    except Exception:
                        text = ""
                    max_len = max(max_len, len(text))
            ws_summary.column_dimensions[get_column_letter(col)].width = min(max_len + 3, 40)

        # --- Sheet 2: Item Detail (column-per-item) ---
        ws_detail = workbook.create_sheet("Item Master")

        detail_header_fill = PatternFill("solid", fgColor="DCE9F5")
        center = Alignment(horizontal="center", vertical="center")
        right = Alignment(horizontal="right", vertical="center")

        # Row 1: item codes as column headers
        ws_detail.cell(row=1, column=1, value="Specification")
        ws_detail.cell(row=1, column=1).fill = detail_header_fill
        ws_detail.cell(row=1, column=1).font = Font(bold=True)
        ws_detail.cell(row=1, column=1).alignment = center
        for ci, item in enumerate(all_items, 2):
            cell = ws_detail.cell(row=1, column=ci, value=item.item_code)
            cell.fill = detail_header_fill
            cell.font = Font(bold=True)
            cell.alignment = center

        # Row 2: Type/Size of each item
        ws_detail.cell(row=2, column=1, value="Type / Size")
        ws_detail.cell(row=2, column=1).font = Font(bold=True)
        for ci, item in enumerate(all_items, 2):
            ws_detail.cell(row=2, column=ci, value=item.variant_name_gu or item.variant_name or item.default_size_gu or item.default_size or "")

        # Row 3+: metric rows
        cost_values = []
        vendor_values = []
        manager_values = []
        for item in all_items:
            lot = latest_lots.get(item.pk)
            cost = lot.unit_rate if lot else Decimal(item.estimated_rate or 0)
            if cost == int(cost):
                cost = int(cost)
            cost_values.append(cost)
            vendor_values.append(str(lot.vendor) if lot and lot.vendor else "")
            manager_values.append(lot.managed_by.get_full_name() if lot and lot.managed_by else (str(lot.managed_by) if lot and lot.managed_by else ""))

        metrics = [
            ("Item Name", [item.display_name() for item in all_items]),
            ("Current Req.", [int(current_req_map.get(item.pk, 0)) for item in all_items]),
            ("Current Stock", [int(balances.get(item.pk).current_stock) if balances.get(item.pk) and balances.get(item.pk).current_stock == int(balances.get(item.pk).current_stock) else (balances.get(item.pk).current_stock if balances.get(item.pk) else 0) for item in all_items]),
            ("Qty Acquired", [int(acquired_map.get(item.pk, 0)) if acquired_map.get(item.pk, 0) == int(acquired_map.get(item.pk, 0)) else acquired_map.get(item.pk, 0) for item in all_items]),
            ("Qty Distributed", [int(distributed_map.get(item.pk, 0)) if distributed_map.get(item.pk, 0) == int(distributed_map.get(item.pk, 0)) else distributed_map.get(item.pk, 0) for item in all_items]),
            ("Cost", cost_values),
            ("Vendor", vendor_values),
            ("Manager", manager_values),
        ]

        for ri, (metric_name, values) in enumerate(metrics, 3):
            cell = ws_detail.cell(row=ri, column=1, value=metric_name)
            cell.font = Font(bold=True)
            for ci, val in enumerate(values, 2):
                ws_detail.cell(row=ri, column=ci, value=val)
                if metric_name in ("Current Req.", "Current Stock", "Qty Acquired", "Qty Distributed", "Cost"):
                    ws_detail.cell(row=ri, column=ci).alignment = right

        ws_detail.freeze_panes = "B3"
        for col_idx in range(1, len(all_items) + 2):
            max_len = 0
            for row in ws_detail.iter_rows(min_row=1, max_row=ws_detail.max_row, min_col=col_idx, max_col=col_idx):
                for cell in row:
                    try:
                        text = str(cell.value or "")
                    except Exception:
                        text = ""
                    max_len = max(max_len, len(text))
            ws_detail.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 3, 40)

        buffer = BytesIO()
        workbook.save(buffer)
        response = HttpResponse(buffer.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="item_master_{event.name}.xlsx"'

        buffer = BytesIO()
        workbook.save(buffer)
        response = HttpResponse(buffer.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="item_master_{event.name}.xlsx"'
        return response


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
