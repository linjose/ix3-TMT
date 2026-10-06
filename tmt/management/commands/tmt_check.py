import os
import shutil
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Check ix3-TMT runtime dependencies, DB, media path and OCR languages."

    def handle(self, *args, **options):
        failures = []
        for command in ("soffice", "pdftoppm", "tesseract"):
            path = shutil.which(command)
            if path:
                self.stdout.write(self.style.SUCCESS(f"OK  {command}: {path}"))
            else:
                failures.append(command)
                self.stderr.write(self.style.ERROR(f"MISS {command}"))

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write(self.style.SUCCESS(f"OK  database: {connection.vendor}"))
        except Exception as exc:
            failures.append("database")
            self.stderr.write(self.style.ERROR(f"MISS database: {exc}"))

        media = Path(settings.MEDIA_ROOT)
        try:
            media.mkdir(parents=True, exist_ok=True)
            probe = media / ".tmt-write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            self.stdout.write(self.style.SUCCESS(f"OK  media writable: {media}"))
        except Exception as exc:
            failures.append("media")
            self.stderr.write(self.style.ERROR(f"MISS media writable: {exc}"))

        if shutil.which("tesseract"):
            cp = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, check=False)
            langs = set((cp.stdout + cp.stderr).splitlines())
            wanted = set(settings.TMT_OCR_LANGUAGES.split("+")) if settings.TMT_OCR_ENABLED else set()
            missing = sorted(wanted - langs)
            if missing:
                failures.append("ocr-language")
                self.stderr.write(self.style.ERROR(f"MISS OCR languages: {', '.join(missing)}"))
            elif wanted:
                self.stdout.write(self.style.SUCCESS(f"OK  OCR languages: {settings.TMT_OCR_LANGUAGES}"))

        self.stdout.write(f"OCR enabled={settings.TMT_OCR_ENABLED}, dpi={settings.TMT_RENDER_DPI}, psm={settings.TMT_OCR_PSM}")
        if failures:
            raise CommandError("TMT check failed: " + ", ".join(failures))
        self.stdout.write(self.style.SUCCESS("All required ix3-TMT checks passed."))
