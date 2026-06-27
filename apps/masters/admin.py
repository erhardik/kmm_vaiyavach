from django.contrib import admin
from .models import Event, EventManagerContact, Item, RouteArea, RouteSubArea, Sponsor, Upashray, Vendor, Volunteer


class RouteSubAreaInline(admin.TabularInline):
    model = RouteSubArea
    extra = 1
    fields = ["display_code", "name", "display_order"]


@admin.register(RouteArea)
class RouteAreaAdmin(admin.ModelAdmin):
    list_display = ["display_code", "name", "display_order"]
    list_editable = ["display_order"]
    inlines = [RouteSubAreaInline]


@admin.register(RouteSubArea)
class RouteSubAreaAdmin(admin.ModelAdmin):
    list_display = ["route_area", "display_code", "name", "display_order"]
    list_editable = ["display_order"]
    list_filter = ["route_area"]


@admin.register(Upashray)
class UpashrayAdmin(admin.ModelAdmin):
    list_display = ["name", "sub_area", "city", "contact_person", "mobile", "status"]
    list_filter = ["event", "sub_area__route_area", "status"]
    search_fields = ["name", "address", "contact_person", "mobile"]


admin.site.register(Event)
admin.site.register(EventManagerContact)
admin.site.register(Item)
admin.site.register(Volunteer)
admin.site.register(Sponsor)
admin.site.register(Vendor)
