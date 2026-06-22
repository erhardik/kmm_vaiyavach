from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from django.db import migrations, models


ROW_RE = re.compile(r"^\|?\s*([0-9]+[A-Za-z]?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|?$")


@dataclass
class ParsedRow:
    number: int
    name: str


def _parse_row_number(raw_number: str) -> int:
    digits = []
    for char in raw_number.strip():
        if char.isdigit():
            digits.append(str(unicodedata.digit(char)))
    if not digits:
        raise ValueError(raw_number)
    return int("".join(digits))


def _parse_markdown_rows(source_path: Path):
    rows = []
    with source_path.open(encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "|" not in line:
                continue
            match = ROW_RE.match(line)
            if not match:
                continue
            number, item_name, _, _ = match.groups()
            header_text = item_name.strip().lower()
            if header_text in {"item", "item name", "no.", "no"}:
                continue
            try:
                parsed_number = _parse_row_number(number)
            except ValueError:
                continue
            rows.append(ParsedRow(number=parsed_number, name=item_name.strip()))
    return rows


def backfill_standard_serial(apps, schema_editor):
    Item = apps.get_model("masters", "Item")
    source_path = Path("items_Eng.md")
    if not source_path.exists():
        return

    serial_map = {row.name.strip().lower(): row.number for row in _parse_markdown_rows(source_path)}
    for item in Item.objects.all():
        serial = serial_map.get((item.item_name or "").strip().lower())
        if serial:
            item.standard_serial = serial
            item.save(update_fields=["standard_serial"])


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0004_alter_eventmanagercontact_event"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="standard_serial",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(backfill_standard_serial, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="item",
            index=models.Index(fields=["event", "standard_serial"], name="masters_item_event_8b04eb_idx"),
        ),
        migrations.AddConstraint(
            model_name="item",
            constraint=models.UniqueConstraint(fields=("event", "standard_serial"), name="unique_event_item_standard_serial"),
        ),
    ]
