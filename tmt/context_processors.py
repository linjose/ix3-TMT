from django.conf import settings


def tmt_settings(request):
    return {
        "TMT_ALLOW_SELF_SIGNUP": settings.TMT_ALLOW_SELF_SIGNUP,
        "TMT_MAX_UPLOAD_MB": settings.TMT_MAX_UPLOAD_MB,
    }
