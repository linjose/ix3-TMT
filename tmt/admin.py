from django.contrib import admin
from .models import (
    Collection, CollectionItem, Deck, DownloadEvent, ProcessingJob,
    Slide, SlideTag, Star, Tag, ViewEvent,
)


class SlideInline(admin.TabularInline):
    model = Slide
    fields = ("page_number", "title", "star_count", "view_count", "ocr_used")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "visibility", "page_count", "created_at")
    list_filter = ("status", "visibility", "created_at")
    search_fields = ("title", "description", "owner__username", "source_title")
    filter_horizontal = ("allowed_users", "allowed_groups")
    inlines = [SlideInline]


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("deck", "page_number", "title", "star_count", "view_count", "ocr_used")
    search_fields = ("title", "native_text", "ocr_text", "summary", "deck__title")
    list_filter = ("ocr_used", "created_at")


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ("deck", "status", "attempts", "worker_id", "created_at", "started_at", "finished_at")
    list_filter = ("status",)
    readonly_fields = ("created_at", "started_at", "finished_at")


admin.site.register(Tag)
admin.site.register(SlideTag)
admin.site.register(Star)
admin.site.register(Collection)
admin.site.register(CollectionItem)
admin.site.register(ViewEvent)
admin.site.register(DownloadEvent)
