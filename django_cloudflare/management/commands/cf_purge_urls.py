"""
Management command to purge specific URLs from Cloudflare cache.
"""

from django.core.management.base import BaseCommand

from django_cloudflare.client import get_client, CloudflareAPIError


class Command(BaseCommand):
    """Django management command to purge specific URLs."""

    help = "Purge specific URLs from the Cloudflare cache"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "urls",
            nargs="+",
            type=str,
            help="URLs to purge from cache",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be purged without actually purging",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        urls = options.get("urls", [])
        dry_run = options.get("dry_run", False)

        if not urls:
            self.stdout.write(
                self.style.ERROR("No URLs provided")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would purge {len(urls)} URLs:")
            )
            for url in urls:
                self.stdout.write(f"  - {url}")
            return

        try:
            client = get_client()
            result = client.purge_urls(urls)

            if result.get("success"):
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully purged {len(urls)} URLs")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Failed to purge URLs")
                )

        except CloudflareAPIError as e:
            self.stdout.write(
                self.style.ERROR(f"Error purging URLs: {e}")
            )
            raise
