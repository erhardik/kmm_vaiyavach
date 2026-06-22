from django import forms

from apps.masters.models import Event, ItemCategory


class ItemControlFilterForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.none(), required=False)
    category = forms.ChoiceField(required=False)
    pending_only = forms.BooleanField(required=False)
    fully_covered = forms.BooleanField(required=False)
    shortage = forms.BooleanField(required=False)

    def __init__(self, *args, event_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event"].queryset = event_queryset or Event.objects.none()
        self.fields["category"].choices = [("", "All Categories")] + list(ItemCategory.choices)
        self.fields["event"].widget.attrs.update({"class": "form-select"})
        self.fields["category"].widget.attrs.update({"class": "form-select"})
        self.fields["pending_only"].widget.attrs.update({"class": "form-check-input"})
        self.fields["fully_covered"].widget.attrs.update({"class": "form-check-input"})
        self.fields["shortage"].widget.attrs.update({"class": "form-check-input"})
