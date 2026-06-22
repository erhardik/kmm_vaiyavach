from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from apps.dashboard.forms import ItemControlFilterForm
from apps.dashboard.services import build_home_summary, build_item_control_center, get_dashboard_event_queryset
from apps.masters.models import Event


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = Event.objects.filter(is_active=True).order_by("-is_current", "-start_date").first()
        context["event"] = event
        context["summary"] = build_home_summary(event) if event else {}
        context["item_control_url"] = reverse_lazy("dashboard:item_control_center")
        return context


class ItemControlCenterView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/item_control_center.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_queryset = get_dashboard_event_queryset()
        selected_event = event_queryset.first()
        form = ItemControlFilterForm(self.request.GET or None, event_queryset=event_queryset)
        is_valid = form.is_valid()
        if is_valid and form.cleaned_data.get("event"):
            selected_event = form.cleaned_data["event"]
        category = form.cleaned_data.get("category") if is_valid else self.request.GET.get("category") or None
        pending_only = form.cleaned_data.get("pending_only") if is_valid else "pending_only" in self.request.GET
        fully_covered = form.cleaned_data.get("fully_covered") if is_valid else "fully_covered" in self.request.GET
        shortage = form.cleaned_data.get("shortage") if is_valid else "shortage" in self.request.GET

        rows = []
        summary = {}
        if selected_event:
            rows, summary = build_item_control_center(
                selected_event,
                category=category or None,
                pending_only=pending_only,
                fully_covered=fully_covered,
                shortage=shortage,
            )

        context["selected_event"] = selected_event
        context["form"] = form
        context["rows"] = rows
        context["summary"] = summary
        context["event_queryset"] = event_queryset
        return context
