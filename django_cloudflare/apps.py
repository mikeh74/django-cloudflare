"""Django app configuration for django_cloudflare."""

from django.apps import AppConfig


class DjangoCloudflareConfig(AppConfig):
    """Django Cloudflare app configuration."""

    name = "django_cloudflare"
    verbose_name = "Django Cloudflare"

    def ready(self):
        """Import signals when the app is ready."""
        # Import signals to register them
        from django_cloudflare import signals  # noqa: F401
