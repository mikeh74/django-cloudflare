"""
Django settings for running tests.
"""

SECRET_KEY = "test-secret-key-for-django-cloudflare"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_cloudflare",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True

# Cloudflare settings for tests
CLOUDFLARE_API_TOKEN = "test-api-token"
CLOUDFLARE_ZONE_ID = "test-zone-id"
CLOUDFLARE_ENABLED = True
CLOUDFLARE_BACKGROUND_PURGE = False
CLOUDFLARE_SITE_URL = "https://example.com"
CLOUDFLARE_URL_DEPENDENCIES = {
    "testapp.blogpost": ["/blog/", "/"],
    "testapp.page": ["/"],
}
