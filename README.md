# django-cloudflare

A Django app for managing Cloudflare cache with automatic purging support.

## Features

- **Cloudflare API Client**: Uses API Tokens for secure authentication
- **Automatic Cache Purging**: Automatically purge cache when Django models are saved or deleted
- **Dependency-Aware Purging**: Configure URL dependencies so related pages are also purged
- **Background-Safe Operations**: Purge operations can run in background threads
- **Management Commands**: CLI commands for manual cache clearing
- **Configurable Settings**: Override settings in your Django project

## Installation

```bash
pip install django-cloudflare
```

Add `django_cloudflare` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    'django_cloudflare',
]
```

## Configuration

Add the following settings to your Django settings file:

```python
# Required settings
CLOUDFLARE_API_TOKEN = 'your-api-token'
CLOUDFLARE_ZONE_ID = 'your-zone-id'

# Optional settings
CLOUDFLARE_ENABLED = True  # Set to False to disable purging
CLOUDFLARE_SITE_URL = 'https://example.com'  # Your site URL
CLOUDFLARE_BACKGROUND_PURGE = True  # Run purges in background
CLOUDFLARE_PURGE_BATCH_SIZE = 30  # URLs per API request (max 30)
CLOUDFLARE_PURGE_DELAY_SECONDS = 0  # Delay before executing background purges

# URL dependencies - when a model changes, these URLs will also be purged
CLOUDFLARE_URL_DEPENDENCIES = {
    'blog.Post': ['/blog/', '/'],  # When a blog post changes, also purge blog index and home
    'pages.Page': ['/'],  # When a page changes, also purge home
}
```

## Usage

### Automatic Cache Purging

Register models to automatically purge their cache when saved or deleted:

```python
from django_cloudflare.signals import register_model
from myapp.models import BlogPost, Page

# Register models for automatic cache purging
register_model(BlogPost)
register_model(Page)

# Or with a custom URL function
def get_post_urls(post):
    return [
        post.get_absolute_url(),
        f'/category/{post.category.slug}/',
    ]

register_model(BlogPost, get_url_func=get_post_urls)
```

### Manual Cache Purging

```python
from django_cloudflare.purge import purge_urls, purge_everything, purge_model

# Purge specific URLs
purge_urls([
    'https://example.com/page1/',
    'https://example.com/page2/',
])

# Purge a model instance
purge_model(my_blog_post)

# Purge everything
purge_everything()
```

### Using the Client Directly

```python
from django_cloudflare.client import get_client

client = get_client()

# Purge specific URLs
client.purge_urls(['https://example.com/page/'])

# Purge everything
client.purge_everything()

# Purge by cache tags (Enterprise only)
client.purge_tags(['blog', 'news'])

# Verify your API token
result = client.verify_token()
```

## Management Commands

### Purge All Cache

```bash
python manage.py cf_purge_all
python manage.py cf_purge_all --dry-run
```

### Purge Specific URLs

```bash
python manage.py cf_purge_urls https://example.com/page1/ https://example.com/page2/
python manage.py cf_purge_urls https://example.com/page/ --dry-run
```

### Verify API Token

```bash
python manage.py cf_verify_token
```

## Creating a Cloudflare API Token

1. Go to the [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **My Profile** → **API Tokens**
3. Click **Create Token**
4. Use the **Edit zone DNS** template or create a custom token with:
   - **Permissions**: Zone → Cache Purge → Purge
   - **Zone Resources**: Include → Specific zone → Your zone
5. Copy the generated token to your Django settings

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT License
