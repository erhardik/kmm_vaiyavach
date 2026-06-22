from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.distribution.models import DistributionBatch, DistributionLine
from apps.distribution.services import sync_distribution_line
from apps.funds.models import Donation, FundTransaction, FundTransactionType
from apps.inventory.models import InventoryTransactionType
from apps.inventory.services import create_inventory_transaction
from apps.masters.models import Event, Item, Sponsor, Upashray, Vendor, Volunteer
from apps.procurement.models import GoodsReceipt, PurchaseOrder, PurchaseOrderLine
from apps.procurement.services import sync_goods_receipt
from apps.requirements.models import RequirementHeader, RequirementLine, RequirementStatus
from apps.sponsorship.models import SponsorMaterialReceipt, SponsorshipCommitment, SponsorshipStatus


def _sample_event(options):
    event = Event.objects.filter(slug=options["event_slug"]).first()
    if event:
        return event
    return Event.objects.create(
        name=options["event_name"],
        slug=options["event_slug"],
        start_date=date.fromisoformat(options["start_date"]),
        end_date=date.fromisoformat(options["end_date"]),
        location=options["location"],
        is_current=False,
        is_active=True,
    )


class Command(BaseCommand):
    help = "Seed a realistic sample event dataset for demonstrations and QA."

    def add_arguments(self, parser):
        parser.add_argument("--event-slug", default="sample-chaturmas-2025")
        parser.add_argument("--event-name", default="Sample Chaturmas 2025")
        parser.add_argument("--start-date", default="2025-06-01")
        parser.add_argument("--end-date", default="2025-09-30")
        parser.add_argument("--location", default="Ahmedabad")
        parser.add_argument("--replace", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        event = _sample_event(options)

        if options["replace"]:
            SponsorMaterialReceipt.objects.filter(event=event).delete()
            SponsorshipCommitment.objects.filter(event=event).delete()
            DistributionLine.objects.filter(event=event).delete()
            DistributionBatch.objects.filter(event=event).delete()
            GoodsReceipt.objects.filter(event=event).delete()
            PurchaseOrderLine.objects.filter(event=event).delete()
            PurchaseOrder.objects.filter(event=event).delete()
            FundTransaction.objects.filter(event=event).delete()
            Donation.objects.filter(event=event).delete()
            RequirementLine.objects.filter(event=event).delete()
            RequirementHeader.objects.filter(event=event).delete()
            Vendor.objects.filter(event=event).delete()
            Sponsor.objects.filter(event=event).delete()
            Volunteer.objects.filter(event=event).delete()
            Upashray.objects.filter(event=event).delete()

        items = list(Item.objects.filter(event=event, is_active=True).order_by("item_code")[:12])
        if len(items) < 6:
            source_items = list(Item.objects.filter(is_active=True).exclude(event=event).order_by("item_code")[:12])
            if len(source_items) < 6:
                raise CommandError("Seed requires at least 6 imported items. Run import_standard_items first.")
            items = []
            for source in source_items:
                items.append(
                    Item.objects.create(
                        event=event,
                        item_code=source.item_code,
                        item_name=source.item_name,
                        item_name_gu=source.item_name_gu,
                        category=source.category,
                        unit=source.unit,
                        default_size=source.default_size,
                        description=f"Seed copy of {source.item_code}",
                        estimated_rate=source.estimated_rate,
                    )
                )

        upashrays = [
            Upashray.objects.create(event=event, name=f"Upashray {idx}", area=f"Area {idx}", city="Ahmedabad", contact_person=f"Contact {idx}", mobile=f"99999{idx:04d}")
            for idx in range(1, 6)
        ]
        volunteers = [
            Volunteer.objects.create(event=event, name=f"Volunteer {idx}", mobile=f"88888{idx:04d}", area=f"Zone {idx}", vehicle_available=idx % 2 == 0)
            for idx in range(1, 6)
        ]
        vendors = [
            Vendor.objects.create(event=event, vendor_name=f"Vendor {idx}", contact_person=f"Manager {idx}", mobile=f"77777{idx:04d}", gst_no=f"GST{idx:03d}")
            for idx in range(1, 4)
        ]
        sponsors = [
            Sponsor.objects.create(event=event, sponsor_name=f"Sponsor {idx}", mobile=f"66666{idx:04d}", organization=f"Organization {idx}", reference_volunteer=volunteers[(idx - 1) % len(volunteers)])
            for idx in range(1, 6)
        ]

        requirement_lines = []
        for idx, upashray in enumerate(upashrays, start=1):
            header = RequirementHeader.objects.create(
                event=event,
                upashray=upashray,
                requirement_date=date(2025, 6, 1 + idx),
                status=RequirementStatus.SUBMITTED,
                remarks=f"Seed requirement for {upashray.name}",
            )
            for item in items[:4]:
                line = RequirementLine.objects.create(
                    event=event,
                    requirement=header,
                    item=item,
                    required_qty=Decimal("2") + Decimal(str(idx)),
                    remarks="Seed line",
                )
                requirement_lines.append(line)

        commitments = []
        for idx, sponsor in enumerate(sponsors, start=1):
            for item in items[:2]:
                commitments.append(
                    SponsorshipCommitment.objects.create(
                        event=event,
                        sponsor=sponsor,
                        item=item,
                        committed_qty=Decimal("3") + Decimal(str(idx)),
                        received_qty=Decimal("0"),
                        status=SponsorshipStatus.COMMITTED,
                        expected_date=date(2025, 6, 10 + idx),
                        remarks="Seed commitment",
                    )
                )

        for commitment in commitments[:4]:
            receipt = SponsorMaterialReceipt.objects.create(
                event=event,
                commitment=commitment,
                item=commitment.item,
                received_qty=Decimal("2"),
                received_date=date(2025, 6, 15),
                received_by=None,
                remarks="Seed sponsor receipt",
            )
            receipt.save()

        purchase_order = PurchaseOrder.objects.create(
            event=event,
            vendor=vendors[0],
            po_number="PO-001",
            date=date(2025, 6, 18),
            remarks="Seed purchase order",
        )
        for item in items[:3]:
            PurchaseOrderLine.objects.create(
                event=event,
                purchase_order=purchase_order,
                item=item,
                qty=Decimal("4"),
                rate=item.estimated_rate or Decimal("0"),
                tax_amount=Decimal("0"),
                line_total=(item.estimated_rate or Decimal("0")) * Decimal("4"),
            )
        goods_receipt = GoodsReceipt.objects.create(
            event=event,
            purchase_order=purchase_order,
            date=date(2025, 6, 19),
            remarks="Seed goods receipt",
        )
        sync_goods_receipt(goods_receipt)

        batch = DistributionBatch.objects.create(
            event=event,
            batch_name="Batch 1",
            date=date(2025, 6, 20),
            assigned_volunteer=volunteers[0],
            remarks="Seed distribution",
        )
        for upashray, item in zip(upashrays, items[:5], strict=False):
            line = DistributionLine.objects.create(
                event=event,
                distribution_batch=batch,
                upashray=upashray,
                item=item,
                required_qty=Decimal("3"),
                dispatched_qty=Decimal("0"),
                delivered_qty=Decimal("2"),
                balance_qty=Decimal("1"),
            )
            sync_distribution_line(line)

        Donation.objects.create(
            event=event,
            donor_name="Seed Donor",
            mobile="9999999999",
            amount=Decimal("5000"),
            remarks="Seed donation",
        )
        FundTransaction.objects.create(
            event=event,
            transaction_type=FundTransactionType.INCOME,
            category="Donations",
            amount=Decimal("5000"),
            date=date(2025, 6, 15),
            remarks="Seed income",
            reference_module="donation",
            reference_id="seed-1",
        )
        FundTransaction.objects.create(
            event=event,
            transaction_type=FundTransactionType.EXPENSE,
            category="Procurement",
            amount=Decimal("1200"),
            date=date(2025, 6, 19),
            remarks="Seed expense",
            reference_module="procurement",
            reference_id="PO-001",
        )
        create_inventory_transaction(
            event=event,
            item=items[0],
            transaction_type=InventoryTransactionType.ADJUSTMENT,
            qty=Decimal("1"),
            source_module="seed",
            reference_id="seed-adjustment",
            reference_label="Seed adjustment",
            remarks="Opening balance seed",
        )

        self.stdout.write(self.style.SUCCESS(f"Seeded sample data for {event.name}."))
