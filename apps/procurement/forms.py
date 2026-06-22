from django import forms

from apps.procurement.models import GoodsReceipt, PurchaseOrder, PurchaseOrderLine
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


class PurchaseOrderForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["vendor"].queryset = Vendor.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = PurchaseOrder
        fields = ["vendor", "po_number", "date", "status", "remarks"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}


class PurchaseOrderLineForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["purchase_order"].queryset = PurchaseOrder.objects.filter(event=current_event)
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ["purchase_order", "item", "qty", "rate", "tax_amount", "line_total"]


class GoodsReceiptForm(BootstrapModelForm):
    class Meta:
        model = GoodsReceipt
        fields = ["purchase_order", "date", "received_by", "remarks"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}
