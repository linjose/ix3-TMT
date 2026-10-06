import time
from django.conf import settings
from django.core.management.base import BaseCommand
from tmt.services.processing import claim_job, run_job


class Command(BaseCommand):
    help = "Process queued PPT/PPTX jobs. Use --loop for a lightweight always-on worker."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Keep polling for queued jobs")
        parser.add_argument("--max-jobs", type=int, default=0, help="Stop after N jobs (0 = unlimited in loop mode)")
        parser.add_argument("--poll-seconds", type=int, default=settings.TMT_JOB_POLL_SECONDS)

    def handle(self, *args, **options):
        processed = 0
        while True:
            job = claim_job()
            if job:
                self.stdout.write(f"Processing job {job.pk}: {job.deck.title}")
                try:
                    run_job(job)
                except Exception as exc:
                    self.stderr.write(self.style.ERROR(f"Job {job.pk} failed: {exc}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Job {job.pk} completed"))
                processed += 1
                if options["max_jobs"] and processed >= options["max_jobs"]:
                    break
                continue
            if not options["loop"]:
                break
            time.sleep(max(1, options["poll_seconds"]))
