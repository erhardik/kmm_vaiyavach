from django import forms

from apps.inventory.models import InventoryBalance, InventoryTransaction, PurchaseLot
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


class InventoryTransactionForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, user=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)
        if user and user.is_authenticated and user.groups.filter(name="KMM Manager").exists():
            self.fields.pop("unit_rate", None)

    class Meta:
        model = InventoryTransaction
        fields = [
            "item",
            "transaction_type",
            "qty",
            "source_module",
            "reference_id",
            "reference_label",
            "unit_rate",
            "remarks",
            "reversal_of",
        ]


class InventoryBalanceForm(BootstrapModelForm):
    class Meta:
        model = InventoryBalance
        fields = ["item", "current_stock", "reserved_stock", "available_stock", "distributed_stock"]


class PurchaseLotLineForm(forms.Form):
    qty = forms.DecimalField(max_digits=12, decimal_places=3, label="Qty")
    unit_rate = forms.DecimalField(max_digits=14, decimal_places=2, label="Rate", initial=0)
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.none(), required=False, label="Vendor")
    notes = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={"placeholder": "Notes"}))

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        if event is not None:
            self.fields["vendor"].queryset = Vendor.objects.filter(event=event, is_active=True)


class PurchaseEntryForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.none(), label="Item")

    def __init__(self, *args, event=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if event is not None:
            self.fields["item"].queryset = Item.objects.filter(event=event, is_active=True).order_by("standard_serial", "pk")
        if user and user.is_authenticated and user.groups.filter(name="KMM Manager").exists():
            pass  # Manager can see all fields for purchase entry
