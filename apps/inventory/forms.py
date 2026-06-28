from django import forms

from apps.inventory.models import InventoryBalance, InventoryTransaction
from apps.masters.models import Item


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
