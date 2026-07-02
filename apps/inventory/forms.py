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
    item = forms.ChoiceField(choices=[], label="Item")

    def __init__(self, *args, event=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "Select item...")]
        for base in base_items:
            variants = list(base.variants.filter(is_active=True).order_by("item_code", "pk"))
            if variants:
                for vi, variant in enumerate(variants):
                    suffix = chr(ord('A') + vi) if vi < 26 else f"X{vi+1}"
                    serial = f"{base.standard_serial or base.pk}-{suffix}"
                    name = variant.display_name()
                    type_size = variant.variant_name_gu or variant.variant_name or variant.default_size_gu or variant.default_size or ""
                    label = f"{serial} - {name}"
                    if type_size:
                        label += f" - {type_size}"
                    choices.append((variant.pk, label))
            else:
                serial = str(base.standard_serial or base.pk)
                name = base.display_name()
                type_size = base.default_size_gu or base.default_size or ""
                label = f"{serial} - {name}"
                if type_size:
                    label += f" - {type_size}"
                choices.append((base.pk, label))
        self.fields["item"].choices = choices

    def clean_item(self):
        value = self.cleaned_data["item"]
        try:
            item = Item.objects.get(pk=value)
            if not item.is_active:
                raise forms.ValidationError("This item is deactivated and cannot be used.")
        except Item.DoesNotExist:
            raise forms.ValidationError("Invalid item selected.")
        return item
