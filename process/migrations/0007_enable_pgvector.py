from django.db import migrations


def enable_pgvector(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")


class Migration(migrations.Migration):

    dependencies = [
        ("process", "0006_renter_move_out_date_alter_renter_apartment_and_more"),
    ]

    operations = [
        migrations.RunPython(enable_pgvector, migrations.RunPython.noop),
    ]
