from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.masters.models import Item


def _parse_markdown_table(filepath):
    content = Path(filepath).read_text(encoding="utf-8")
    lines = content.splitlines()
    rows = []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        if "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 4:
            try:
                serial = int(cells[1])
                rows.append((serial, cells[2], cells[3]))
            except ValueError:
                pass
    return rows


class Command(BaseCommand):
    help = "Populate default_size_gu and variant_name_gu from items_GUJ.md"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, default="items_GUJ.md", help="Path to markdown file")

    def handle(self, *args, **options):
        filepath = Path(options["file"])
        if not filepath.exists():
            self.stderr.write(f"File not found: {filepath}")
            return

        rows = _parse_markdown_table(filepath)
        self.stdout.write(f"Parsed {len(rows)} rows from markdown")

        updated_default = 0
        updated_variant = 0
        not_found = 0

        with transaction.atomic():
            for serial, gu_name, gu_size in rows:
                parent = Item.objects.filter(standard_serial=serial, parent_item__isnull=True).first()
                if not parent:
                    not_found += 1
                    continue

                if gu_size:
                    parent.default_size_gu = gu_size
                    parent.save(update_fields=["default_size_gu"])
                    updated_default += 1

                variants = list(
                    Item.objects.filter(parent_item=parent, is_active=True).order_by("pk")
                )
                if not variants:
                    continue

                gu_parts = [p.strip() for p in gu_size.split("/") if p.strip()] if gu_size else []
                if not gu_parts:
                    continue

                for i, variant in enumerate(variants):
                    if i < len(gu_parts):
                        gu_part = gu_parts[i]
                        if gu_part != (variant.variant_name_gu or ""):
                            variant.variant_name_gu = gu_part
                            variant.save(update_fields=["variant_name_gu"])
                            updated_variant += 1

        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated_default} default_size_gu, {updated_variant} variant_name_gu, {not_found} serials not found"
        ))
