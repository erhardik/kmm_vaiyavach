from django import forms

from apps.distribution.models import DistributionBatch, DistributionLine
from apps.masters.models import Item, Upashray, Volunteer


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


class DistributionBatchForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["assigned_volunteer"].queryset = Volunteer.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = DistributionBatch
        fields = ["batch_name", "date", "assigned_volunteer", "status", "remarks"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class DistributionLineForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["distribution_batch"].queryset = DistributionBatch.objects.filter(event=current_event)
            self.fields["upashray"].queryset = Upashray.objects.filter(event=current_event, is_active=True)
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = DistributionLine
        fields = ["distribution_batch", "upashray", "item", "required_qty", "dispatched_qty", "delivered_qty", "balance_qty", "status"]
