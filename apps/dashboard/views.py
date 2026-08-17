import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View

from apps.accounts.permissions import is_manager

from apps.dashboard.forms import ItemControlFilterForm
from apps.dashboard.models import Feedback
from apps.dashboard.services import (
    build_dashboard_data,
    build_home_summary,
    build_item_control_center,
    build_public_item_preview,
    build_public_status_summary,
    get_dashboard_event_queryset,
    resolve_dashboard_event,
)
from apps.masters.models import Event


class PublicLandingView(TemplateView):
    template_name = "public/landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name").first()
        context["event"] = event
        context["accepting_responses"] = bool(event and event.accepting_responses)
        context["status_summary"] = build_public_status_summary(event) if event else {}
        context["public_items"] = build_public_item_preview(event) if event else []
        context["request_form_url"] = reverse_lazy("requirements:public-collect", kwargs={"event_token": event.public_form_token}) if event else reverse_lazy("dashboard:home")
        context["requests_url"] = reverse_lazy("public-requests")
        context["login_url"] = reverse_lazy("login")
        return context


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def dispatch(self, request, *args, **kwargs):
        if is_manager(request.user):
            return redirect("masters:item-list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = resolve_dashboard_event(self.request)
        context["event"] = event
        context["selected_event"] = event
        context["event_queryset"] = get_dashboard_event_queryset()
        context["summary"] = build_home_summary(event) if event else {}
        context["item_control_url"] = reverse_lazy("dashboard:item_control_center")
        return context


class ItemControlCenterView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/item_control_center.html"

    def dispatch(self, request, *args, **kwargs):
        if is_manager(request.user):
            return redirect("masters:item-list")
        return super().dispatch(request, *args, **kwargs)

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


class ChaturmasDashboardDataView(LoginRequiredMixin, TemplateView):
    """JSON endpoint serving dashboard data in the format expected by the chart dashboard."""

    def get(self, request, *args, **kwargs):
        event = resolve_dashboard_event(request)
        if not event:
            return JsonResponse({"items_meta": [], "records": []})
        data = build_dashboard_data(event)
        return JsonResponse(data)


class ChaturmasDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/chaturmas_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = resolve_dashboard_event(self.request)
        context["event"] = event
        context["event_queryset"] = get_dashboard_event_queryset()
        if event:
            data = build_dashboard_data(event)
            context["dashboard_json"] = json.dumps(data)
        else:
            context["dashboard_json"] = json.dumps({"items_meta": [], "records": []})
        return context


class PublicFeedbackView(View):
    template_name = "public/feedback.html"

    def get_event(self):
        return Event.objects.filter(is_active=True).order_by("-is_current", "-start_date", "name").first()

    def get(self, request):
        event = self.get_event()
        if not event:
            return redirect("public-landing")
        return render(request, self.template_name, {"event": event, "login_url": reverse_lazy("login")})

    def post(self, request):
        event = self.get_event()
        if not event:
            return redirect("public-landing")
        errors = []
        name = request.POST.get("volunteer_name", "").strip()
        if not name:
            errors.append("Please enter your name.")
        event_feedback = request.POST.get("event_feedback", "").strip()
        portal_feedback = request.POST.get("portal_feedback", "").strip()

        event_rating = request.POST.get("event_rating")
        portal_rating = request.POST.get("portal_rating")
        if not event_rating or not portal_rating:
            errors.append("Please provide both ratings.")
        try:
            event_rating = int(event_rating) if event_rating else 0
            portal_rating = int(portal_rating) if portal_rating else 0
            if event_rating < 1 or event_rating > 5 or portal_rating < 1 or portal_rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("Ratings must be between 1 and 5.")
        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, self.template_name, {"event": event, "login_url": reverse_lazy("login")})
        Feedback.objects.create(
            event=event,
            volunteer_name=name,
            volunteer_mobile=request.POST.get("volunteer_mobile", "").strip(),
            event_rating=event_rating,
            portal_rating=portal_rating,
            event_feedback=event_feedback,
            portal_feedback=portal_feedback,
        )
        lang = request.POST.get("lang", "gu")
        return redirect(f"{reverse('feedback-thanks')}?lang={lang}")


class FeedbackDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        fb = get_object_or_404(Feedback, pk=pk)
        fb.delete()
        messages.success(request, "Feedback deleted.")
        return redirect("dashboard:feedback-list")


class FeedbackListView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/feedback_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedbacks = Feedback.objects.select_related("event").order_by("-created_at")
        context["feedbacks"] = feedbacks
        context["total"] = feedbacks.count()
        avg_event = feedbacks.aggregate(avg=Avg("event_rating"))["avg"]
        avg_portal = feedbacks.aggregate(avg=Avg("portal_rating"))["avg"]
        context["avg_event_rating"] = round(avg_event, 1) if avg_event else None
        context["avg_portal_rating"] = round(avg_portal, 1) if avg_portal else None
        return context


class FeedbackThankYouView(TemplateView):
    template_name = "public/feedback_thanks.html"
