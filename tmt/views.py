from __future__ import annotations

import mimetypes
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CollectionForm, DeckEditForm, DeckUploadForm, RegistrationForm
from .models import Collection, CollectionItem, Deck, DownloadEvent, ProcessingJob, Slide, Star, Tag, ViewEvent
from .services.processing import compute_sha256

User = get_user_model()


def _visible_slides(user):
    return Slide.objects.visible_to(user).filter(deck__status=Deck.Status.READY).select_related("deck", "deck__owner")


@login_required
def home(request):
    slides = _visible_slides(request.user).prefetch_related("tags")
    q = request.GET.get("q", "").strip()
    tag = request.GET.get("tag", "").strip()
    sort = request.GET.get("sort", "newest")
    mine = request.GET.get("mine") == "1"
    starred = request.GET.get("starred") == "1"

    if q:
        terms = [t for t in q.split() if t][:8]
        for term in terms:
            slides = slides.filter(
                Q(search_text__icontains=term)
                | Q(title__icontains=term)
                | Q(deck__title__icontains=term)
                | Q(deck__description__icontains=term)
                | Q(tags__name__icontains=term)
            )
    if tag:
        slides = slides.filter(tags__name=tag)
    if mine:
        slides = slides.filter(deck__owner=request.user)
    if starred:
        slides = slides.filter(stars__user=request.user)

    if sort == "popular":
        slides = slides.order_by("-star_count", "-view_count", "-created_at")
    elif sort == "viewed":
        slides = slides.order_by("-view_count", "-star_count", "-created_at")
    else:
        slides = slides.order_by("-created_at")
    slides = slides.distinct()[:120]

    starred_ids = set(Star.objects.filter(user=request.user, slide__in=slides).values_list("slide_id", flat=True))
    visible_ids = _visible_slides(request.user).values_list("pk", flat=True)
    popular_tags = Tag.objects.filter(slides__id__in=visible_ids).distinct().order_by("name")[:30]
    return render(request, "tmt/home.html", {
        "slides": slides, "q": q, "tag": tag, "sort": sort,
        "mine": mine, "starred_filter": starred,
        "starred_ids": starred_ids, "popular_tags": popular_tags,
    })


@login_required
def upload_deck(request):
    if request.method == "POST":
        form = DeckUploadForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                deck = form.save(commit=False)
                deck.owner = request.user
                deck.original_filename = request.FILES["original_file"].name
                deck.file_size = request.FILES["original_file"].size
                deck.status = Deck.Status.QUEUED
                deck.save()
                form.save_m2m()
                try:
                    deck.sha256 = compute_sha256(Path(deck.original_file.path))
                    deck.save(update_fields=["sha256"])
                except OSError:
                    pass
                duplicate = Deck.objects.exclude(pk=deck.pk).filter(sha256=deck.sha256).first() if deck.sha256 else None
                ProcessingJob.objects.create(deck=deck)
            if duplicate:
                messages.warning(request, f"已排程處理；系統偵測到相同內容可能曾由 {duplicate.owner} 上傳：{duplicate.title}")
            else:
                messages.success(request, "簡報已上傳並加入處理佇列。")
            return redirect("tmt:deck_detail", pk=deck.pk)
    else:
        form = DeckUploadForm()
    return render(request, "tmt/upload.html", {"form": form})


@login_required
def deck_detail(request, pk):
    deck = get_object_or_404(Deck.objects.visible_to(request.user).select_related("owner"), pk=pk)
    slides = deck.slides.all().prefetch_related("tags") if deck.status == Deck.Status.READY else []
    latest_job = deck.jobs.order_by("-created_at").first()
    return render(request, "tmt/deck_detail.html", {"deck": deck, "slides": slides, "latest_job": latest_job})


@login_required
def deck_edit(request, pk):
    deck = get_object_or_404(Deck.objects.visible_to(request.user), pk=pk)
    if deck.owner != request.user and not request.user.is_staff:
        raise Http404
    form = DeckEditForm(request.POST or None, instance=deck)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "簡報資訊與權限已更新。")
        return redirect("tmt:deck_detail", pk=deck.pk)
    return render(request, "tmt/deck_edit.html", {"deck": deck, "form": form})


@login_required
@require_POST
def deck_delete(request, pk):
    deck = get_object_or_404(Deck.objects.visible_to(request.user), pk=pk)
    if deck.owner != request.user and not request.user.is_staff:
        raise Http404
    if deck.jobs.filter(status__in=[ProcessingJob.Status.QUEUED, ProcessingJob.Status.RUNNING]).exists():
        messages.error(request, "簡報仍在排程/處理中，為避免 Worker 與刪除動作衝突，請處理完成後再刪除。")
        return redirect("tmt:deck_detail", pk=deck.pk)
    title = deck.title
    deck.delete()
    messages.success(request, f"已刪除簡報「{title}」及其衍生投影片。")
    return redirect("tmt:home")


@login_required
def slide_detail(request, pk):
    slide = get_object_or_404(_visible_slides(request.user).prefetch_related("tags"), pk=pk)
    ViewEvent.objects.create(user=request.user, slide=slide)
    Slide.objects.filter(pk=slide.pk).update(view_count=F("view_count") + 1)
    slide.view_count += 1
    is_starred = Star.objects.filter(user=request.user, slide=slide).exists()
    collections = request.user.collections.all()
    contained_in = set(CollectionItem.objects.filter(collection__user=request.user, slide=slide).values_list("collection_id", flat=True))
    prev_slide = slide.deck.slides.filter(page_number__lt=slide.page_number).order_by("-page_number").first()
    next_slide = slide.deck.slides.filter(page_number__gt=slide.page_number).order_by("page_number").first()
    return render(request, "tmt/slide_detail.html", {
        "slide": slide, "is_starred": is_starred, "collections": collections,
        "contained_in": contained_in, "prev_slide": prev_slide, "next_slide": next_slide,
    })


@login_required
@require_POST
def toggle_star(request, pk):
    slide = get_object_or_404(_visible_slides(request.user), pk=pk)
    star = Star.objects.filter(user=request.user, slide=slide).first()
    if star:
        star.delete()
        active = False
    else:
        Star.objects.create(user=request.user, slide=slide)
        active = True
    count = Star.objects.filter(slide=slide).count()
    Slide.objects.filter(pk=slide.pk).update(star_count=count)
    return JsonResponse({"ok": True, "active": active, "count": count})


@login_required
def collections(request):
    items = request.user.collections.all().prefetch_related("items")
    return render(request, "tmt/collections.html", {"collections": items})


@login_required
def collection_create(request):
    form = CollectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        collection = form.save(commit=False)
        collection.user = request.user
        collection.save()
        messages.success(request, "收藏夾已建立。")
        return redirect("tmt:collection_detail", pk=collection.pk)
    return render(request, "tmt/collection_form.html", {"form": form, "title": "新增收藏夾"})


@login_required
def collection_edit(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    form = CollectionForm(request.POST or None, instance=collection)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "收藏夾已更新。")
        return redirect("tmt:collection_detail", pk=collection.pk)
    return render(request, "tmt/collection_form.html", {"form": form, "title": "編輯收藏夾"})


@login_required
@require_POST
def collection_delete(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    name = collection.name
    collection.delete()
    messages.success(request, f"已刪除收藏夾「{name}」。")
    return redirect("tmt:collections")


@login_required
def collection_detail(request, pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    visible_ids = _visible_slides(request.user).values_list("pk", flat=True)
    items = collection.items.filter(slide_id__in=visible_ids).select_related("slide", "slide__deck")
    return render(request, "tmt/collection_detail.html", {"collection": collection, "items": items})


@login_required
@require_POST
def collection_add(request, slide_pk):
    slide = get_object_or_404(_visible_slides(request.user), pk=slide_pk)
    collection = get_object_or_404(Collection, pk=request.POST.get("collection_id"), user=request.user)
    item, created = CollectionItem.objects.get_or_create(collection=collection, slide=slide)
    note = request.POST.get("note", "").strip()[:500]
    if note and item.note != note:
        item.note = note
        item.save(update_fields=["note"])
    if created:
        messages.success(request, f"已加入「{collection.name}」。")
    else:
        messages.info(request, f"這張投影片已在「{collection.name}」中。")
    return redirect(request.POST.get("next") or reverse("tmt:slide_detail", args=[slide.pk]))


@login_required
@require_POST
def collection_item_note(request, pk, item_pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    item = get_object_or_404(CollectionItem, pk=item_pk, collection=collection)
    item.note = request.POST.get("note", "").strip()[:500]
    item.save(update_fields=["note"])
    messages.success(request, "書籤備註已更新。")
    return redirect("tmt:collection_detail", pk=collection.pk)

@login_required
@require_POST
def collection_remove(request, pk, item_pk):
    collection = get_object_or_404(Collection, pk=pk, user=request.user)
    item = get_object_or_404(CollectionItem, pk=item_pk, collection=collection)
    item.delete()
    messages.success(request, "已從收藏夾移除。")
    return redirect("tmt:collection_detail", pk=collection.pk)


@login_required
def my_contributions(request):
    decks = request.user.decks.all()
    slides = Slide.objects.filter(deck__owner=request.user, deck__status=Deck.Status.READY)
    stats = {
        "decks": decks.filter(status=Deck.Status.READY).count(),
        "slides": slides.count(),
        "stars": Star.objects.filter(slide__deck__owner=request.user).count(),
        "unique_starrers": Star.objects.filter(slide__deck__owner=request.user).values("user_id").distinct().count(),
        "views": sum(slides.values_list("view_count", flat=True)),
        "collections": CollectionItem.objects.filter(slide__deck__owner=request.user).values("collection__user_id").distinct().count(),
    }
    top_slides = slides.order_by("-star_count", "-view_count")[:12]
    recent_decks = decks[:10]
    return render(request, "tmt/contributions.html", {"stats": stats, "top_slides": top_slides, "recent_decks": recent_decks})


@login_required
def leaderboard(request):
    visible = list(_visible_slides(request.user).values("id", "deck__owner_id", "star_count", "view_count"))
    by_user = defaultdict(lambda: {"slides": 0, "stars": 0, "views": 0})
    slide_ids = []
    for row in visible:
        data = by_user[row["deck__owner_id"]]
        data["slides"] += 1
        data["stars"] += row["star_count"]
        data["views"] += row["view_count"]
        slide_ids.append(row["id"])
    unique = defaultdict(set)
    for user_id, owner_id in Star.objects.filter(slide_id__in=slide_ids).values_list("user_id", "slide__deck__owner_id"):
        unique[owner_id].add(user_id)
    users = {u.id: u for u in User.objects.filter(id__in=by_user.keys())}
    rows = []
    for uid, data in by_user.items():
        data["user"] = users.get(uid)
        data["unique_starrers"] = len(unique[uid])
        rows.append(data)
    rows.sort(key=lambda x: (x["stars"], x["unique_starrers"], x["slides"]), reverse=True)
    return render(request, "tmt/leaderboard.html", {"rows": rows})


@login_required
@require_POST
def retry_job(request, pk):
    deck = get_object_or_404(Deck.objects.visible_to(request.user), pk=pk)
    if deck.owner != request.user and not request.user.is_staff:
        raise Http404
    if deck.jobs.filter(status__in=[ProcessingJob.Status.QUEUED, ProcessingJob.Status.RUNNING]).exists():
        messages.info(request, "這份簡報已有處理工作正在排程或執行。")
    else:
        ProcessingJob.objects.create(deck=deck)
        deck.status = Deck.Status.QUEUED
        deck.processing_error = ""
        deck.save(update_fields=["status", "processing_error", "updated_at"])
        messages.success(request, "已重新加入處理佇列。")
    return redirect("tmt:deck_detail", pk=deck.pk)


def _secure_file_response(path: str, filename: str | None = None, content_type: str | None = None, as_attachment=False):
    try:
        fh = open(path, "rb")
    except FileNotFoundError:
        raise Http404
    if not content_type:
        content_type = mimetypes.guess_type(filename or path)[0] or "application/octet-stream"
    return FileResponse(fh, content_type=content_type, as_attachment=as_attachment, filename=filename)


@login_required
def slide_image(request, pk, thumb=False):
    slide = get_object_or_404(_visible_slides(request.user), pk=pk)
    field = slide.thumbnail if thumb else slide.image
    response = _secure_file_response(field.path, Path(field.name).name)
    if slide.deck.visibility in {Deck.Visibility.CONFIDENTIAL, Deck.Visibility.PRIVATE}:
        response["Cache-Control"] = "private, no-store"
    else:
        response["Cache-Control"] = "private, max-age=3600"
    return response


@login_required
def deck_download(request, pk):
    deck = get_object_or_404(Deck.objects.visible_to(request.user), pk=pk)
    DownloadEvent.objects.create(user=request.user, deck=deck)
    return _secure_file_response(deck.original_file.path, deck.original_filename, as_attachment=True)


def register(request):
    if not settings.TMT_ALLOW_SELF_SIGNUP:
        raise Http404
    if request.user.is_authenticated:
        return redirect("tmt:home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("tmt:home")
    return render(request, "registration/register.html", {"form": form})


def health(request):
    return JsonResponse({"ok": True, "service": "ix3-TMT"})
