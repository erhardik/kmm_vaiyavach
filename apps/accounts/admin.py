from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import EventMembership, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class EventMembershipInline(admin.TabularInline):
    model = EventMembership
    extra = 0
    fk_name = "user"


User = get_user_model()

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, EventMembershipInline]
    list_display = ("username", "email", "is_staff", "is_superuser", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "email", "profile__mobile", "event_memberships__event__name")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "mobile", "designation", "area", "updated_at")
    search_fields = ("user__username", "user__email", "mobile", "designation", "area")


@admin.register(EventMembership)
class EventMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "role", "is_primary", "is_active")
    list_filter = ("role", "is_primary", "is_active", "event")
    search_fields = ("user__username", "user__email", "event__name")
