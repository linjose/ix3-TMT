from django.db import migrations


def add_pg_trgm(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        cursor.execute("CREATE INDEX IF NOT EXISTS tmt_slide_search_trgm ON tmt_slide USING gin (search_text gin_trgm_ops)")
        cursor.execute("CREATE INDEX IF NOT EXISTS tmt_slide_title_trgm ON tmt_slide USING gin (title gin_trgm_ops)")


def remove_pg_trgm_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS tmt_slide_search_trgm")
        cursor.execute("DROP INDEX IF EXISTS tmt_slide_title_trgm")


class Migration(migrations.Migration):
    dependencies = [("tmt", "0001_initial")]
    operations = [migrations.RunPython(add_pg_trgm, remove_pg_trgm_indexes)]
