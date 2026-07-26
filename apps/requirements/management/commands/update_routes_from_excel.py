import openpyxl

from django.core.management.base import BaseCommand

from apps.requirements.models import RequirementHeader


def _build_route_display_to_code():
    mapping = {}
    for choice in RequirementHeader.RouteAreaChoices:
        mapping[choice.label] = choice.value
    return mapping


def _build_sub_route_display_to_code():
    mapping = {}
    for area_code, choices in RequirementHeader.SUB_ROUTE_CHOICES.items():
        for code, label in choices:
            mapping[label] = code
    return mapping


class Command(BaseCommand):
    help = "Update Route / Sub Route on RequirementHeader records from a correction Excel file."

    def add_arguments(self, parser):
        parser.add_argument("excel_path", help="Path to the correction Excel file")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving",
        )

    def handle(self, *args, **options):
        path = options["excel_path"]
        dry_run = options["dry_run"]

        route_map = _build_route_display_to_code()
        sub_route_map = _build_sub_route_display_to_code()

        wb = openpyxl.load_workbook(path)
        ws = wb.active
        rows = list(ws.iter_rows(min_row=1, values_only=True))
        if not rows:
            self.stderr.write(self.style.ERROR("Excel file is empty"))
            return

        header = [str(c or "").strip() for c in rows[0]]

        def col(name):
            try:
                return header.index(name)
            except ValueError:
                return -1

        idx_form = col("Form No.")
        idx_order = col("Order ID")
        idx_route = col("Route")
        idx_sub = col("Sub Route")

        if idx_form == -1 and idx_order == -1:
            self.stderr.write(self.style.ERROR("Excel must have a 'Form No.' or 'Order ID' column"))
            return
        if idx_route == -1:
            self.stderr.write(self.style.ERROR("Excel must have a 'Route' column"))
            return

        updated = 0
        skipped = 0
        errors = 0

        for row in rows[1:]:
            if not any(cell is not None for cell in row):
                continue

            form_no = str(row[idx_form]).strip() if idx_form != -1 and row[idx_form] is not None else ""
            order_id = str(row[idx_order]).strip() if idx_order != -1 and row[idx_order] is not None else ""
            route_display = str(row[idx_route]).strip() if row[idx_route] is not None else ""
            sub_route_display = str(row[idx_sub]).strip() if idx_sub != -1 and row[idx_sub] is not None else ""

            if not route_display:
                errors += 1
                self.stderr.write(self.style.WARNING(f"Skipping row — Route is empty (form={form_no}, order={order_id})"))
                continue

            route_code = route_map.get(route_display)
            if not route_code:
                errors += 1
                self.stderr.write(self.style.ERROR(f"Unknown Route display value: '{route_display}' (form={form_no}, order={order_id})"))
                continue

            sub_route_code = ""
            if sub_route_display:
                sub_route_code = sub_route_map.get(sub_route_display)
                if not sub_route_code:
                    errors += 1
                    self.stderr.write(self.style.ERROR(f"Unknown Sub Route display value: '{sub_route_display}' (form={form_no}, order={order_id})"))
                    continue

            header_obj = None
            if form_no:
                header_obj = RequirementHeader.objects.filter(form_number=form_no).first()
            if not header_obj and order_id:
                header_obj = RequirementHeader.objects.filter(order_number=order_id).first()

            if not header_obj:
                errors += 1
                self.stderr.write(self.style.WARNING(f"RequirementHeader not found (form={form_no}, order={order_id})"))
                continue

            old_route = header_obj.get_route_area_display()
            old_sub = header_obj.get_route_sub_area_display()
            new_route = route_display
            new_sub = sub_route_display or old_sub

            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] {header_obj.form_number or header_obj.order_number}: "
                    f"Route '{old_route}' -> '{new_route}', "
                    f"Sub Route '{old_sub}' -> '{new_sub}'"
                )
            else:
                header_obj.route_area = route_code
                header_obj.route_sub_area = sub_route_code
                header_obj.save(update_fields=["route_area", "route_sub_area"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated {header_obj.form_number or header_obj.order_number}: "
                        f"Route '{old_route}' -> '{new_route}', "
                        f"Sub Route '{old_sub}' -> '{new_sub}'"
                    )
                )
            updated += 1

        summary = f"Done. {updated} processed, {skipped} skipped, {errors} errors."
        if dry_run:
            summary = "[DRY-RUN] " + summary
        if errors:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
