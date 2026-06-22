from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("requirements", "0005_requirementheader_contact_and_stay_updates"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="requirementheader",
            options={"ordering": ["-updated_at", "-created_at"]},
        ),
    ]
