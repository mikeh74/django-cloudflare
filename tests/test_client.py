"""
Tests for the Cloudflare client.
"""

import json
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError

from django.test import TestCase, override_settings

from django_cloudflare.client import (
    CloudflareClient,
    CloudflareAPIError,
    get_client,
)


class CloudflareClientTestCase(TestCase):
    """Tests for CloudflareClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = CloudflareClient(
            api_token="test-token",
            zone_id="test-zone",
        )

    def test_init_with_explicit_values(self):
        """Test client initialization with explicit values."""
        client = CloudflareClient(
            api_token="my-token",
            zone_id="my-zone",
            base_url="https://api.example.com",
        )
        self.assertEqual(client.api_token, "my-token")
        self.assertEqual(client.zone_id, "my-zone")
        self.assertEqual(client.base_url, "https://api.example.com")

    @override_settings(
        CLOUDFLARE_API_TOKEN="settings-token",
        CLOUDFLARE_ZONE_ID="settings-zone",
    )
    def test_init_from_settings(self):
        """Test client initialization from settings."""
        client = CloudflareClient()
        self.assertEqual(client.api_token, "settings-token")
        self.assertEqual(client.zone_id, "settings-zone")

    def test_get_headers(self):
        """Test that headers are correctly formatted."""
        headers = self.client._get_headers()
        self.assertEqual(headers["Authorization"], "Bearer test-token")
        self.assertEqual(headers["Content-Type"], "application/json")

    @override_settings(CLOUDFLARE_ENABLED=True)
    @patch("django_cloudflare.client.urlopen")
    def test_purge_urls_success(self, mock_urlopen):
        """Test successful URL purge."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "success": True,
            "result": {"id": "purge-123"},
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        urls = ["https://example.com/page1", "https://example.com/page2"]
        result = self.client.purge_urls(urls)

        self.assertTrue(result["success"])
        mock_urlopen.assert_called_once()

        # Check the request was made correctly
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertIn("/zones/test-zone/purge_cache", request.full_url)

    @override_settings(CLOUDFLARE_ENABLED=True)
    @patch("django_cloudflare.client.urlopen")
    def test_purge_everything_success(self, mock_urlopen):
        """Test successful full cache purge."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "success": True,
            "result": {"id": "purge-456"},
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = self.client.purge_everything()

        self.assertTrue(result["success"])
        mock_urlopen.assert_called_once()

    @override_settings(CLOUDFLARE_ENABLED=True)
    @patch("django_cloudflare.client.urlopen")
    def test_api_error_handling(self, mock_urlopen):
        """Test handling of API errors."""
        error_body = json.dumps({
            "success": False,
            "errors": [{"code": 1001, "message": "Invalid zone identifier"}],
        }).encode("utf-8")

        mock_error = HTTPError(
            url="https://api.cloudflare.com",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=MagicMock(read=MagicMock(return_value=error_body)),
        )
        mock_urlopen.side_effect = mock_error

        with self.assertRaises(CloudflareAPIError) as context:
            self.client.purge_urls(["https://example.com/"])

        self.assertIn("Invalid zone identifier", str(context.exception))

    @override_settings(CLOUDFLARE_ENABLED=False)
    def test_purge_disabled(self):
        """Test that purge is skipped when disabled."""
        client = CloudflareClient()
        result = client.purge_urls(["https://example.com/"])

        # Should return success without making API call
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["id"], "disabled")

    @override_settings(CLOUDFLARE_ENABLED=True)
    def test_purge_empty_urls(self):
        """Test purging empty URL list."""
        result = self.client.purge_urls([])
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["id"], "empty")

    @patch("django_cloudflare.client.urlopen")
    def test_verify_token(self, mock_urlopen):
        """Test token verification."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "success": True,
            "result": {"status": "active"},
        }).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = self.client.verify_token()

        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["status"], "active")


class GetClientTestCase(TestCase):
    """Tests for get_client function."""

    def test_get_client_returns_singleton(self):
        """Test that get_client returns the same instance."""
        # Reset the singleton
        import django_cloudflare.client as client_module
        client_module._client = None

        client1 = get_client()
        client2 = get_client()

        self.assertIs(client1, client2)
