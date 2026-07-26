from django.contrib import admin

from apps.dashboard.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["volunteer_name", "event_rating", "portal_rating", "created_at"]
    list_filter = ["event", "event_rating", "portal_rating", "created_at"]
    search_fields = ["volunteer_name", "volunteer_mobile", "event_feedback", "portal_feedback"]
    date_hierarchy = "created_at"
    readonly_fields = ["created_at"]
