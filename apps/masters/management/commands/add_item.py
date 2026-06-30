from django.core.management.base import BaseCommand
from django.db import models
from apps.masters.models import Event, Item


class Command(BaseCommand):
    help = "Add a new item or variant from the bash console"

    def add_arguments(self, parser):
        parser.add_argument("item_code", help="Item code (e.g. STA003)")
        parser.add_argument("item_name", help="Item name in English")
        parser.add_argument("--gu", help="Item name in Gujarati", default="")
        parser.add_argument("--category", default="GENERAL", choices=["GENERAL", "STATIONERY", "MEDICAL", "AYURVEDIC", "COLOR_MATERIAL"])
        parser.add_argument("--unit", default="", help="Unit (Piece, Gram, Meter...)")
        parser.add_argument("--size", default="", help="Default size in English")
        parser.add_argument("--size-gu", default="", help="Default size in Gujarati")
        parser.add_argument("--serial", type=int, default=0, help="Standard serial for ordering")
        parser.add_argument("--variant-of", default="", help="Parent item code (makes this a variant)")
        parser.add_argument("--variant-name", default="", help="Variant name in English")
        parser.add_argument("--variant-name-gu", default="", help="Variant name in Gujarati")
        parser.add_argument("--rate", type=float, default=0, help="Estimated rate")
        parser.add_argument("--event", type=int, default=0, help="Event ID (defaults to current event)")

    def handle(self, *args, **options):
        event_qs = Event.objects.filter(is_active=True)
        if options["event"]:
            event = event_qs.filter(pk=options["event"]).first()
        else:
            event = event_qs.filter(is_current=True).first()
        if not event:
            self.stderr.write(self.style.ERROR("No active event found"))
            return

        parent = None
        if options["variant_of"]:
            parent = Item.objects.filter(event=event, item_code=options["variant_of"]).first()
            if not parent:
                self.stderr.write(self.style.ERROR(f"Parent item '{options['variant_of']}' not found"))
                return

        serial = options["serial"]
        if not serial and not parent:
            max_serial = Item.objects.filter(event=event).aggregate(models.Max("standard_serial"))["standard_serial__max"] or 0
            serial = max_serial + 1

        item = Item(
            event=event,
            item_code=options["item_code"],
            item_name=options["item_name"],
            item_name_gu=options["gu"],
            category=options["category"],
            unit=options["unit"],
            default_size=options["size"],
            default_size_gu=options["size_gu"],
            standard_serial=serial,
            parent_item=parent,
            variant_name=options["variant_name"],
            variant_name_gu=options["variant_name_gu"],
            estimated_rate=options["rate"],
            is_active=True,
        )
        item.save()
        label = f"variant of {parent.item_code}" if parent else "base item"
        self.stdout.write(self.style.SUCCESS(f"Created {options['item_code']} ({label}) with serial {serial}"))
