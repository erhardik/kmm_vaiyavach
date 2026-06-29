from django.contrib import admin
from .models import EditRequest, RequirementHeader, RequirementLine, SpecialRequirement

admin.site.register(RequirementHeader)
admin.site.register(RequirementLine)
admin.site.register(SpecialRequirement)
admin.site.register(EditRequest)
