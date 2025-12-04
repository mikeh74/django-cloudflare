"""
Management command to purge the entire Cloudflare cache.
"""

from django.core.management.base import BaseCommand

from django_cloudflare.client import get_client, CloudflareAPIError


class Command(BaseCommand):
    """Django management command to purge all cached content."""

    help = "Purge the entire Cloudflare cache for the configured zone"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be purged without actually purging",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN: Would purge entire cache")
            )
            return

        try:
            client = get_client()
            result = client.purge_everything()

            if result.get("success"):
                self.stdout.write(
                    self.style.SUCCESS("Successfully purged entire cache")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Failed to purge cache")
                )

        except CloudflareAPIError as e:
            self.stdout.write(
                self.style.ERROR(f"Error purging cache: {e}")
            )
            raise
