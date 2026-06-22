from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0002_item_item_name_gu_alter_item_unit"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="primary_contact_mobile",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="event",
            name="primary_contact_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.CreateModel(
            name="EventManagerContact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("contact_name", models.CharField(max_length=120)),
                ("mobile", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("designation", models.CharField(blank=True, max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("is_primary", models.BooleanField(default=False)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="masters_eventmanagercontact_records", to="masters.event")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("is_active", models.BooleanField(default=True)),
                ("is_deleted", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-is_primary", "contact_name"],
            },
        ),
        migrations.AddConstraint(
            model_name="eventmanagercontact",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_primary", True)),
                fields=("event",),
                name="unique_primary_event_manager_contact",
            ),
        ),
    ]
