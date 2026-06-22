from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.auditlog.services import log_activity, serialize_instance
from apps.masters.models import Event


class CurrentEventMixin:
    event_field_name = "event"

    def get_current_event(self):
        event_id = self.request.GET.get("event") or self.request.POST.get("event")
        if event_id:
            return Event.objects.filter(pk=event_id, is_active=True).first()
        return Event.objects.filter(is_current=True, is_active=True).first()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["current_event"] = self.get_current_event()
        return kwargs


class EventScopedListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    event_filter_param = "event"
    row_fields = ()
    edit_url_name = ""
    delete_url_name = ""
    create_url_name = ""
    permission_action = "view"
    raise_exception = True

    def get_permission_required(self):
        meta = self.model._meta
        return (f"{meta.app_label}.{self.permission_action}_{meta.model_name}",)

    def _perm(self, action):
        meta = self.model._meta
        return f"{meta.app_label}.{action}_{meta.model_name}"

    def get_row_url_kwargs(self, obj):
        return {"pk": obj.pk}

    def get_queryset(self):
        qs = super().get_queryset()
        has_event_field = any(field.name == "event" for field in qs.model._meta.get_fields())
        event_id = self.request.GET.get(self.event_filter_param)
        if event_id and has_event_field:
            qs = qs.filter(event_id=event_id)
        elif has_event_field:
            current_event = Event.objects.filter(is_current=True, is_active=True).first()
            if current_event:
                qs = qs.filter(event=current_event)
        search = self.request.GET.get("q")
        if search:
            search_fields = getattr(self, "search_fields", [])
            if search_fields:
                query = Q()
                for field in search_fields:
                    query |= Q(**{f"{field}__icontains": search})
                qs = qs.filter(query)
        return qs.select_related("event") if has_event_field else qs

    def get_table_rows(self):
        rows = []
        for obj in self.object_list:
            rows.append(
                {
                    "object": obj,
                    "cells": [getattr(obj, field)() if callable(getattr(obj, field)) else getattr(obj, field, "") for field in self.row_fields],
                    "edit_url": reverse(self.edit_url_name, kwargs=self.get_row_url_kwargs(obj)) if self.edit_url_name else "",
                    "delete_url": reverse(self.delete_url_name, kwargs=self.get_row_url_kwargs(obj)) if self.delete_url_name else "",
                }
            )
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["table_rows"] = self.get_table_rows()
        context["event_queryset"] = Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name")
        context["can_add"] = self.request.user.has_perm(self._perm("add"))
        context["can_change"] = self.request.user.has_perm(self._perm("change"))
        context["can_delete"] = self.request.user.has_perm(self._perm("delete"))
        return context


class EventScopedCreateView(CurrentEventMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_action = "add"
    raise_exception = True

    def get_permission_required(self):
        meta = self.model._meta
        return (f"{meta.app_label}.{self.permission_action}_{meta.model_name}",)

    def form_valid(self, form):
        event = self.get_current_event()
        if event is None:
            raise Http404("No active event found.")
        obj = form.save(commit=False)
        obj.event = event
        if hasattr(obj, "created_by_id"):
            obj.created_by = self.request.user
            obj.updated_by = self.request.user
        obj.save()
        self.object = obj
        form.save_m2m() if hasattr(form, "save_m2m") else None
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
        return redirect(self.get_success_url())


class EventScopedUpdateView(CurrentEventMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_action = "change"
    raise_exception = True

    def get_permission_required(self):
        meta = self.model._meta
        return (f"{meta.app_label}.{self.permission_action}_{meta.model_name}",)

    def form_valid(self, form):
        before = serialize_instance(self.get_object())
        obj = form.save(commit=False)
        if hasattr(obj, "updated_by_id"):
            obj.updated_by = self.request.user
        obj.save()
        self.object = obj
        log_activity(
            user=self.request.user,
            event=getattr(obj, "event", None),
            action="updated",
            module=self.model._meta.label_lower,
            record_id=obj.pk,
            old_value=before,
            new_value=serialize_instance(obj),
            request=self.request,
        )
        messages.success(self.request, "Record updated successfully.")
        return redirect(self.get_success_url())


class EventScopedDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_action = "delete"
    raise_exception = True

    def get_permission_required(self):
        meta = self.model._meta
        return (f"{meta.app_label}.{self.permission_action}_{meta.model_name}",)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        old_value = serialize_instance(obj)
        event = getattr(obj, "event", None)
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
