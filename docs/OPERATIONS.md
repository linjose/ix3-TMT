# Operations Guide

## Health

```text
GET /health/
```

returns:

```json
{"ok": true, "service": "ix3-TMT"}
```

## Important services

Native:

```bash
systemctl status ix3-tmt-web
systemctl status ix3-tmt-worker
```

Docker:

```bash
docker compose ps
docker compose logs -f web
docker compose logs -f worker
```

## Worker recovery

Jobs in `failed` are not retried infinitely. Use the Deck page's retry button after fixing the environment.

If a process was killed while a Job was `running`, an administrator can inspect it in `/admin/tmt/processingjob/`. The current minimal worker intentionally does not auto-reset stale `running` jobs because automatic retry of a repeatedly crashing LibreOffice input can cause a loop.

## Backup checklist

Backup together:

- PostgreSQL database
- media directory/volume
- `/etc/ix3-tmt.env` in a secret-management-safe location

Do not commit `.env`.

## Capacity notes

Storage use is dominated by:

- original PPT/PPTX;
- full-size rendered PNGs;
- WebP thumbnails.

Temporary PDF/high-resolution render files are created under the OS temporary directory and removed at the end of each job.

If storage becomes a concern, the first optimization should be changing full-size derivative storage from PNG to high-quality WebP while retaining the original PPT. The current version stays with PNG for predictable quality and OCR traceability.

## Upgrade

Always run migrations after upgrading code. See README.

## Monitoring ideas

For the initial version, useful operational signals are:

- queued job count;
- oldest queued job age;
- failed job count;
- disk free space;
- DB backup age;
- worker service status.

These can later be exported to Prometheus without altering the processing model.
