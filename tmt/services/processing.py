from __future__ import annotations

import hashlib
import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils import timezone

from tmt.models import Deck, ProcessingJob, Slide, SlideTag, Tag
from .ocr import OCRError, recognize
from .text_extract import extract_keywords, extract_native_slides, normalize_text, summarize_text


class ProcessingError(RuntimeError):
    pass


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], *, timeout: int = 600, env: dict | None = None) -> subprocess.CompletedProcess:
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ProcessingError(f"指令逾時：{' '.join(cmd[:3])} …") from exc
    if cp.returncode != 0:
        message = (cp.stderr or cp.stdout or "unknown error").strip()
        raise ProcessingError(f"指令失敗 ({cp.returncode})：{' '.join(cmd[:3])} …\n{message[-2000:]}")
    return cp


def _convert_to_pdf(source: Path, workdir: Path) -> Path:
    if not shutil.which("soffice"):
        raise ProcessingError("找不到 LibreOffice soffice。")
    profile = workdir / "lo-profile"
    profile.mkdir(exist_ok=True)
    profile_uri = profile.resolve().as_uri()
    _run([
        "soffice", "--headless", f"-env:UserInstallation={profile_uri}",
        "--convert-to", "pdf", "--outdir", str(workdir), str(source),
    ], timeout=900)
    candidates = list(workdir.glob("*.pdf"))
    if not candidates:
        raise ProcessingError("LibreOffice 未產生 PDF。")
    return candidates[0]


def _render_pdf(pdf_path: Path, workdir: Path) -> list[Path]:
    if not shutil.which("pdftoppm"):
        raise ProcessingError("找不到 pdftoppm；請安裝 poppler-utils。")
    prefix = workdir / "slide"
    _run([
        "pdftoppm", "-png", "-r", str(settings.TMT_RENDER_DPI),
        str(pdf_path), str(prefix),
    ], timeout=1800)

    def page_num(path: Path) -> int:
        try:
            return int(path.stem.rsplit("-", 1)[-1])
        except ValueError:
            return 999999

    files = sorted(workdir.glob("slide-*.png"), key=page_num)
    if not files:
        raise ProcessingError("PDF 未能轉成投影片圖片。")
    return files


def _make_thumbnail(source: Path, dest: Path) -> tuple[int, int]:
    with Image.open(source) as im:
        im = im.convert("RGB")
        width, height = im.size
        thumb = im.copy()
        if thumb.width > settings.TMT_THUMBNAIL_WIDTH:
            ratio = settings.TMT_THUMBNAIL_WIDTH / thumb.width
            thumb = thumb.resize((settings.TMT_THUMBNAIL_WIDTH, round(thumb.height * ratio)), Image.Resampling.LANCZOS)
        thumb.save(dest, "WEBP", quality=82, method=6)
        return width, height


def _should_ocr(native_text: str, has_visual: bool) -> bool:
    if not settings.TMT_OCR_ENABLED:
        return False
    chars = len(native_text.strip())
    if chars < settings.TMT_OCR_TRIGGER_TEXT_LENGTH:
        return True
    if has_visual and chars < settings.TMT_OCR_VISUAL_TRIGGER_TEXT_LENGTH:
        return True
    return False


def _save_slide(deck: Deck, page_number: int, image_path: Path, native, thumb_path: Path) -> Slide:
    native_text = normalize_text(native.text if native else "")
    title = (native.title if native else "").strip()
    has_visual = bool(native.has_visual) if native else True
    ocr_text = ""
    ocr_error = ""
    ocr_used = False
    if _should_ocr(native_text, has_visual):
        ocr_used = True
        try:
            ocr_text = normalize_text(recognize(image_path))
        except OCRError as exc:
            ocr_error = str(exc)[:2000]

    combined = normalize_text("\n".join(x for x in [title, native_text, ocr_text] if x))
    summary = summarize_text(combined)
    if not title:
        title = summary[:100] if summary else f"第 {page_number} 頁"

    width, height = _make_thumbnail(image_path, thumb_path)
    slide = Slide(
        deck=deck, page_number=page_number, title=title[:500],
        native_text=native_text, ocr_text=ocr_text, summary=summary,
        search_text=combined, width=width, height=height,
        ocr_used=ocr_used, ocr_error=ocr_error,
    )
    with image_path.open("rb") as fh:
        slide.image.save(f"{page_number:04d}.png", File(fh), save=False)
    with thumb_path.open("rb") as fh:
        slide.thumbnail.save(f"{page_number:04d}.webp", File(fh), save=False)
    slide.save()

    for keyword in extract_keywords(combined, settings.TMT_MAX_AUTO_TAGS):
        tag, _ = Tag.objects.get_or_create(name=keyword[:80])
        SlideTag.objects.get_or_create(slide=slide, tag=tag, defaults={"source": SlideTag.Source.AUTO, "confidence": 0.6})
    # Include tags in the denormalized search field.
    tag_text = " ".join(slide.tags.values_list("name", flat=True))
    if tag_text:
        slide.search_text = normalize_text(f"{slide.search_text}\n{tag_text}")
        slide.save(update_fields=["search_text"])
    return slide


def process_deck(deck: Deck) -> int:
    source = Path(deck.original_file.path)
    if not source.exists():
        raise ProcessingError("原始簡報檔不存在。")

    deck.status = Deck.Status.PROCESSING
    deck.processing_error = ""
    if not deck.sha256:
        deck.sha256 = compute_sha256(source)
    deck.save(update_fields=["status", "processing_error", "sha256", "updated_at"])

    # Retries start clean. FileField deletion removes old derivatives from storage.
    for old_slide in list(deck.slides.all()):
        old_slide.image.delete(save=False)
        old_slide.thumbnail.delete(save=False)
        old_slide.delete()

    native_slides = {s.page_number: s for s in extract_native_slides(source)}

    with tempfile.TemporaryDirectory(prefix="tmt-") as temp_name:
        temp = Path(temp_name)
        pdf = _convert_to_pdf(source, temp)
        pages = _render_pdf(pdf, temp)
        for idx, page_image in enumerate(pages, start=1):
            thumb = temp / f"thumb-{idx}.webp"
            _save_slide(deck, idx, page_image, native_slides.get(idx), thumb)

    deck.page_count = deck.slides.count()
    deck.status = Deck.Status.READY
    deck.processing_error = ""
    deck.save(update_fields=["page_count", "status", "processing_error", "updated_at"])
    return deck.page_count


def claim_job(worker_id: str | None = None) -> ProcessingJob | None:
    worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}"
    with transaction.atomic():
        # skip_locked is supported by PostgreSQL; SQLite simply runs one worker in recommended mode.
        qs = ProcessingJob.objects.select_for_update()
        if transaction.get_connection().vendor == "postgresql":
            qs = qs.select_for_update(skip_locked=True)
        job = qs.filter(status=ProcessingJob.Status.QUEUED).order_by("created_at").first()
        if not job:
            return None
        job.mark_running(worker_id)
        Deck.objects.filter(pk=job.deck_id).update(status=Deck.Status.PROCESSING, processing_error="")
        return job


def run_job(job: ProcessingJob) -> None:
    try:
        process_deck(job.deck)
    except Exception as exc:
        message = str(exc)[:8000]
        ProcessingJob.objects.filter(pk=job.pk).update(
            status=ProcessingJob.Status.FAILED, error=message, finished_at=timezone.now()
        )
        Deck.objects.filter(pk=job.deck_id).update(status=Deck.Status.FAILED, processing_error=message)
        raise
    else:
        ProcessingJob.objects.filter(pk=job.pk).update(
            status=ProcessingJob.Status.SUCCEEDED, error="", finished_at=timezone.now()
        )
