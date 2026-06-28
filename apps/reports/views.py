from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.permissions import is_manager

from apps.dashboard.forms import ItemControlFilterForm
from apps.dashboard.services import get_dashboard_event_queryset
from apps.reports.forms import ReportScopeForm
from apps.reports.services import (
    build_inventory_ledger_export,
    build_item_control_export,
    build_analytics_summary,
    build_fund_ledger_export,
    build_requirement_export,
    build_recent_activity,
    build_sponsorship_export,
    build_top_shortage_items,
    build_report_home_summary,
    export_rows_to_csv,
    export_rows_to_xlsx,
    get_default_event,
)


class ReportHomeView(LoginRequiredMixin, TemplateView):
    template_name = "reports/home.html"

    def dispatch(self, request, *args, **kwargs):
        if is_manager(request.user):
            messages.warning(request, "You do not have access to Reports.")
            return redirect("masters:item-list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_queryset = get_dashboard_event_queryset()
        form = ReportScopeForm(self.request.GET or None, event_queryset=event_queryset)
        selected_event = form.cleaned_data["event"] if form.is_valid() else get_default_event()
        if selected_event is None:
            selected_event = get_default_event()
        context["form"] = form
        context["event_queryset"] = event_queryset
        context["selected_event"] = selected_event
        context["summary"] = build_report_home_summary(selected_event)
        context["analytics_url"] = reverse("reports:analytics")
        context["item_control_csv_url"] = reverse("reports:item-control-export") + "?format=csv"
        context["item_control_xlsx_url"] = reverse("reports:item-control-export") + "?format=xlsx"
        context["inventory_csv_url"] = reverse("reports:inventory-export") + "?format=csv"
        context["inventory_xlsx_url"] = reverse("reports:inventory-export") + "?format=xlsx"
        context["fund_csv_url"] = reverse("reports:fund-export") + "?format=csv"
        context["fund_xlsx_url"] = reverse("reports:fund-export") + "?format=xlsx"
        context["requirement_csv_url"] = reverse("reports:requirement-export") + "?format=csv"
        context["requirement_xlsx_url"] = reverse("reports:requirement-export") + "?format=xlsx"
        context["sponsorship_csv_url"] = reverse("reports:sponsorship-export") + "?format=csv"
        context["sponsorship_xlsx_url"] = reverse("reports:sponsorship-export") + "?format=xlsx"
        return context


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = "reports/analytics.html"

    def dispatch(self, request, *args, **kwargs):
        if is_manager(request.user):
            messages.warning(request, "You do not have access to Analytics.")
            return redirect("masters:item-list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_queryset = get_dashboard_event_queryset()
        form = ReportScopeForm(self.request.GET or None, event_queryset=event_queryset)
        selected_event = form.cleaned_data["event"] if form.is_valid() else get_default_event()
        context["form"] = form
        context["selected_event"] = selected_event
        context["summary"] = build_analytics_summary(selected_event)
        context["top_shortages"] = build_top_shortage_items(selected_event) if selected_event else []
        context["recent_activity"] = build_recent_activity(selected_event) if selected_event else []
        context["report_home_url"] = reverse("reports:report-home")
        return context


class ItemControlExportView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if is_manager(request.user):
            return HttpResponse("Access denied.", status=403)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        event_queryset = get_dashboard_event_queryset()
        form = ItemControlFilterForm(request.GET or None, event_queryset=event_queryset)
        if not form.is_valid():
            return HttpResponse("Invalid filter data.", status=400)

        event = form.cleaned_data.get("event") or get_default_event()
        if event is None:
            return HttpResponse("No active event found.", status=404)

        rows, _summary = build_item_control_export(
            event,
            category=form.cleaned_data.get("category") or None,
            pending_only=form.cleaned_data.get("pending_only", False),
            fully_covered=form.cleaned_data.get("fully_covered", False),
            shortage=form.cleaned_data.get("shortage", False),
        )
        headers = [
            "Item",
            "Category",
            "Rate",
            "Required",
            "Acquired",
            "Sponsored",
            "Received",
            "Purchased Qty",
            "Purchase Needed",
            "Remaining",
            "Shortage",
            "Stock",
            "Distributed",
            "Balance",
            "Required Cost",
            "Purchase Cost",
            "Source",
        ]
        export_format = request.GET.get("format", "csv").lower()
        if export_format == "xlsx":
            content = export_rows_to_xlsx(rows, headers, sheet_title="Item Control")
            response = HttpResponse(
                content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="item_control_center.xlsx"'
        else:
            content = export_rows_to_csv(rows, headers)
            response = HttpResponse(content, content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="item_control_center.csv"'
        return response


class InventoryLedgerExportView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if is_manager(request.user):
            return HttpResponse("Access denied.", status=403)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        event = get_default_event()
        event_id = request.GET.get("event")
        if event_id:
            event = get_dashboard_event_queryset().filter(pk=event_id).first() or event
        if event is None:
            return HttpResponse("No active event found.", status=404)

        rows = build_inventory_ledger_export(event)
        headers = ["Timestamp", "Item", "Type", "Qty", "Source Module", "Reference", "Unit Rate", "Remarks", "Created By"]
        export_format = request.GET.get("format", "csv").lower()
        if export_format == "xlsx":
            content = export_rows_to_xlsx(rows, headers, sheet_title="Inventory Ledger")
            response = HttpResponse(
                content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="inventory_ledger.xlsx"'
        else:
            content = export_rows_to_csv(rows, headers)
            response = HttpResponse(content, content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="inventory_ledger.csv"'
        return response


class FundLedgerExportView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if is_manager(request.user):
            return HttpResponse("Access denied.", status=403)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        event = get_default_event()
        event_id = request.GET.get("event")
        if event_id:
            event = get_dashboard_event_queryset().filter(pk=event_id).first() or event
        if event is None:
            return HttpResponse("No active event found.", status=404)

        rows = build_fund_ledger_export(event)
        headers = ["Date", "Type", "Category", "Amount", "Reference Module", "Reference ID", "Remarks"]
        export_format = request.GET.get("format", "csv").lower()
        if export_format == "xlsx":
            content = export_rows_to_xlsx(rows, headers, sheet_title="Fund Ledger")
            response = HttpResponse(
                content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="fund_ledger.xlsx"'
        else:
            content = export_rows_to_csv(rows, headers)
            response = HttpResponse(content, content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="fund_ledger.csv"'
        return response


class RequirementExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        event = get_default_event()
        event_id = request.GET.get("event")
        if event_id:
            event = get_dashboard_event_queryset().filter(pk=event_id).first() or event
        if event is None:
            return HttpResponse("No active event found.", status=404)

        rows = build_requirement_export(event)
        headers = ["Requirement", "Upashray", "Item", "Required Qty", "Remarks"]
        export_format = request.GET.get("format", "csv").lower()
        if export_format == "xlsx":
            content = export_rows_to_xlsx(rows, headers, sheet_title="Requirements")
            response = HttpResponse(
                content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="requirements.xlsx"'
        else:
            content = export_rows_to_csv(rows, headers)
            response = HttpResponse(content, content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="requirements.csv"'
        return response


class SponsorshipExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        event = get_default_event()
        event_id = request.GET.get("event")
        if event_id:
            event = get_dashboard_event_queryset().filter(pk=event_id).first() or event
        if event is None:
            return HttpResponse("No active event found.", status=404)

        rows = build_sponsorship_export(event)
        headers = ["Sponsor", "Item", "Committed Qty", "Received Qty", "Status", "Expected Date"]
        export_format = request.GET.get("format", "csv").lower()
        if export_format == "xlsx":
            content = export_rows_to_xlsx(rows, headers, sheet_title="Sponsorship")
            response = HttpResponse(
                content,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="sponsorship.xlsx"'
        else:
            content = export_rows_to_csv(rows, headers)
            response = HttpResponse(content, content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="sponsorship.csv"'
        return response
