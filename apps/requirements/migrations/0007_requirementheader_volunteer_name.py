from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("requirements", "0006_alter_requirementheader_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="requirementheader",
            name="volunteer_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
    ]
