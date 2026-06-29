import re
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from config.models import EventScopedModel


class RequirementStatus(models.TextChoices):
    DRAFT = "DRAFT", "Open"
    NOT_CONFIRMED = "NOT_CONFIRMED", "Not Confirmed"
    CONFIRMED = "CONFIRMED", "Confirmed"
    SUBMITTED = "SUBMITTED", "Pending"
    PACKED = "PACKED", "Packed"
    IN_PROGRESS = "IN_PROGRESS", "Packing done"
    DELIVERED = "DELIVERED", "Delivered"
    CLOSED = "CLOSED", "On route"
    CANCELLED = "CANCELLED", "Rejected by M.S."
    RETURN_REQUESTED = "RETURN_REQUESTED", "Return Requested"
    RETURN_DONE = "RETURN_DONE", "Return Done"
    RECEIVED_BY_MS = "RECEIVED_BY_MS", "Recieved by M.S."


class PriorityLevel(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


class RequirementHeader(EventScopedModel):
    class StayType(models.TextChoices):
        SANGH_UPASHRAY = "SANGH_UPASHRAY", "Sangh Upashray"
        STHIRVAS = "STHIRVAS", "Sthirvas"

    class RouteAreaChoices(models.TextChoices):
        A1 = "A1", "Area-1 City-ReliefRoad"
        A2 = "A2", "Area-2 Shahpur-Usmanpura"
        A3 = "A3", "Area-3 Naranpura-Thaltej"
        A4 = "A4", "Area-4 Vadaj Subhashbridge"
        A5 = "A5", "Area-5 KrishnaNagar-Naroda"
        A6 = "A6", "Area-6 Jivrajpark-Satellite"
        A7 = "A7", "Area-7 Vasna-New Vasna"
        A8 = "A8", "Area-8 Paldi-ChandraNagar"
        A9 = "A9", "Area-9 Shahibag"
        A10 = "A10", "Area-10 Sabarmati-Chandkheda"
        A11 = "A11", "Area-11 Other Areas"
        NOT_IN_LIST = "NOT_IN_LIST", "NOT IN LIST"

    SUB_ROUTE_CHOICES = {
        "A1": [
            ("1-A", "1-A - આસ્ટોડિયા / માણેકચોક"),
            ("1-B", "1-B - ગાંધી રોડ / રિલીફ રોડ"),
        ],
        "A2": [
            ("2-A", "2-A - શાહપુર / ખાનપુર"),
            ("2-B", "2-B - ઉસ્માનપુરા / શાંતિનગર / નવરંગપુરા"),
        ],
        "A3": [
            ("3-A", "3-A - નહેરુનગર / દાદાસાહેબ પગલા"),
            ("3-B", "3-B - દેવકીનંદન / મીરાંબિકા / અંકુર / વિજયનગર"),
            ("3-C", "3-C - ઝવેરી પાર્ક / નારણપુરા"),
            ("3-D", "3-D - પારસનગર / ચિત્રકૂટ / પ્રગતિનગર / પારુલનગર"),
            ("3-E", "3-E - નિર્ણયનગર / ચાણક્યપુરી / ઘાટલોડિયા / સત્તાધાર / થલતેજ / ગુરુકુળ"),
        ],
        "A4": [
            ("4-A", "4-A - નવા-જુના વાડજ / નંદનવન / તુલસીશ્યામ / સુભાષ બ્રિજ"),
        ],
        "A5": [
            ("5-A", "5-A - કૃષ્ણનગર / નરોડા"),
            ("5-B", "5-B - મહાસુખનગર / બાપુનગર / સરસપુર"),
            ("5-C", "5-C - ઓઢવ / નિકોલ / જનતાનગર / ઇસનપુર"),
        ],
        "A6": [
            ("6-A", "6-A - સેટેલાઈટ / જીવરાજપાર્ક / વેજલપુર"),
            ("6-B", "6-B - વસ્ત્રાપુર / S.G. Highway / પ્રેરણાતીર્થ"),
        ],
        "A7": [
            ("7-A", "7-A - ગોદાવરી / આયોજનનગર"),
            ("7-B", "7-B - વાસણા / નવકાર / ન્યૂ વાસણા"),
            ("7-C", "7-C - શાંતિવન / રંગસાગર"),
            ("7-D", "7-D - જૈન મર્ચન્ટ / લક્ષ્મીવિહાર"),
        ],
        "A8": [
            ("8-A", "8-A - ઓપેરા"),
            ("8-B", "8-B - વસંતકુંજ / જૈનનગર / પરિમલ"),
            ("8-C", "8-C - વિકાસગૃહ રોડ"),
            ("8-D", "8-D - દશાપોરવાડ"),
            ("8-E", "8-E - જૈન સોસાયટી / કુંથુનાથ"),
            ("8-F", "8-F - પંકજ / રાજનગર"),
        ],
        "A9": [
            ("9-A", "9-A - શાહીબાગ / ગિરધરનગર / હઠીસિંહની વાડી"),
        ],
        "A10": [
            ("10-A", "10-A - સાબરમતી / રાણીપ / ચાંદખેડા / રામોલ"),
        ],
        "A11": [
            ("11-A", "11-A - મણીનગર / કાંકરિયા"),
            ("11-B", "11-B - બોપલ / ગોતા / અદાણી શાંતિગ્રામ"),
            ("11-C", "11-C - સરખેજ / સાણંદ"),
            ("11-D", "11-D - બરોડા"),
        ],
    }

    @classmethod
    def get_all_sub_route_choices(cls):
        choices = []
        for area_choices in cls.SUB_ROUTE_CHOICES.values():
            choices.extend(area_choices)
        choices.append(("NOT_IN_LIST", "NOT IN LIST"))
        return choices

    order_number = models.CharField(max_length=32, unique=False, editable=False, null=True, blank=True, verbose_name="Order ID")
    form_number = models.CharField(max_length=32, blank=True, default="", verbose_name="Form No.")
    public_view_token = models.UUIDField(default=None, null=True, blank=True, unique=True, editable=False)
    upashray = models.ForeignKey("masters.Upashray", on_delete=models.PROTECT, related_name="requirements")
    requirement_date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)
    volunteer_name = models.CharField(max_length=120, blank=True, default="")
    volunteer_mobile = models.CharField(max_length=20, blank=True, default="")
    route_area = models.CharField(max_length=20, blank=True, default="", choices=RouteAreaChoices.choices)
    route_sub_area = models.CharField(max_length=80, blank=True, default="")
    pujya_shri_name = models.CharField(max_length=120, blank=True, default="")
    pujya_shri_mobile = models.CharField(max_length=20, blank=True, default="")
    current_address = models.TextField(blank=True, default="")
    thana_count = models.PositiveIntegerField(null=True, blank=True)
    area = models.CharField(max_length=120, blank=True, default="")
    chaturmas_place_address = models.TextField(blank=True, default="")
    chaturmas_entry_date = models.DateField(null=True, blank=True)
    caretaker_name = models.CharField(max_length=120, blank=True, default="")
    caretaker_mobile = models.CharField(max_length=20, blank=True, default="")
    stay_type = models.CharField(max_length=20, choices=StayType.choices, blank=True, default=StayType.STHIRVAS)
    status = models.CharField(max_length=30, choices=RequirementStatus.choices, default=RequirementStatus.DRAFT)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    packing_stock_applied_at = models.DateTimeField(null=True, blank=True)
    packed_by_name = models.CharField(max_length=120, blank=True, default="")
    checked_by_name = models.CharField(max_length=120, blank=True, default="")
    distributed_to_ms_by_name = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-updated_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "order_number"], name="unique_event_order_number"),
        ]

    def __str__(self) -> str:
        if self.form_number:
            return self.form_number
        if self.order_number:
            return self.order_number
        return "(draft)"

    def save(self, *args, **kwargs):
        if not self.public_view_token:
            self.public_view_token = uuid.uuid4()
        if not self.order_number and self.status in (RequirementStatus.SUBMITTED, RequirementStatus.CONFIRMED):
            raw_area = (self.route_area or "").strip()
            if raw_area == "NOT_IN_LIST" or not raw_area:
                raw_area = "A11"
            area_num = int(raw_area[1:])
            name_part = re.sub(r"[^A-Z0-9]", "", self.volunteer_name.strip().upper())[:10] or "UNKNOWN"
            date_part = timezone.localdate().strftime("%d%m%y")
            seq = RequirementHeader.objects.filter(event=self.event, status=RequirementStatus.SUBMITTED).count() + 1
            self.order_number = f"A{area_num:02d}-{name_part}-{date_part}-{seq:03d}"
        super().save(*args, **kwargs)


class RequirementLine(EventScopedModel):
    requirement = models.ForeignKey(RequirementHeader, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("masters.Item", on_delete=models.PROTECT, related_name="requirement_lines")
    required_qty = models.DecimalField(max_digits=12, decimal_places=3)
    remarks = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["requirement", "item"], name="unique_requirement_item"),
        ]

    def __str__(self) -> str:
        return f"{self.requirement} - {self.item}"


class SpecialRequirement(EventScopedModel):
    upashray = models.ForeignKey("masters.Upashray", on_delete=models.PROTECT, related_name="special_requirements")
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PriorityLevel.choices, default=PriorityLevel.MEDIUM)
    status = models.CharField(max_length=30, choices=RequirementStatus.choices, default=RequirementStatus.DRAFT)
    photo = models.FileField(upload_to="requirements/photos/", blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.upashray} - {self.priority}"


class EditRequest(EventScopedModel):
    header = models.ForeignKey(RequirementHeader, on_delete=models.CASCADE, related_name="edit_requests")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"EditRequest for {self.header} - {'Resolved' if self.is_resolved else 'Pending'}"

