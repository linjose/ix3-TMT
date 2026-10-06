# Security Policy and Deployment Notes

## Supported version

The `main` branch is the actively maintained line for the 2.x rewrite.

## Reporting a vulnerability

Please use a private channel with the repository owner rather than publishing exploitable details in a public issue.

## Content authorization

ix3-TMT is intended for internal knowledge sharing. A Deck controls access to all derivative Slides.

Do not expose `MEDIA_ROOT` directly through Nginx/Apache unless you replace the current protected file views with an authorization-aware internal redirect design.

## Uploaded files

The application only accepts extensions configured by `TMT_ALLOWED_EXTENSIONS` (default `.pptx,.ppt`) and enforces an upload-size limit.

PowerPoint files are passed to LibreOffice for conversion. Treat uploaded Office files as untrusted input:

- keep LibreOffice and the OS patched;
- run the worker as an unprivileged account;
- do not run the worker as root;
- use a dedicated server/container for high-risk public upload scenarios;
- consider malware scanning if uploads come from outside the organization.

The project does not execute PowerPoint macros.

## Secrets

Never commit:

- `.env`
- DB passwords
- Django secret key
- enterprise API keys

Production should set `DJANGO_DEBUG=0`.

## Third-party and confidential content

OCR/search does not change copyright or confidentiality obligations. Organizations should only ingest content they are authorized to store and share.

When AI/VLM support is added, restricted content should not automatically leave the organization. Use an explicit policy per Deck or organization.
