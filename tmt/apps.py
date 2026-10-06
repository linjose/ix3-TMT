from django.apps import AppConfig


class TmtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tmt"
    verbose_name = "ix3-TMT"

    def ready(self):
        from . import signals  # noqa: F401
