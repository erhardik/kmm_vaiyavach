from django.db import migrations


def backfill_order_numbers(apps, schema_editor):
    RequirementHeader = apps.get_model("requirements", "RequirementHeader")
    for header in RequirementHeader.objects.filter(order_number__isnull=True).order_by("pk"):
        header.order_number = f"REQ-{header.requirement_date:%Y%m%d}-{header.pk:06d}"
        header.save(update_fields=["order_number"])


class Migration(migrations.Migration):

    dependencies = [
        ("requirements", "0003_requirementheader_area_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_order_numbers, migrations.RunPython.noop),
    ]
