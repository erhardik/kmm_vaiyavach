from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("requirements", "0004_backfill_requirement_order_numbers"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="requirementheader",
            name="volunteer_name",
        ),
        migrations.RemoveField(
            model_name="requirementheader",
            name="your_name",
        ),
        migrations.AddField(
            model_name="requirementheader",
            name="pujya_shri_mobile",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="requirementheader",
            name="caretaker_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AlterField(
            model_name="requirementheader",
            name="stay_type",
            field=models.CharField(blank=True, choices=[("SANGH_UPASHRAY", "Sangh Upashray"), ("STHIRVAS", "Sthirvas")], default="STHIRVAS", max_length=20),
        ),
    ]
