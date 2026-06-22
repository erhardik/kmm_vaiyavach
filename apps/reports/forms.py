from django import forms

from apps.masters.models import Event


class ReportScopeForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.none(), required=False)

    def __init__(self, *args, event_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event"].queryset = event_queryset or Event.objects.none()
        self.fields["event"].widget.attrs.update({"class": "form-select"})
