from django.contrib import admin
from .models import RequirementHeader, RequirementLine, SpecialRequirement

admin.site.register(RequirementHeader)
admin.site.register(RequirementLine)
admin.site.register(SpecialRequirement)
