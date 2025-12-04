"""
Settings for Django Cloudflare.

These settings can be overridden in your Django project's settings.py file
by prefixing them with 'CLOUDFLARE_'.

Example:
    CLOUDFLARE_API_TOKEN = 'your-api-token'
    CLOUDFLARE_ZONE_ID = 'your-zone-id'
"""

from django.conf import settings as django_settings


def get_setting(name, default=None):
    """
    Get a setting from Django settings with CLOUDFLARE_ prefix.

    Args:
        name: The setting name without prefix.
        default: Default value if setting is not found.

    Returns:
        The setting value or default.
    """
    return getattr(django_settings, f"CLOUDFLARE_{name}", default)


# Default values for settings
DEFAULTS = {
    "API_TOKEN": "",
    "ZONE_ID": "",
    "API_BASE_URL": "https://api.cloudflare.com/client/v4",
    "ENABLED": True,
    "PURGE_BATCH_SIZE": 30,
    "PURGE_DELAY_SECONDS": 0,
    "BACKGROUND_PURGE": True,
    "DEBUG": False,
    "URL_DEPENDENCIES": {},
    "SITE_URL": "",
}


def get_api_token():
    """Get the Cloudflare API token."""
    return get_setting("API_TOKEN", DEFAULTS["API_TOKEN"])


def get_zone_id():
    """Get the Cloudflare zone ID."""
    return get_setting("ZONE_ID", DEFAULTS["ZONE_ID"])


def get_api_base_url():
    """Get the Cloudflare API base URL."""
    return get_setting("API_BASE_URL", DEFAULTS["API_BASE_URL"])


def is_enabled():
    """Check if Cloudflare integration is enabled."""
    return get_setting("ENABLED", DEFAULTS["ENABLED"])


def get_purge_batch_size():
    """Get the batch size for URL purging."""
    return get_setting("PURGE_BATCH_SIZE", DEFAULTS["PURGE_BATCH_SIZE"])


def get_purge_delay_seconds():
    """Get the delay before executing background purges."""
    return get_setting("PURGE_DELAY_SECONDS", DEFAULTS["PURGE_DELAY_SECONDS"])


def use_background_purge():
    """Check if background purging is enabled."""
    return get_setting("BACKGROUND_PURGE", DEFAULTS["BACKGROUND_PURGE"])


def is_debug():
    """Check if debug mode is enabled."""
    return get_setting("DEBUG", DEFAULTS["DEBUG"])


def get_url_dependencies():
    """Get the URL dependencies configuration."""
    return get_setting("URL_DEPENDENCIES", DEFAULTS["URL_DEPENDENCIES"])


def get_site_url():
    """Get the site URL for constructing full URLs."""
    return get_setting("SITE_URL", DEFAULTS["SITE_URL"])
