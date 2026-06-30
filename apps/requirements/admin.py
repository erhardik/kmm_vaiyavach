from django.contrib import admin
from .models import EditRequest, RequirementHeader, RequirementLine, SpecialRequirement, ViewControl

admin.site.register(RequirementHeader)
admin.site.register(RequirementLine)
admin.site.register(SpecialRequirement)
admin.site.register(EditRequest)
admin.site.register(ViewControl)
