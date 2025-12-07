"""
Tests for management commands.
"""

from io import StringIO
from unittest.mock import patch, MagicMock

from django.core.management import call_command
from django.test import TestCase


class CfPurgeAllCommandTestCase(TestCase):
    """Tests for cf_purge_all command."""

    @patch("django_cloudflare.management.commands.cf_purge_all.get_client")
    def test_purge_all_success(self, mock_get_client):
        """Test successful full cache purge."""
        mock_client = MagicMock()
        mock_client.purge_everything.return_value = {"success": True}
        mock_get_client.return_value = mock_client

        out = StringIO()
        call_command("cf_purge_all", stdout=out)

        self.assertIn("Successfully purged", out.getvalue())
        mock_client.purge_everything.assert_called_once()

    def test_purge_all_dry_run(self):
        """Test dry run mode."""
        out = StringIO()
        call_command("cf_purge_all", "--dry-run", stdout=out)

        self.assertIn("DRY RUN", out.getvalue())


class CfPurgeUrlsCommandTestCase(TestCase):
    """Tests for cf_purge_urls command."""

    @patch("django_cloudflare.management.commands.cf_purge_urls.get_client")
    def test_purge_urls_success(self, mock_get_client):
        """Test successful URL purge."""
        mock_client = MagicMock()
        mock_client.purge_urls.return_value = {"success": True}
        mock_get_client.return_value = mock_client

        out = StringIO()
        call_command(
            "cf_purge_urls",
            "https://example.com/page1",
            "https://example.com/page2",
            stdout=out,
        )

        self.assertIn("Successfully purged", out.getvalue())
        mock_client.purge_urls.assert_called_once()

    def test_purge_urls_dry_run(self):
        """Test dry run mode."""
        out = StringIO()
        call_command(
            "cf_purge_urls",
            "https://example.com/page1",
            "--dry-run",
            stdout=out,
        )

        self.assertIn("DRY RUN", out.getvalue())
        self.assertIn("https://example.com/page1", out.getvalue())


class CfVerifyTokenCommandTestCase(TestCase):
    """Tests for cf_verify_token command."""

    @patch("django_cloudflare.management.commands.cf_verify_token.get_client")
    def test_verify_token_success(self, mock_get_client):
        """Test successful token verification."""
        mock_client = MagicMock()
        mock_client.verify_token.return_value = {
            "success": True,
            "result": {"status": "active"},
        }
        mock_get_client.return_value = mock_client

        out = StringIO()
        call_command("cf_verify_token", stdout=out)

        self.assertIn("API token is valid", out.getvalue())
        mock_client.verify_token.assert_called_once()
