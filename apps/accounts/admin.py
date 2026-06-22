from django.contrib import admin
from .models import EventMembership, UserProfile

admin.site.register(UserProfile)
admin.site.register(EventMembership)
