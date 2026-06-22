from apps.auditlog.models import ActivityLog
from apps.common.views import EventScopedListView


class ActivityLogListView(EventScopedListView):
    model = ActivityLog
    template_name = "common/list.html"
    row_fields = ("timestamp", "user", "event", "module", "action", "record_id")
    headers = ["Timestamp", "User", "Event", "Module", "Action", "Record ID"]
    search_fields = ["user__username", "module", "action", "record_id"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Activity Log"
        context["page_subtitle"] = "Immutable audit trail"
        context["create_url"] = ""
        return context
