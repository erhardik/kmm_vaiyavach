from django import forms
from django.utils.text import slugify

from apps.masters.models import Event, EventManagerContact, Item, JourneyCard, Sponsor, Upashray, Vendor, Volunteer


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
            "allow_requirement_edit_after_confirm",
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
    add_to_current_form_immediately = forms.BooleanField(
        required=False,
        initial=True,
        label="Add in Current event form immediately",
        help_text="If checked, the item becomes active right away and appears at the end of the current event forms.",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields.pop("add_to_current_form_immediately", None)
            self.fields["is_active"].label = "Active"
            self.fields["is_active"].help_text = "If deactivated, item will be hidden from requirement forms."
            if self.instance.parent_item_id:
                self.fields.pop("default_size", None)
                self.fields.pop("default_size_gu", None)
            else:
                self.fields.pop("variant_name", None)
                self.fields.pop("variant_name_gu", None)
        else:
            self.fields.pop("is_active")
            self.fields.pop("variant_name", None)
            self.fields.pop("variant_name_gu", None)
        if user and user.is_authenticated and user.groups.filter(name="KMM Manager").exists():
            self.fields.pop("estimated_rate", None)

    class Meta:
        model = Item
        fields = ["item_code", "item_name", "item_name_gu", "variant_name", "variant_name_gu", "category", "unit", "default_size", "default_size_gu", "description", "estimated_rate", "is_active"]


class UpashrayForm(BootstrapModelForm):
    class Meta:
        model = Upashray
        fields = ["name", "area", "sub_area", "address", "city", "contact_person", "mobile", "maharaj_name", "entry_date", "status"]
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


class JourneyCardForm(BootstrapModelForm):
    class Meta:
        model = JourneyCard
        fields = ["year", "month", "title", "description", "category"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["year"].help_text = "ઈવેન્ટનું વર્ષ લખો, દા.ત. 2024. (નોંધ: કૃપા કરીને બધું ગુજરાતીમાં લખો.)"
        self.fields["month"].help_text = (
            "મહિનો અથવા તારીખોની રેન્જ ગુજરાતીમાં લખો, દા.ત. 'ફેબ્રુઆરી' અથવા 'જૂન–જુલાઈ'. "
            "લેન્ડિંગ પેજની ટાઈમલાઈનમાં કાર્ડ મહિના-વર્ષના ક્રમમાં ગોઠવાશે."
        )
        self.fields["title"].help_text = (
            "હેડિંગ ગુજરાતીમાં લખો. મહત્તમ 200 અક્ષર — કાર્ડની પહોળાઈ સાચવવા માટે ટૂંકું રાખો."
        )
        self.fields["description"].help_text = (
            "વર્ણન ગુજરાતીમાં લખો. મહત્તમ 600 અક્ષર (લગભગ 30 શબ્દો) — "
            "જેથી કાર્ડની ઊંચાઈ-પહોળાઈ હાલના કાર્ડ જેટલી જ રહે."
        )
