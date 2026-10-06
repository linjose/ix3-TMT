from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from django.conf import settings


class OCRError(RuntimeError):
    pass


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def recognize(image_path: Path, languages: str | None = None) -> str:
    if not settings.TMT_OCR_ENABLED:
        return ""
    if not tesseract_available():
        raise OCRError("找不到 tesseract；請安裝 tesseract-ocr 與語言包。")
    lang = languages or settings.TMT_OCR_LANGUAGES
    cmd = [
        "tesseract", str(image_path), "stdout",
        "-l", lang,
        "--oem", "1",
        "--psm", str(settings.TMT_OCR_PSM),
        "quiet",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False,
            timeout=settings.TMT_OCR_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise OCRError(f"OCR 超過 {settings.TMT_OCR_TIMEOUT_SECONDS} 秒") from exc
    if result.returncode != 0:
        raise OCRError((result.stderr or "Tesseract OCR failed").strip())
    return result.stdout.strip()
