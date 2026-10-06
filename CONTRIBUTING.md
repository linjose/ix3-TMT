# Contributing

1. Fork or create a branch.
2. Keep the Slide-first data model intact unless a design change is discussed first.
3. Add tests for permission or processing behavior changes.
4. Run:

```bash
python manage.py check
python manage.py test
python -m compileall -q config tmt
```

5. Never add real client decks, credentials, or copyrighted third-party samples to the repository.

## Coding principles

- Core features must continue to work without external AI APIs.
- Permission checks belong on server-side queries and file delivery, not only templates.
- CPU-heavy processing belongs in the worker, not HTTP request handling.
- Preserve source provenance for third-party material.
