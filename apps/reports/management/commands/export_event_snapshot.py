import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.dashboard.services import get_dashboard_event_queryset
from apps.reports.services import (
    build_fund_ledger_export,
    build_inventory_ledger_export,
    build_item_control_export,
    build_requirement_export,
    build_report_home_summary,
    build_sponsorship_export,
    export_rows_to_csv,
)


class Command(BaseCommand):
    help = "Export a full event snapshot into CSV and JSON files."

    def add_arguments(self, parser):
        parser.add_argument("--event-slug")
        parser.add_argument("--output", default="media/exports")

    def handle(self, *args, **options):
        event = None
        if options.get("event_slug"):
            event = get_dashboard_event_queryset().filter(slug=options["event_slug"]).first()
        else:
            event = get_dashboard_event_queryset().first()
        if event is None:
            raise CommandError("No active event found.")

        output_dir = Path(options["output"])
        output_dir.mkdir(parents=True, exist_ok=True)

        item_rows, item_summary = build_item_control_export(event)
        files = {
            "item_control.csv": export_rows_to_csv(item_rows, ["Item", "Category", "Required", "Sponsored", "Received", "Purchase Needed", "Stock", "Distributed", "Balance"]),
            "inventory_ledger.csv": export_rows_to_csv(build_inventory_ledger_export(event), ["Timestamp", "Item", "Type", "Qty", "Source Module", "Reference", "Unit Rate", "Remarks", "Created By"]),
            "fund_ledger.csv": export_rows_to_csv(build_fund_ledger_export(event), ["Date", "Type", "Category", "Amount", "Reference Module", "Reference ID", "Remarks"]),
            "requirements.csv": export_rows_to_csv(build_requirement_export(event), ["Requirement", "Upashray", "Item", "Required Qty", "Remarks"]),
            "sponsorship.csv": export_rows_to_csv(build_sponsorship_export(event), ["Sponsor", "Item", "Committed Qty", "Received Qty", "Status", "Expected Date"]),
            "summary.json": json.dumps(
                {
                    "event": event.name,
                    "slug": event.slug,
                    "summary": build_report_home_summary(event),
                    "item_control_summary": item_summary,
                },
                indent=2,
                default=str,
            ),
        }

        for filename, content in files.items():
            (output_dir / filename).write_text(content, encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"Exported event snapshot for {event.name} to {output_dir}"))
