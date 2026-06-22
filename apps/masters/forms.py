from django import forms
from django.utils.text import slugify

from apps.masters.models import Event, EventManagerContact, Item, Sponsor, Upashray, Vendor, Volunteer


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        self.current_event = current_event
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.SelectMultiple):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


def _build_unique_slug(name: str, instance=None) -> str:
    base_slug = slugify(name) or "event"
    slug = base_slug
    counter = 2
    qs = Event.objects.all()
    if instance and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


class EventCreateForm(BootstrapModelForm):
    class Meta:
        model = Event
        fields = ["name", "start_date", "end_date", "primary_contact_name", "primary_contact_mobile"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = _build_unique_slug(instance.name, instance=instance)
        if commit:
            instance.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return instance


class EventUpdateForm(BootstrapModelForm):
    class Meta:
        model = Event
        fields = [
            "name",
            "slug",
            "start_date",
            "end_date",
            "location",
            "primary_contact_name",
            "primary_contact_mobile",
            "status",
            "is_current",
            "is_active",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class EventManagerContactForm(BootstrapModelForm):
    class Meta:
        model = EventManagerContact
        fields = ["contact_name", "mobile", "email", "designation", "is_primary", "notes"]


class ItemForm(BootstrapModelForm):
    class Meta:
        model = Item
        fields = ["item_code", "item_name", "item_name_gu", "category", "unit", "default_size", "description", "estimated_rate"]


class UpashrayForm(BootstrapModelForm):
    class Meta:
        model = Upashray
        fields = ["name", "area", "address", "city", "contact_person", "mobile", "maharaj_name", "entry_date", "status"]
        widgets = {"entry_date": forms.DateInput(attrs={"type": "date"})}


class VolunteerForm(BootstrapModelForm):
    class Meta:
        model = Volunteer
        fields = ["name", "mobile", "email", "area", "vehicle_available", "remarks"]


class SponsorForm(BootstrapModelForm):
    def __init__(self, *args, current_event=None, **kwargs):
        super().__init__(*args, current_event=current_event, **kwargs)
        if current_event is not None:
            self.fields["reference_volunteer"].queryset = Volunteer.objects.filter(event=current_event, is_active=True)

    class Meta:
        model = Sponsor
        fields = ["sponsor_name", "mobile", "address", "organization", "reference_volunteer"]


class VendorForm(BootstrapModelForm):
    class Meta:
        model = Vendor
        fields = ["vendor_name", "contact_person", "mobile", "address", "gst_no", "remarks"]
