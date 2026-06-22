from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import re
import unicodedata

from django.core.management.base import BaseCommand, CommandError

from apps.masters.models import Event, Item, ItemCategory


SECTION_CATEGORY_MAP = {
    "general items": ItemCategory.GENERAL,
    "general utility items": ItemCategory.GENERAL,
    "stationery": ItemCategory.STATIONERY,
    "medical": ItemCategory.MEDICAL,
    "medical items": ItemCategory.MEDICAL,
    "ayurvedic medicines": ItemCategory.AYURVEDIC,
    "utensil coloring materials": ItemCategory.COLOR_MATERIAL,
    "utility items": ItemCategory.GENERAL,
    "other useful items": ItemCategory.GENERAL,
}

CATEGORY_PREFIX_MAP = {
    ItemCategory.GENERAL: "GEN",
    ItemCategory.STATIONERY: "STA",
    ItemCategory.MEDICAL: "MED",
    ItemCategory.AYURVEDIC: "AYU",
    ItemCategory.COLOR_MATERIAL: "COL",
}

ROW_RE = re.compile(r"^\|?\s*([0-9]+[A-Za-z]?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|?$")


@dataclass
class ParsedItemRow:
    number: int
    name: str
    size: str
    category: ItemCategory


def _parse_row_number(raw_number: str) -> int:
    digits = []
    for char in raw_number.strip():
        if char.isdigit():
            digits.append(str(unicodedata.digit(char)))
    if not digits:
        raise ValueError(raw_number)
    return int("".join(digits))


def _infer_category(section: str, category_text: str) -> ItemCategory:
    inferred = (category_text or section).strip().lower()
    if inferred in SECTION_CATEGORY_MAP:
        return SECTION_CATEGORY_MAP[inferred]
    if "stationery" in inferred:
        return ItemCategory.STATIONERY
    if "medical" in inferred:
        return ItemCategory.MEDICAL
    if "ayurvedic" in inferred:
        return ItemCategory.AYURVEDIC
    if "color" in inferred:
        return ItemCategory.COLOR_MATERIAL
    return ItemCategory.GENERAL


def parse_markdown_rows(source_path: Path):
    rows = []
    section = ""
    with source_path.open(encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("---"):
                continue
            if line.startswith("#"):
                section = line.lstrip("#").strip().lower()
                continue
            if "|" not in line:
                continue
            match = ROW_RE.match(line)
            if not match:
                continue
            number, item_name, default_size, category_text = match.groups()
            header_text = item_name.strip().lower()
            if header_text in {"item", "item name", "no.", "no"}:
                continue
            try:
                parsed_number = _parse_row_number(number)
            except ValueError:
                continue
            rows.append(
                ParsedItemRow(
                    number=parsed_number,
                    name=item_name.strip(),
                    size=default_size.strip(),
                    category=_infer_category(section, category_text),
                )
            )
    return rows


class Command(BaseCommand):
    help = "Import the standard item list from markdown tables and optionally attach Gujarati labels."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="items_Eng.md")
        parser.add_argument("--guj-source", default="items_GUJ.md")
        parser.add_argument("--event-slug")
        parser.add_argument("--create-event", action="store_true")
        parser.add_argument("--event-name", default="Chaturmas 2025")
        parser.add_argument("--start-date", default=date.today().isoformat())
        parser.add_argument("--end-date", default=(date.today() + timedelta(days=120)).isoformat())
        parser.add_argument("--location", default="")
        parser.add_argument("--replace", action="store_true")

    def handle(self, *args, **options):
        source_path = Path(options["source"])
        if not source_path.exists():
            raise CommandError(f"Source file not found: {source_path}")

        guj_map = {}
        guj_path = Path(options["guj_source"])
        if guj_path.exists():
            guj_rows = parse_markdown_rows(guj_path)
            guj_map = {row.number: row.name for row in guj_rows}

        event = self._resolve_event(options)
        if options["replace"]:
            Item.objects.filter(event=event).delete()

        created_count = 0
        counters = defaultdict(int)
        english_rows = parse_markdown_rows(source_path)

        for row in english_rows:
            prefix = CATEGORY_PREFIX_MAP[row.category]
            counters[prefix] += 1
            item_code = f"{prefix}{counters[prefix]:03d}"

            Item.objects.create(
                event=event,
                standard_serial=row.number,
                item_code=item_code,
                item_name=row.name,
                item_name_gu=guj_map.get(row.number, ""),
                category=row.category,
                unit="",
                default_size=row.size,
                description=f"Imported from {source_path.name}",
                estimated_rate=0,
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created_count} items for {event.name}."))

    def _resolve_event(self, options):
        event_slug = options.get("event_slug")
        if event_slug:
            event = Event.objects.filter(slug=event_slug).first()
            if event:
                return event
            if options["create_event"]:
                return Event.objects.create(
                    name=options["event_name"],
                    slug=event_slug,
                    start_date=date.fromisoformat(options["start_date"]),
                    end_date=date.fromisoformat(options["end_date"]),
                    location=options["location"],
                    is_current=True,
                )
            raise CommandError(f"Event not found: {event_slug}")

        event = Event.objects.filter(is_current=True, is_active=True).first()
        if event:
            return event

        if options["create_event"]:
            slug = options["event_name"].lower().replace(" ", "-")
            return Event.objects.create(
                name=options["event_name"],
                slug=slug,
                start_date=date.fromisoformat(options["start_date"]),
                end_date=date.fromisoformat(options["end_date"]),
                location=options["location"],
                is_current=True,
            )

        raise CommandError("No current event found. Create one first or pass --create-event.")
