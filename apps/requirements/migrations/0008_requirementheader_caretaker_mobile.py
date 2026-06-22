from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("requirements", "0007_requirementheader_volunteer_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="requirementheader",
            name="caretaker_mobile",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
