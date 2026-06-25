from collections import defaultdict
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.forms import formset_factory
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views import View
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.common.views import EventScopedCreateView, EventScopedDeleteView, EventScopedListView, EventScopedUpdateView
from apps.masters.models import Event, EventManagerContact, Item, ItemCategory
from apps.requirements.forms import (
    RequirementCollectionHeaderForm,
    RequirementCollectionItemForm,
    RequirementHeaderForm,
    RequirementLineForm,
    SpecialRequirementForm,
)
from apps.requirements.models import RequirementHeader, RequirementLine, RequirementStatus, SpecialRequirement
from apps.masters.models import Upashray


CATEGORY_LABELS = {
    "en": {
        ItemCategory.GENERAL: "General",
        ItemCategory.STATIONERY: "Stationery",
        ItemCategory.MEDICAL: "Medical",
        ItemCategory.AYURVEDIC: "Ayurvedic",
        ItemCategory.COLOR_MATERIAL: "Color Material",
    },
    "gu": {
        ItemCategory.GENERAL: "સામાન્ય",
        ItemCategory.STATIONERY: "સ્ટેશનરી",
        ItemCategory.MEDICAL: "મેડિકલ",
        ItemCategory.AYURVEDIC: "આયુર્વેદિક",
        ItemCategory.COLOR_MATERIAL: "રંગ સામગ્રી",
    },
}

CATEGORY_ROW_CLASSES = {
    ItemCategory.GENERAL: "cat-general",
    ItemCategory.STATIONERY: "cat-stationery",
    ItemCategory.MEDICAL: "cat-medical",
    ItemCategory.AYURVEDIC: "cat-ayurvedic",
    ItemCategory.COLOR_MATERIAL: "cat-color",
}

PDF_FONT_NAME = "Helvetica"
_pdf_font_candidates = [
    Path("C:/Windows/Fonts/shruti.ttf"),
    Path("C:/Windows/Fonts/Nirmala.ttc"),
]
for candidate in _pdf_font_candidates:
    if candidate.exists():
        try:
            pdfmetrics.registerFont(TTFont("KMMUnicode", str(candidate)))
            PDF_FONT_NAME = "KMMUnicode"
            break
        except Exception:
            pass

PDF_GUJARATI_FONT_NAME = PDF_FONT_NAME
for candidate in [Path("C:/Windows/Fonts/shruti.ttf"), Path("C:/Windows/Fonts/shrutib.ttf")]:
    if candidate.exists():
        try:
            pdfmetrics.registerFont(TTFont("KMMGujarati", str(candidate)))
            PDF_GUJARATI_FONT_NAME = "KMMGujarati"
            break
        except Exception:
            pass


def _lang_code(request):
    return (getattr(request, "LANGUAGE_CODE", None) or "en")[:2]


def _format_qty(value):
    if value is None:
        return "-"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric.is_integer():
        return str(int(numeric))
    return ("{:.3f}".format(numeric)).rstrip("0").rstrip(".")


def _format_pdf_date(value):
    if not value:
        return "-"
    month_names = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    return f"{value.day:02d}-{month_names[value.month - 1]}-{value.year}"


def _format_main_contact(event):
    if event is None:
        return "Main Event Manager: -"
    contact = EventManagerContact.objects.filter(event=event, is_primary=True).first()
    if contact:
        bits = [contact.contact_name or "-", contact.mobile or ""]
        contact_text = " | ".join(bit for bit in bits if bit)
        return f"Main Event Manager: {contact_text}"
    bits = [event.primary_contact_name or "-", event.primary_contact_mobile or ""]
    contact_text = " | ".join(bit for bit in bits if bit)
    return f"Main Event Manager: {contact_text}"


class RequirementHeaderListView(EventScopedListView):
    model = RequirementHeader
    template_name = "requirements/header_list.html"
    row_fields = ("order_number", "upashray", "requirement_date", "get_status_display", "is_locked", "remarks")
    headers = ["Order No.", "Upashray", "Date", "Status", "Locked", "Special Request / Note"]
    search_fields = ["order_number", "upashray__name", "remarks"]
    create_url_name = "requirements:collect"
    edit_url_name = "requirements:collect-edit"
    delete_url_name = "requirements:header-delete"
    detail_url_name = "requirements:header-detail"
    pdf_url_name = "requirements:collect-print"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Requirements"
        context["page_subtitle"] = "Collect new orders, review saved orders, and edit them when needed."
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context

    def get_queryset(self):
        return super().get_queryset().select_related("upashray")

    def get_table_rows(self):
        rows = []
        for obj in self.object_list:
            row_kwargs = self.get_row_url_kwargs(obj)
            rows.append(
                {
                    "object": obj,
                    "cells": [
                        getattr(obj, field)() if callable(getattr(obj, field)) else getattr(obj, field, "")
                        for field in self.row_fields
                    ],
                    "view_url": reverse(self.detail_url_name, kwargs=row_kwargs) if self.detail_url_name else "",
                    "pdf_url": reverse(self.pdf_url_name, kwargs=row_kwargs) if self.pdf_url_name else "",
                    "edit_url": reverse(self.edit_url_name, kwargs=row_kwargs) if self.edit_url_name else "",
                    "delete_url": reverse(self.delete_url_name, kwargs=row_kwargs) if self.delete_url_name else "",
                }
            )
        return rows


class RequirementCollectionView(View):
    template_name = "requirements/collect.html"
    confirm_required_fields = (
        "volunteer_name",
        "pujya_shri_name",
        "current_address",
        "thana_count",
        "area",
        "chaturmas_place_address",
        "chaturmas_entry_date",
        "stay_type",
    )

    def _get_event(self):
        event_token = self.kwargs.get("event_token") or self.request.GET.get("event_token") or self.request.POST.get("event_token")
        if event_token:
            return Event.objects.filter(public_form_token=event_token, is_active=True).first()
        event_id = self.request.GET.get("event") or self.request.POST.get("event") or self.kwargs.get("event_pk")
        if event_id:
            return Event.objects.filter(pk=event_id, is_active=True).first()
        return Event.objects.filter(is_current=True, is_active=True).first()

    def _get_header(self, event):
        token = self.kwargs.get("token") or self.request.POST.get("token") or self.request.GET.get("token")
        if token:
            return RequirementHeader.objects.filter(public_view_token=token, event=event).first()
        pk = self.kwargs.get("pk") or self.request.POST.get("header_pk") or self.request.GET.get("header_pk")
        if not pk or event is None:
            return None
        return RequirementHeader.objects.filter(pk=pk, event=event).first()

    def _editing_allowed(self, event, header, user):
        if header and header.status == RequirementStatus.SUBMITTED:
            if event and not event.allow_requirement_edit_after_confirm and not user.is_superuser:
                return False
        return True

    def _get_items(self, event):
        return list(Item.objects.filter(event=event, is_active=True).order_by("standard_serial", "pk"))

    def _resolve_upashray(self, event, upashray_name):
        name = (upashray_name or "").strip()
        if not name:
            existing = Upashray.objects.filter(event=event, is_active=True).order_by("name").first()
            if existing:
                return existing
            name = event.name
        upashray = Upashray.objects.filter(event=event, name__iexact=name, is_active=True).first()
        if upashray:
            return upashray
        return Upashray.objects.create(event=event, name=name)

    def _build_formset(self, items, data=None, initial_quantities=None, initial_remarks=None):
        collection_formset = formset_factory(RequirementCollectionItemForm, extra=0)
        initial_quantities = initial_quantities or {}
        initial_remarks = initial_remarks or {}
        initial = []
        for item in items:
            initial.append(
                {
                    "item_id": item.pk,
                    "required_qty": initial_quantities.get(item.pk, 0),
                    "remarks": initial_remarks.get(item.pk, ""),
                }
            )
        return collection_formset(data=data, initial=initial, prefix="items")

    def _build_rows(self, items, formset, language_code):
        rows = []
        for item, form in zip(items, formset.forms, strict=False):
            display_name = item.item_name_gu if language_code == "gu" and item.item_name_gu else item.item_name
            rows.append(
                {
                    "serial": item.standard_serial or item.pk,
                    "item": item,
                    "form": form,
                    "display_name": display_name,
                    "category_class": CATEGORY_ROW_CLASSES.get(item.category, "cat-general"),
                }
            )
        return rows

    def _group_rows(self, rows, language_code):
        grouped = []
        current_category = None
        current_group = None
        for row in rows:
            item = row["item"]
            if item.category != current_category:
                current_category = item.category
                current_group = {
                    "category": CATEGORY_LABELS.get(language_code, CATEGORY_LABELS["en"]).get(item.category, item.get_category_display()),
                    "category_class": CATEGORY_ROW_CLASSES.get(item.category, "cat-general"),
                    "rows": [],
                }
                grouped.append(current_group)
            current_group["rows"].append(row)
        return grouped

    def _build_context(self, request, event, header, form, formset, items):
        language_code = _lang_code(request)
        draft_key = f"kmm.requirements.collect.{event.pk if event else 'noevent'}.{header.pk if header else 'new'}"
        return {
            "event": event,
            "header": header,
            "form": form,
            "formset": formset,
            "item_groups": self._group_rows(self._build_rows(items, formset, language_code), language_code),
            "language_code": language_code,
            "page_title": "જરૂરિયાતો એકત્ર કરો" if language_code == "gu" else "Collect Requirements",
            "page_subtitle": "જથ્થો ભરો. સાચવો અને પછી એક જ ઓર્ડર પર ફરીથી સંપાદિત કરો."
            if language_code == "gu"
            else "Fill quantities, save once, and edit the same order later.",
            "list_url": reverse_lazy("requirements:header-list"),
            "can_save": bool(event),
            "order_number": header.order_number if header else None,
            "public_collect_url": reverse("requirements:public-collect", kwargs={"event_token": event.public_form_token}) if event else None,
            "public_pdf_url": reverse("requirements:public-print", kwargs={"token": header.public_view_token}) if header and header.order_number else None,
            "editing_allowed": self._editing_allowed(event, header, request.user),
            "event_requires_lock": bool(event and not event.allow_requirement_edit_after_confirm),
            "draft_storage_key": draft_key,
        }

    def _render_summary_html(self, request, header):
        return render_to_string(
            "requirements/_saved_order_summary.html",
            {
                "request": request,
                "header": header,
                "lang": _lang_code(request),
                "public_pdf_url": reverse("requirements:public-print", kwargs={"token": header.public_view_token}) if header and header.order_number else None,
            },
        )

    def get(self, request, *args, **kwargs):
        event = self._get_event()
        header = self._get_header(event) if event else None
        items = self._get_items(event) if event else []
        existing_quantities = {line.item_id: line.required_qty for line in header.lines.all()} if header else {}
        existing_remarks = {line.item_id: line.remarks for line in header.lines.all()} if header else {}
        form = RequirementCollectionHeaderForm(instance=header, current_event=event)
        formset = self._build_formset(items, initial_quantities=existing_quantities, initial_remarks=existing_remarks)
        return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        event = self._get_event()
        language_code = _lang_code(request)
        if event is None:
            messages.error(request, "સક્રિય ઇવેન્ટ મળી નથી." if language_code == "gu" else "No active event found.")
            return redirect(reverse_lazy("dashboard:home"))

        header = self._get_header(event)
        items = self._get_items(event)
        form = RequirementCollectionHeaderForm(request.POST, instance=header, current_event=event)
        existing_quantities = {line.item_id: line.required_qty for line in header.lines.all()} if header else {}
        existing_remarks = {line.item_id: line.remarks for line in header.lines.all()} if header else {}
        formset = self._build_formset(
            items,
            data=request.POST,
            initial_quantities=existing_quantities,
            initial_remarks=existing_remarks,
        )

        save_details_now = "save_details" in request.POST
        confirm_now = "confirm" in request.POST
        editing_allowed = self._editing_allowed(event, header, request.user)

        if not editing_allowed:
            messages.error(request, "This confirmed order is locked by admin.")
            return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))

        if header and header.is_locked and not request.user.is_superuser:
            messages.error(request, "This requirement order is locked.")
            return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))

        if save_details_now:
            if not form.is_valid():
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    payload = {
                        "ok": False,
                        "message": "Please fix the highlighted fields.",
                        "errors": form.errors.get_json_data(),
                    }
                    return JsonResponse(payload, status=400)
                return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))

            header_obj = form.save(commit=False)
            header_obj.event = event
            header_obj.requirement_date = form.cleaned_data.get("requirement_date") or timezone.localdate()
            header_obj.upashray = self._resolve_upashray(event, form.cleaned_data.get("upashray_name"))
            if header_obj.upashray is None:
                form.add_error("upashray_name", "Upashray name is required.")
                return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))

            header_obj.status = header.status if header else RequirementStatus.DRAFT
            header_obj.order_number = header.order_number if header else None
            header_obj.is_locked = header.is_locked if header else False
            header_obj.locked_at = header.locked_at if header else None
            header_obj.save()

            item_errors = []
            if formset.is_valid():
                RequirementLine.objects.filter(event=event, requirement=header_obj).delete()
                for item_form in formset.cleaned_data:
                    item_id = item_form.get("item_id")
                    qty = item_form.get("required_qty") or 0
                    note = item_form.get("remarks") or ""
                    if not item_id or qty <= 0:
                        continue
                    RequirementLine.objects.create(
                        event=event,
                        requirement=header_obj,
                        item_id=item_id,
                        required_qty=qty,
                        remarks=note,
                    )
            else:
                item_errors = formset.errors

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "ok": True,
                        "message": "Saved",
                        "header_pk": header_obj.pk,
                        "detail": "Basic details saved. You can continue filling items.",
                        "summary_html": self._render_summary_html(request, header_obj),
                        "item_errors": item_errors,
                    },
                )
            messages.success(request, "Basic details saved. You can continue filling items.")
            return render(request, self.template_name, self._build_context(request, event, header_obj, form, formset, items))

        if not form.is_valid() or not formset.is_valid():
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                payload = {
                    "ok": False,
                    "message": "Please fix the highlighted fields.",
                    "errors": form.errors.get_json_data(),
                }
                if not formset.is_valid():
                    payload["item_errors"] = formset.errors
                return JsonResponse(payload, status=400)
            return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))

        header_obj = form.save(commit=False)
        header_obj.event = event
        header_obj.requirement_date = form.cleaned_data.get("requirement_date") or timezone.localdate()
        header_obj.upashray = self._resolve_upashray(event, form.cleaned_data.get("upashray_name"))
        if header_obj.upashray is None:
            form.add_error("upashray_name", "Upashray name is required.")
            return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))
        if confirm_now:
            missing_fields = []
            for field_name in self.confirm_required_fields:
                value = form.cleaned_data.get(field_name)
                if value in (None, "", []):
                    form.add_error(field_name, "This field is required.")
                    missing_fields.append(field_name)
            if missing_fields:
                return render(request, self.template_name, self._build_context(request, event, header, form, formset, items))
            header_obj.status = RequirementStatus.SUBMITTED
        else:
            header_obj.status = header.status if header else RequirementStatus.DRAFT
            header_obj.order_number = header.order_number if header else None
            header_obj.is_locked = header.is_locked if header else False
            header_obj.locked_at = header.locked_at if header else None
        header_obj.save()

        RequirementLine.objects.filter(event=event, requirement=header_obj).delete()
        for item_form in formset.cleaned_data:
            item_id = item_form.get("item_id")
            qty = item_form.get("required_qty") or 0
            note = item_form.get("remarks") or ""
            if not item_id or qty <= 0:
                continue
            RequirementLine.objects.create(
                event=event,
                requirement=header_obj,
                item_id=item_id,
                required_qty=qty,
                remarks=note,
            )

        if confirm_now:
            messages.success(request, f"Requirement sent to team. Order No: {header_obj.order_number}")
            return redirect(reverse("requirements:header-list"))
        messages.success(request, "Data saved. Press Confirm to send Requirement to team.")
        return render(request, self.template_name, self._build_context(request, event, header_obj, form, formset, items))


class RequirementCollectionPrintView(View):
    def get(self, request, pk=None, token=None):
        query = RequirementHeader.objects.select_related("event", "upashray")
        if token is not None:
            header = query.filter(public_view_token=token).first()
        else:
            header = query.filter(pk=pk).first()
        if header is None:
            messages.error(request, "Requirement order not found.")
            return redirect(reverse_lazy("requirements:header-list"))

        items = list(
            RequirementLine.objects.filter(requirement=header)
            .select_related("item")
            .order_by("item__standard_serial", "item__pk")
        )
        language_code = _lang_code(request)
        return self._render_pdf(header, items, language_code)

    def _render_pdf(self, header, lines, language_code):
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "KMMTitle",
            parent=styles["Title"],
            fontName=PDF_FONT_NAME,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#14324f"),
            spaceAfter=6,
            alignment=TA_LEFT,
        )
        heading_style = ParagraphStyle(
            "KMMHeading",
            parent=styles["Heading2"],
            fontName=PDF_FONT_NAME,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#14324f"),
            alignment=TA_LEFT,
        )
        body_style = ParagraphStyle(
            "KMMBody",
            parent=styles["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
        )
        small_style = ParagraphStyle(
            "KMMSmall",
            parent=styles["BodyText"],
            fontName=PDF_FONT_NAME,
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
        )

        def p(text, style=body_style):
            parts = [escape(part) for part in str(text or "-").splitlines() or ["-"]]
            return Paragraph("<br/>".join(parts), style)

        story = [
            Paragraph("Requirement Order" if language_code != "gu" else "જરૂરિયાત ઓર્ડર", title_style),
            Paragraph(f"Order No.: {header.order_number}", heading_style),
            Spacer(1, 4),
        ]

        base_url = getattr(settings, "PUBLIC_SITE_URL", "").rstrip("/")
        if not base_url:
            base_url = "http://127.0.0.1:8000"
        qr_value = f"{base_url}{reverse('requirements:header-detail', kwargs={'pk': header.pk})}"
        qr_drawing = createBarcodeDrawing("QR", value=qr_value, barBorder=0, width=26 * mm, height=26 * mm)
        header_strip = Table(
            [
                [
                    [
                        Paragraph("Requirement Order" if language_code != "gu" else "àªœàª°à«‚àª°àª¿àª¯àª¾àª¤ àª“àª°à«àª¡àª°", title_style),
                        Paragraph(f"Order No.: {header.order_number}", heading_style),
                    ],
                    qr_drawing,
                ]
            ],
            colWidths=[150 * mm, 26 * mm],
        )
        header_strip.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        logo_path = Path(settings.BASE_DIR) / "pdf_header.png"
        logo_image = Image(str(logo_path), width=90 * mm, height=26.5 * mm) if logo_path.exists() else None
        gujarati_title_style = ParagraphStyle(
            "KMMGujaratiTitle",
            parent=title_style,
            fontName=PDF_GUJARATI_FONT_NAME,
        )
        brand_title = Paragraph("કલ્યાણ મિત્ર મંડળ", gujarati_title_style)
        order_label = Paragraph(f"Vaiyavachch laabh number: {header.order_number}", heading_style)
        if logo_image:
            brand_row = Table([[logo_image, qr_drawing]], colWidths=[150 * mm, 26 * mm])
        else:
            brand_row = Table([[brand_title, qr_drawing]], colWidths=[150 * mm, 26 * mm])
        brand_row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story = [brand_row, order_label, Spacer(1, 4)]

        status_table = Table(
            [
                [
                    p("[ ] All Items Packed" if language_code != "gu" else "[ ] àª¸àª°à«‡àª² àª†àª‡àªŸàª® àªªà«àª¯àª¾àª• àª¹àª¥àª¾", small_style),
                    p("[ ] Ready for Distribution" if language_code != "gu" else "[ ] àªµàª¿àª¤àª°àª£ àª®àª¾àªŸà«‡ àª¤à«ˆàª¯àª¾àª°", small_style),
                    p("Checked by: ____________________", small_style),
                ]
            ],
            colWidths=[55 * mm, 55 * mm, 74 * mm],
        )
        status_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#14324f")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9bb4c9")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), PDF_FONT_NAME),
                    ("LEADING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        basic_rows = [
            [
                p("Pujya Shri" if language_code != "gu" else "????? ????", small_style),
                p(header.pujya_shri_name, body_style),
                p("Current Address" if language_code != "gu" else "??????? ???????", small_style),
                p(header.current_address, body_style),
            ],
            [
                p("Thana" if language_code != "gu" else "????", small_style),
                p(header.thana_count, body_style),
                p("Area" if language_code != "gu" else "???????", small_style),
                p(header.area, body_style),
            ],
            [
                p("Chaturmas Place Address" if language_code != "gu" else "????????? ???? ???????", small_style),
                p(header.chaturmas_place_address, body_style),
                p("Chaturmas Entry Date" if language_code != "gu" else "????????? ?????? ?????", small_style),
                p(_format_pdf_date(header.chaturmas_entry_date), body_style),
            ],
            [
                p("Volunteer Name" if language_code != "gu" else "???????????????????????????????????? ?????????", small_style),
                p(header.volunteer_name, body_style),
                p("Stay Type" if language_code != "gu" else "?????? ??????", small_style),
                p(header.stay_type, body_style),
            ],
            [
                p("Care Taker Name" if language_code != "gu" else "??????????? ???", small_style),
                p(header.caretaker_name, body_style),
                p("Care Taker Contact" if language_code != "gu" else "??????????? ?????? ????", small_style),
                p(header.caretaker_mobile, body_style),
            ],
            [
                p("Special Request / Note" if language_code != "gu" else "??? ?????? / ????", small_style),
                p(header.remarks, body_style),
                p("", small_style),
                p("", body_style),
            ],
        ]
        basic_table = Table(basic_rows, colWidths=[28 * mm, 62 * mm, 35 * mm, 53 * mm])
        basic_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#14324f")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9bb4c9")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEADING", (0, 0), (-1, -1), 12),
                    ("FONTNAME", (0, 0), (-1, -1), PDF_FONT_NAME),
                ]
            )
        )
        story.append(status_table)
        story.append(Spacer(1, 8))
        story.extend([basic_table, Spacer(1, 8), Paragraph("Item List" if language_code != "gu" else "આઇટમ સૂચિ", heading_style)])

        table_data = [
            [
                p("Pack" if language_code != "gu" else "પેક", small_style),
                p("Sr. No." if language_code != "gu" else "ક્રમ નં.", small_style),
                p("Name of Item" if language_code != "gu" else "વસ્તુનું નામ", small_style),
                p("QTY Req" if language_code != "gu" else "જથ્થો", small_style),
                p("Remark" if language_code != "gu" else "નોંધ", small_style),
            ]
        ]
        for line in lines:
            item = line.item
            display_name = item.item_name_gu if language_code == "gu" and item.item_name_gu else item.item_name
            content = display_name
            if item.default_size:
                content = f"{display_name} ({item.default_size})"
            table_data.append([p("[ ]", small_style), p(item.standard_serial or item.pk), p(content), p(_format_qty(line.required_qty), body_style), p(line.remarks)])

        item_table = Table(table_data, colWidths=[14 * mm, 18 * mm, 78 * mm, 20 * mm, 48 * mm], repeatRows=1)
        item_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce9f5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#14324f")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#14324f")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9bb4c9")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), PDF_FONT_NAME),
                    ("LEADING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(item_table)

        footer_contact = _format_main_contact(header.event)

        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                page_count = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_footer(page_count)
                    super().showPage()
                super().save()

            def draw_footer(self, page_count):
                self.saveState()
                self.setStrokeColor(colors.HexColor("#9bb4c9"))
                self.setLineWidth(0.5)
                self.line(12 * mm, 14 * mm, A4[0] - 12 * mm, 14 * mm)
                self.setFont(PDF_FONT_NAME, 8)
                self.setFillColor(colors.HexColor("#14324f"))
                self.drawString(12 * mm, 8 * mm, footer_contact)
                self.drawRightString(A4[0] - 12 * mm, 8 * mm, f"Page {self._pageNumber} of {page_count}")
                self.restoreState()

        document.build(story, canvasmaker=NumberedCanvas)
        pdf_data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{header.order_number or "requirement-order"}.pdf"'
        response.write(pdf_data)
        return response


class RequirementCollectionDetailView(View):
    def get(self, request, pk=None, token=None):
        query = RequirementHeader.objects.select_related("event", "upashray")
        if token is not None:
            header = query.filter(public_view_token=token).first()
        else:
            header = query.filter(pk=pk).first()
        if header is None:
            return HttpResponse("Requirement order not found.", status=404)
        lines = list(
            RequirementLine.objects.filter(requirement=header)
            .select_related("item")
            .order_by("item__standard_serial", "item__pk")
        )
        return render(
            request,
            "requirements/header_detail.html" if request.headers.get("x-requested-with") == "XMLHttpRequest" else "requirements/header_detail_page.html",
            {
                "header": header,
                "lines": lines,
                "lang": _lang_code(request),
                "public_pdf_url": reverse("requirements:public-print", kwargs={"token": header.public_view_token}) if header.order_number else None,
            },
        )


class RequirementCollectByEventView(RequirementCollectionView):
    pass


class RequirementHeaderCreateView(EventScopedCreateView):
    model = RequirementHeader
    form_class = RequirementHeaderForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:header-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Requirement"
        context["list_url"] = self.success_url
        return context


class RequirementHeaderUpdateView(EventScopedUpdateView):
    model = RequirementHeader
    form_class = RequirementHeaderForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:header-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Requirement"
        context["list_url"] = self.success_url
        return context


class RequirementHeaderDeleteView(EventScopedDeleteView):
    model = RequirementHeader
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("requirements:header-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class RequirementLineListView(EventScopedListView):
    model = RequirementLine
    template_name = "common/list.html"
    row_fields = ("requirement", "item", "required_qty", "remarks")
    headers = ["Requirement", "Item", "Required Qty", "Remarks"]
    search_fields = ["requirement__upashray__name", "item__item_name", "remarks"]
    create_url_name = "requirements:line-create"
    edit_url_name = "requirements:line-update"
    delete_url_name = "requirements:line-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Requirement Lines"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class RequirementLineCreateView(EventScopedCreateView):
    model = RequirementLine
    form_class = RequirementLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Requirement Line"
        context["list_url"] = self.success_url
        return context


class RequirementLineUpdateView(EventScopedUpdateView):
    model = RequirementLine
    form_class = RequirementLineForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Requirement Line"
        context["list_url"] = self.success_url
        return context


class RequirementLineDeleteView(EventScopedDeleteView):
    model = RequirementLine
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("requirements:line-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context


class SpecialRequirementListView(EventScopedListView):
    model = SpecialRequirement
    template_name = "common/list.html"
    row_fields = ("upashray", "get_priority_display", "get_status_display", "description")
    headers = ["Upashray", "Priority", "Status", "Description"]
    search_fields = ["upashray__name", "description"]
    create_url_name = "requirements:special-create"
    edit_url_name = "requirements:special-update"
    delete_url_name = "requirements:special-delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Special Requirements"
        context["create_url"] = reverse_lazy(self.create_url_name)
        return context


class SpecialRequirementCreateView(EventScopedCreateView):
    model = SpecialRequirement
    form_class = SpecialRequirementForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:special-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Special Requirement"
        context["list_url"] = self.success_url
        return context


class SpecialRequirementUpdateView(EventScopedUpdateView):
    model = SpecialRequirement
    form_class = SpecialRequirementForm
    template_name = "common/form.html"
    success_url = reverse_lazy("requirements:special-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Update Special Requirement"
        context["list_url"] = self.success_url
        return context


class SpecialRequirementDeleteView(EventScopedDeleteView):
    model = SpecialRequirement
    template_name = "common/confirm_delete.html"
    success_url = reverse_lazy("requirements:special-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_url"] = self.success_url
        return context
