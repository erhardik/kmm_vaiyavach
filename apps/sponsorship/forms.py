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
    sponsor_name = forms.CharField(max_length=200, label="Sponsor Name")

    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["item"].queryset = Item.objects.filter(event=current_event, is_active=True)
        if self.instance and getattr(self.instance, "sponsor_id", None):
            self.fields["sponsor_name"].initial = self.instance.sponsor.sponsor_name

    class Meta:
        model = SponsorshipCommitment
        fields = ["sponsor_name", "item", "committed_qty", "received_qty", "expected_date", "status", "remarks"]
        widgets = {"expected_date": forms.DateInput(attrs={"type": "date"})}

    def save(self, commit=True):
        instance = super().save(commit=False)
        sponsor_name = (self.cleaned_data.get("sponsor_name") or "").strip()
        if sponsor_name:
            sponsor = None
            if instance.pk and instance.sponsor_id:
                sponsor = instance.sponsor
                if sponsor.sponsor_name != sponsor_name:
                    sponsor = Sponsor.objects.filter(event=self.current_event, sponsor_name__iexact=sponsor_name).first()
            if sponsor is None:
                sponsor = Sponsor.objects.filter(event=self.current_event, sponsor_name__iexact=sponsor_name).first()
            if sponsor is None:
                sponsor = Sponsor(event=self.current_event, sponsor_name=sponsor_name)
            else:
                sponsor.sponsor_name = sponsor_name
            sponsor.save()
            instance.sponsor = sponsor
        if commit:
            instance.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return instance


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
