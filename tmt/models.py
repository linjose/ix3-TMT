from __future__ import annotations

import uuid
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q
from django.utils import timezone

User = get_user_model()


def deck_upload_path(instance: "Deck", filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"decks/{instance.id}/original{suffix}"


def slide_image_path(instance: "Slide", filename: str) -> str:
    return f"decks/{instance.deck_id}/slides/{instance.page_number:04d}.png"


def slide_thumb_path(instance: "Slide", filename: str) -> str:
    return f"decks/{instance.deck_id}/thumbs/{instance.page_number:04d}.webp"


class DeckQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()
        if user.is_staff:
            return self
        group_ids = user.groups.values_list("id", flat=True)
        return self.filter(
            Q(owner=user)
            | Q(visibility=Deck.Visibility.INTERNAL)
            | (
                Q(visibility__in=[Deck.Visibility.RESTRICTED, Deck.Visibility.CONFIDENTIAL])
                & (Q(allowed_users=user) | Q(allowed_groups__id__in=group_ids))
            )
        ).distinct()


class Deck(models.Model):
    class Visibility(models.TextChoices):
        INTERNAL = "internal", "全體同仁"
        RESTRICTED = "restricted", "指定群組/人員"
        CONFIDENTIAL = "confidential", "機密（指定人員）"
        PRIVATE = "private", "僅自己"

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "已上傳"
        QUEUED = "queued", "排程中"
        PROCESSING = "processing", "處理中"
        READY = "ready", "可使用"
        FAILED = "failed", "處理失敗"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="decks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    original_file = models.FileField(upload_to=deck_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    page_count = models.PositiveIntegerField(default=0)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.INTERNAL)
    allowed_users = models.ManyToManyField(User, blank=True, related_name="allowed_decks")
    allowed_groups = models.ManyToManyField(Group, blank=True, related_name="allowed_decks")

    source_title = models.CharField(max_length=255, blank=True)
    source_author = models.CharField(max_length=255, blank=True)
    source_publisher = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(blank=True)
    copyright_notice = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED, db_index=True)
    processing_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DeckQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self):
        return self.title

    def can_view(self, user) -> bool:
        return Deck.objects.visible_to(user).filter(pk=self.pk).exists()


class SlideQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()
        if user.is_staff:
            return self
        group_ids = user.groups.values_list("id", flat=True)
        return self.filter(
            Q(deck__owner=user)
            | Q(deck__visibility=Deck.Visibility.INTERNAL)
            | (
                Q(deck__visibility__in=[Deck.Visibility.RESTRICTED, Deck.Visibility.CONFIDENTIAL])
                & (Q(deck__allowed_users=user) | Q(deck__allowed_groups__id__in=group_ids))
            )
        ).distinct()


class Slide(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="slides")
    page_number = models.PositiveIntegerField()
    title = models.CharField(max_length=500, blank=True)
    native_text = models.TextField(blank=True)
    ocr_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    search_text = models.TextField(blank=True)
    image = models.ImageField(upload_to=slide_image_path)
    thumbnail = models.ImageField(upload_to=slide_thumb_path)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    star_count = models.PositiveIntegerField(default=0, db_index=True)
    view_count = models.PositiveIntegerField(default=0, db_index=True)
    ocr_used = models.BooleanField(default=False)
    ocr_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    tags = models.ManyToManyField("Tag", through="SlideTag", related_name="slides")
    objects = SlideQuerySet.as_manager()

    class Meta:
        ordering = ["deck", "page_number"]
        constraints = [models.UniqueConstraint(fields=["deck", "page_number"], name="uniq_deck_page")]
        indexes = [
            models.Index(fields=["deck", "page_number"]),
            models.Index(fields=["-star_count", "-view_count"]),
        ]

    def __str__(self):
        return f"{self.deck.title} / {self.page_number}"


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SlideTag(models.Model):
    class Source(models.TextChoices):
        AUTO = "auto", "自動"
        MANUAL = "manual", "人工"
        OCR = "ocr", "OCR"
        AI = "ai", "AI"

    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.AUTO)
    confidence = models.FloatField(default=1.0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["slide", "tag"], name="uniq_slide_tag")]


class Star(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stars")
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE, related_name="stars")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "slide"], name="uniq_user_slide_star")]
        ordering = ["-created_at"]


class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slides = models.ManyToManyField(Slide, through="CollectionItem", related_name="collections")

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="uniq_user_collection_name")]

    def __str__(self):
        return f"{self.user} / {self.name}"


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE, related_name="collection_items")
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["collection", "slide"], name="uniq_collection_slide")]


class ProcessingJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "排程中"
        RUNNING = "running", "執行中"
        SUCCEEDED = "succeeded", "完成"
        FAILED = "failed", "失敗"

    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="jobs")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    worker_id = models.CharField(max_length=120, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def mark_running(self, worker_id=""):
        self.status = self.Status.RUNNING
        self.worker_id = worker_id
        self.attempts += 1
        self.started_at = timezone.now()
        self.error = ""
        self.save(update_fields=["status", "worker_id", "attempts", "started_at", "error"])


class ViewEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE, related_name="view_events")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class DownloadEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="download_events")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
