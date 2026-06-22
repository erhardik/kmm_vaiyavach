from django import forms

from apps.vendors.models import VendorQuote
from apps.masters.models import Item, Vendor


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


class VendorQuoteForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["vendor"].queryset = Vendor.objects.filter(event=current_event, is_active=True)
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = VendorQuote
        fields = [
            "vendor",
            "item",
            "rate",
            "home_delivery",
            "pickup_available",
            "return_unused",
            "credit_days",
            "gst_included",
            "quote_date",
            "remarks",
        ]
        widgets = {"quote_date": forms.DateInput(attrs={"type": "date"})}
