from django import forms

from apps.sponsorship.models import SponsorMaterialReceipt, SponsorshipCommitment
from apps.masters.models import Item, Sponsor


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


class SponsorshipCommitmentForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["sponsor"].queryset = Sponsor.objects.filter(event=current_event, is_active=True)
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = SponsorshipCommitment
        fields = ["sponsor", "item", "committed_qty", "received_qty", "expected_date", "status", "remarks"]
        widgets = {"expected_date": forms.DateInput(attrs={"type": "date"})}


class SponsorMaterialReceiptForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["commitment"].queryset = SponsorshipCommitment.objects.filter(event=current_event)
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = SponsorMaterialReceipt
        fields = ["commitment", "item", "received_qty", "received_date", "received_by", "remarks"]
        widgets = {"received_date": forms.DateInput(attrs={"type": "date"})}
