from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ingestion", "0002_pipelinejob"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipelinejob",
            name="last_heartbeat_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Last worker heartbeat while status is processing (crash detection).",
                null=True,
            ),
        ),
    ]
