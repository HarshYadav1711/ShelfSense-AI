import re

from django.db import migrations, models


def strip_legacy_fingerprint_prefixes(apps, schema_editor):
    """Move [fp:...] prefix from summary content into metadata['fingerprint']."""
    BookInsight = apps.get_model("books", "BookInsight")
    pat = re.compile(r"^\[fp:([a-f0-9]+)\] (.*)$", re.DOTALL)
    for insight in BookInsight.objects.filter(insight_type="summary"):
        content = insight.content or ""
        m = pat.match(content)
        if not m:
            continue
        fp, body = m.group(1), m.group(2)
        md = dict(insight.metadata or {})
        md["fingerprint"] = fp
        insight.content = body
        insight.metadata = md
        insight.save(update_fields=["content", "metadata"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0002_bookinsight_unique_insight_type_per_book"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookinsight",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(strip_legacy_fingerprint_prefixes, noop_reverse),
    ]
