# Initial schema for ix3-TMT 2.0
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import tmt.models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("auth", "0012_alter_user_first_name_max_length")]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Deck",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("original_file", models.FileField(upload_to=tmt.models.deck_upload_path)),
                ("original_filename", models.CharField(max_length=255)),
                ("file_size", models.BigIntegerField(default=0)),
                ("sha256", models.CharField(blank=True, db_index=True, max_length=64)),
                ("page_count", models.PositiveIntegerField(default=0)),
                ("visibility", models.CharField(choices=[("internal", "全體同仁"), ("restricted", "指定群組/人員"), ("confidential", "機密（指定人員）"), ("private", "僅自己")], default="internal", max_length=20)),
                ("source_title", models.CharField(blank=True, max_length=255)),
                ("source_author", models.CharField(blank=True, max_length=255)),
                ("source_publisher", models.CharField(blank=True, max_length=255)),
                ("source_url", models.URLField(blank=True)),
                ("copyright_notice", models.CharField(blank=True, max_length=500)),
                ("status", models.CharField(choices=[("uploaded", "已上傳"), ("queued", "排程中"), ("processing", "處理中"), ("ready", "可使用"), ("failed", "處理失敗")], db_index=True, default="uploaded", max_length=20)),
                ("processing_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("allowed_groups", models.ManyToManyField(blank=True, related_name="allowed_decks", to="auth.group")),
                ("allowed_users", models.ManyToManyField(blank=True, related_name="allowed_decks", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decks", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Slide",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("page_number", models.PositiveIntegerField()),
                ("title", models.CharField(blank=True, max_length=500)),
                ("native_text", models.TextField(blank=True)),
                ("ocr_text", models.TextField(blank=True)),
                ("summary", models.TextField(blank=True)),
                ("search_text", models.TextField(blank=True)),
                ("image", models.ImageField(upload_to=tmt.models.slide_image_path)),
                ("thumbnail", models.ImageField(upload_to=tmt.models.slide_thumb_path)),
                ("width", models.PositiveIntegerField(default=0)),
                ("height", models.PositiveIntegerField(default=0)),
                ("star_count", models.PositiveIntegerField(db_index=True, default=0)),
                ("view_count", models.PositiveIntegerField(db_index=True, default=0)),
                ("ocr_used", models.BooleanField(default=False)),
                ("ocr_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("deck", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="slides", to="tmt.deck")),
            ],
            options={"ordering": ["deck", "page_number"]},
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collections", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="ProcessingJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("queued", "排程中"), ("running", "執行中"), ("succeeded", "完成"), ("failed", "失敗")], db_index=True, default="queued", max_length=20)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("worker_id", models.CharField(blank=True, max_length=120)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("deck", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="jobs", to="tmt.deck")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="Star",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("slide", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stars", to="tmt.slide")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stars", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SlideTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(choices=[("auto", "自動"), ("manual", "人工"), ("ocr", "OCR"), ("ai", "AI")], default="auto", max_length=20)),
                ("confidence", models.FloatField(default=1.0)),
                ("slide", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tmt.slide")),
                ("tag", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tmt.tag")),
            ],
        ),
        migrations.AddField(
            model_name="slide",
            name="tags",
            field=models.ManyToManyField(related_name="slides", through="tmt.SlideTag", to="tmt.tag"),
        ),
        migrations.CreateModel(
            name="CollectionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("note", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("collection", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="tmt.collection")),
                ("slide", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collection_items", to="tmt.slide")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="collection",
            name="slides",
            field=models.ManyToManyField(related_name="collections", through="tmt.CollectionItem", to="tmt.slide"),
        ),
        migrations.CreateModel(
            name="ViewEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("slide", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="view_events", to="tmt.slide")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="DownloadEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("deck", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="download_events", to="tmt.deck")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name="slide", constraint=models.UniqueConstraint(fields=("deck", "page_number"), name="uniq_deck_page")),
        migrations.AddConstraint(model_name="star", constraint=models.UniqueConstraint(fields=("user", "slide"), name="uniq_user_slide_star")),
        migrations.AddConstraint(model_name="slidetag", constraint=models.UniqueConstraint(fields=("slide", "tag"), name="uniq_slide_tag")),
        migrations.AddConstraint(model_name="collection", constraint=models.UniqueConstraint(fields=("user", "name"), name="uniq_user_collection_name")),
        migrations.AddConstraint(model_name="collectionitem", constraint=models.UniqueConstraint(fields=("collection", "slide"), name="uniq_collection_slide")),
        migrations.AddIndex(model_name="deck", index=models.Index(fields=["status", "created_at"], name="tmt_deck_status_4b348a_idx")),
        migrations.AddIndex(model_name="slide", index=models.Index(fields=["deck", "page_number"], name="tmt_slide_deck_id_ed4f9e_idx")),
        migrations.AddIndex(model_name="slide", index=models.Index(fields=["-star_count", "-view_count"], name="tmt_slide_star_co_c8c4e7_idx")),
        migrations.AddIndex(model_name="processingjob", index=models.Index(fields=["status", "created_at"], name="tmt_process_status_51c87f_idx")),
    ]
