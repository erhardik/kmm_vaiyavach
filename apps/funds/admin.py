from django.contrib import admin
from .models import Donation, FundTransaction

admin.site.register(Donation)
admin.site.register(FundTransaction)
