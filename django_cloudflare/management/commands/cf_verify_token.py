"""
Management command to verify Cloudflare API token.
"""

from django.core.management.base import BaseCommand

from django_cloudflare.client import get_client, CloudflareAPIError
from django_cloudflare import settings as cf_settings


class Command(BaseCommand):
    """Django management command to verify Cloudflare configuration."""

    help = "Verify Cloudflare API token and configuration"

    def handle(self, *args, **options):
        """Execute the command."""
        # Check if settings are configured
        if not cf_settings.get_api_token():
            self.stdout.write(
                self.style.ERROR("CLOUDFLARE_API_TOKEN is not configured")
            )
            return

        if not cf_settings.get_zone_id():
            self.stdout.write(
                self.style.ERROR("CLOUDFLARE_ZONE_ID is not configured")
            )
            return

        self.stdout.write("Verifying Cloudflare API token...")

        try:
            client = get_client()
            result = client.verify_token()

            if result.get("success"):
                self.stdout.write(
                    self.style.SUCCESS("API token is valid")
                )

                # Show token details if available
                token_result = result.get("result", {})
                status = token_result.get("status", "unknown")
                self.stdout.write(f"  Status: {status}")
            else:
                self.stdout.write(
                    self.style.ERROR("API token verification failed")
                )

        except CloudflareAPIError as e:
            self.stdout.write(
                self.style.ERROR(f"Error verifying token: {e}")
            )
            raise
