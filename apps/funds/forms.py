from django import forms

from apps.funds.models import Donation, FundTransaction


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


class DonationForm(BootstrapModelForm):
    class Meta:
        model = Donation
        fields = ["donor_name", "mobile", "amount", "mode", "reference_person", "received_date", "remarks"]
        widgets = {"received_date": forms.DateInput(attrs={"type": "date"})}


class FundTransactionForm(BootstrapModelForm):
    class Meta:
        model = FundTransaction
        fields = ["transaction_type", "category", "amount", "date", "remarks", "reference_module", "reference_id"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}
