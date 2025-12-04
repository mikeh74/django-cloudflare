"""Django app configuration for django_cloudflare."""

from django.apps import AppConfig


class DjangoCloudflareConfig(AppConfig):
    """Django Cloudflare app configuration."""

    name = "django_cloudflare"
    verbose_name = "Django Cloudflare"

    def ready(self):
        """
        Import signals when the app is ready.

        The signals module registers Django signal handlers for automatic
        cache purging. This import is for side effects only.
        """
        from django_cloudflare import signals as _signals  # noqa: F401
