from django import forms
from decimal import Decimal

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
        for field_name in (
            "volunteer_name",
            "pujya_shri_name",
            "pujya_shri_mobile",
            "current_address",
            "thana_count",
            "area",
            "chaturmas_place_address",
            "chaturmas_entry_date",
            "stay_type",
        ):
            if field_name in self.fields:
                self.fields[field_name].required = True
        for field_name in ("caretaker_name", "caretaker_mobile"):
            if field_name in self.fields:
                self.fields[field_name].required = False

    class Meta:
        model = RequirementHeader
        fields = [
            "upashray",
            "requirement_date",
            "remarks",
            "volunteer_name",
            "pujya_shri_name",
            "pujya_shri_mobile",
            "current_address",
            "thana_count",
            "area",
            "chaturmas_place_address",
            "chaturmas_entry_date",
            "caretaker_name",
            "caretaker_mobile",
            "stay_type",
            "status",
            "is_locked",
            "packed_by_name",
            "checked_by_name",
            "distributed_to_ms_by_name",
        ]
        widgets = {
            "requirement_date": forms.DateInput(attrs={"type": "date"}),
            "chaturmas_entry_date": forms.DateInput(attrs={"type": "date"}),
            "current_address": forms.Textarea(attrs={"rows": 2}),
            "chaturmas_place_address": forms.Textarea(attrs={"rows": 2}),
        }


class RequirementLineForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["requirement"].queryset = RequirementHeader.objects.filter(event=current_event)
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = RequirementLine
        fields = ["requirement", "item", "required_qty", "remarks"]


class RequirementCollectionHeaderForm(BootstrapModelForm):
    upashray_name = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if self.instance and getattr(self.instance, "pk", None) and self.instance.upashray_id:
            self.fields["upashray_name"].initial = self.instance.upashray.name
        for field_name in self.fields:
            if field_name != "upashray_name":
                self.fields[field_name].required = False

    class Meta:
        model = RequirementHeader
        fields = [
            "requirement_date",
            "remarks",
            "volunteer_name",
            "pujya_shri_name",
            "pujya_shri_mobile",
            "current_address",
            "thana_count",
            "area",
            "chaturmas_place_address",
            "chaturmas_entry_date",
            "caretaker_name",
            "caretaker_mobile",
            "stay_type",
        ]
        widgets = {
            "requirement_date": forms.DateInput(attrs={"type": "date"}),
            "chaturmas_entry_date": forms.DateInput(attrs={"type": "date"}),
            "current_address": forms.Textarea(attrs={"rows": 2}),
            "chaturmas_place_address": forms.Textarea(attrs={"rows": 2}),
            "remarks": forms.Textarea(attrs={"rows": 2}),
        }


class RequirementCollectionItemForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity_choices = [(str(index), str(index)) for index in range(0, 101)]
    required_qty = forms.TypedChoiceField(
        choices=quantity_choices,
        coerce=Decimal,
        required=False,
        initial=Decimal("0"),
        widget=forms.Select(attrs={"class": "form-select form-select-sm item-qty-select"}),
    )


class SpecialRequirementForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["upashray"].queryset = Upashray.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = SpecialRequirement
        fields = ["upashray", "description", "priority", "status", "photo"]
