import uuid

from django.db import models

from config.models import EventScopedModel, TimeStampedModel


class EventStatus(models.TextChoices):
    PLANNING = "PLANNING", "Planning"
    REQUIREMENT_PENDING = "REQUIREMENT_PENDING", "Requirement Pending"
    REQUIREMENT_RECEIVED = "REQUIREMENT_RECEIVED", "Requirement Received"
    PROCUREMENT_IN_PROGRESS = "PROCUREMENT_IN_PROGRESS", "Procurement In Progress"
    DISTRIBUTION_PENDING = "DISTRIBUTION_PENDING", "Distribution Pending"
    COMPLETED = "COMPLETED", "Completed"


class ItemCategory(models.TextChoices):
    GENERAL = "GENERAL", "General"
    STATIONERY = "STATIONERY", "Stationery"
    MEDICAL = "MEDICAL", "Medical"
    AYURVEDIC = "AYURVEDIC", "Ayurvedic"
    COLOR_MATERIAL = "COLOR_MATERIAL", "Color Material"


class UpashrayStatus(models.TextChoices):
    PLANNING = "PLANNING", "Planning"
    REQUIREMENT_PENDING = "REQUIREMENT_PENDING", "Requirement Pending"
    REQUIREMENT_RECEIVED = "REQUIREMENT_RECEIVED", "Requirement Received"
    PROCUREMENT_IN_PROGRESS = "PROCUREMENT_IN_PROGRESS", "Procurement In Progress"
    DISTRIBUTION_PENDING = "DISTRIBUTION_PENDING", "Distribution Pending"
    COMPLETED = "COMPLETED", "Completed"


class Event(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    public_form_token = models.UUIDField(default=None, null=True, blank=True, unique=True, editable=False)
    allow_requirement_edit_after_confirm = models.BooleanField(default=True)
    location = models.CharField(max_length=200, blank=True)
    primary_contact_name = models.CharField(max_length=120, blank=True, default="")
    primary_contact_mobile = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(max_length=40, choices=EventStatus.choices, default=EventStatus.PLANNING)
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.public_form_token:
            self.public_form_token = uuid.uuid4()
        super().save(*args, **kwargs)


class EventManagerContact(EventScopedModel):
    contact_name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    designation = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "contact_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["event"],
                condition=models.Q(is_primary=True),
                name="unique_primary_event_manager_contact",
            ),
        ]

    def __str__(self) -> str:
        return self.contact_name

    def primary_label(self) -> str:
        return "Yes" if self.is_primary else "No"


class Item(EventScopedModel):
    parent_item = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="variants")
    standard_serial = models.PositiveIntegerField(default=0)
    item_code = models.CharField(max_length=50)
    item_name = models.CharField(max_length=200)
    item_name_gu = models.CharField(max_length=200, blank=True)
    variant_name = models.CharField(max_length=120, blank=True, default="")
    variant_name_gu = models.CharField(max_length=120, blank=True, default="")
    category = models.CharField(max_length=40, choices=ItemCategory.choices)
    unit = models.CharField(max_length=40, blank=True)
    default_size = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    estimated_rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["standard_serial", "item_name"]
        constraints = [
            models.UniqueConstraint(fields=["event", "standard_serial"], name="unique_event_item_standard_serial"),
            models.UniqueConstraint(fields=["event", "item_code"], name="unique_event_item_code"),
            models.UniqueConstraint(fields=["event", "parent_item", "variant_name"], name="unique_event_item_variant_name"),
        ]
        indexes = [
            models.Index(fields=["event", "category"]),
            models.Index(fields=["event", "standard_serial"]),
            models.Index(fields=["event", "item_name"]),
        ]

    def __str__(self) -> str:
        return self.item_name

    def display_name(self) -> str:
        if self.parent_item_id:
            base = self.parent_item.item_name_gu if self.parent_item.item_name_gu else self.parent_item.item_name
            variant = self.variant_name_gu or self.variant_name or ""
            return f"{base} - {variant}" if variant else base
        if self.item_name_gu:
            return f"{self.item_name} / {self.item_name_gu}"
        return self.item_name


class Upashray(EventScopedModel):
    name = models.CharField(max_length=200)
    area = models.CharField(max_length=120, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    contact_person = models.CharField(max_length=120, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    maharaj_name = models.CharField(max_length=120, blank=True)
    entry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=40, choices=UpashrayStatus.choices, default=UpashrayStatus.PLANNING)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["event", "name"], name="unique_event_upashray_name"),
        ]

    def __str__(self) -> str:
        return self.name


class Volunteer(EventScopedModel):
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    area = models.CharField(max_length=120, blank=True)
    vehicle_available = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Sponsor(EventScopedModel):
    sponsor_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    organization = models.CharField(max_length=200, blank=True)
    reference_volunteer = models.ForeignKey(Volunteer, on_delete=models.SET_NULL, null=True, blank=True, related_name="referred_sponsors")

    class Meta:
        ordering = ["sponsor_name"]

    def __str__(self) -> str:
        return self.sponsor_name


class Vendor(EventScopedModel):
    vendor_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=120, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    gst_no = models.CharField(max_length=40, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["vendor_name"]

    def __str__(self) -> str:
        return self.vendor_name
