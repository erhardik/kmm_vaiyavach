from django import forms

from apps.requirements.models import PriorityLevel, RequirementHeader, RequirementLine, SpecialRequirement
from apps.masters.models import Upashray, Item


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        self.current_event = current_event
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class RequirementHeaderForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["upashray"].queryset = Upashray.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = RequirementHeader
        fields = ["upashray", "requirement_date", "remarks", "status"]
        widgets = {"requirement_date": forms.DateInput(attrs={"type": "date"})}


class RequirementLineForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["requirement"].queryset = RequirementHeader.objects.filter(event=current_event)
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = RequirementLine
        fields = ["requirement", "item", "required_qty", "remarks"]


class SpecialRequirementForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["upashray"].queryset = Upashray.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = SpecialRequirement
        fields = ["upashray", "description", "priority", "status", "photo"]
