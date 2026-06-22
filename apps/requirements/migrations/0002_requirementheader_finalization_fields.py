from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("requirements", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="requirementheader",
            name="checked_by_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="requirementheader",
            name="distributed_to_ms_by_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="requirementheader",
            name="is_locked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="requirementheader",
            name="locked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="requirementheader",
            name="packed_by_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
    ]
