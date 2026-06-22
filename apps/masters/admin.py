from django.contrib import admin
from .models import Event, Item, Sponsor, Upashray, Vendor, Volunteer

admin.site.register(Event)
admin.site.register(Item)
admin.site.register(Upashray)
admin.site.register(Volunteer)
admin.site.register(Sponsor)
admin.site.register(Vendor)
