"""
Tests for the purge service.
"""

import time
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from django_cloudflare.purge import (
    PurgeService,
    get_purge_service,
    purge_urls,
    purge_model,
    purge_everything,
)
from django_cloudflare.client import CloudflareClient


class MockModel:
    """Mock Django model for testing."""

    class _meta:
        app_label = "testapp"
        model_name = "blogpost"

    def __init__(self, url="/blog/my-post/"):
        self._url = url

    def get_absolute_url(self):
        return self._url


class PurgeServiceTestCase(TestCase):
    """Tests for PurgeService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=CloudflareClient)
        self.mock_client.purge_urls.return_value = {"success": True, "result": {}}
        self.mock_client.purge_everything.return_value = {"success": True, "result": {}}
        self.service = PurgeService(client=self.mock_client)

    @override_settings(CLOUDFLARE_BACKGROUND_PURGE=False)
    def test_purge_urls_synchronous(self):
        """Test synchronous URL purge."""
        urls = ["https://example.com/page1", "https://example.com/page2"]
        result = self.service.purge_urls(urls, background=False)

        self.mock_client.purge_urls.assert_called_once_with(urls)
        self.assertIsNotNone(result)

    @override_settings(CLOUDFLARE_BACKGROUND_PURGE=True, CLOUDFLARE_PURGE_DELAY_SECONDS=0.1)
    def test_purge_urls_background(self):
        """Test background URL purge."""
        urls = ["https://example.com/page1"]
        result = self.service.purge_urls(urls, background=True)

        # Background purge returns None immediately
        self.assertIsNone(result)

        # Wait for background purge to complete
        time.sleep(0.3)

        # Verify the purge was executed
        self.mock_client.purge_urls.assert_called()

    @override_settings(
        CLOUDFLARE_SITE_URL="https://example.com",
        CLOUDFLARE_URL_DEPENDENCIES={"testapp.blogpost": ["/blog/", "/"]},
    )
    def test_purge_model_with_dependencies(self):
        """Test purging a model with dependencies."""
        instance = MockModel(url="/blog/my-post/")
        self.service.purge_model(instance, include_dependencies=True)

        # Should purge the instance URL and dependency URLs
        self.mock_client.purge_urls.assert_called()
        call_args = self.mock_client.purge_urls.call_args[0][0]
        self.assertIn("https://example.com/blog/my-post/", call_args)
        self.assertIn("https://example.com/blog/", call_args)
        self.assertIn("https://example.com/", call_args)

    @override_settings(CLOUDFLARE_SITE_URL="https://example.com")
    def test_purge_model_without_dependencies(self):
        """Test purging a model without dependencies."""
        instance = MockModel(url="/page/")
        self.service.purge_model(instance, include_dependencies=False)

        call_args = self.mock_client.purge_urls.call_args[0][0]
        self.assertEqual(call_args, ["https://example.com/page/"])

    def test_purge_model_with_custom_url_func(self):
        """Test purging with a custom URL function."""
        instance = MockModel()

        def get_urls(obj):
            return ["https://custom.com/url1", "https://custom.com/url2"]

        self.service.purge_model(instance, get_url_func=get_urls, include_dependencies=False)

        call_args = self.mock_client.purge_urls.call_args[0][0]
        self.assertIn("https://custom.com/url1", call_args)
        self.assertIn("https://custom.com/url2", call_args)

    def test_purge_everything_synchronous(self):
        """Test synchronous full cache purge."""
        result = self.service.purge_everything(background=False)

        self.mock_client.purge_everything.assert_called_once()
        self.assertIsNotNone(result)

    @override_settings(CLOUDFLARE_PURGE_BATCH_SIZE=2)
    def test_purge_urls_batching(self):
        """Test that URLs are batched correctly."""
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
            "https://example.com/page4",
            "https://example.com/page5",
        ]

        self.service._do_purge_urls(urls)

        # Should be called 3 times with batch size 2
        self.assertEqual(self.mock_client.purge_urls.call_count, 3)


class ConvenienceFunctionsTestCase(TestCase):
    """Tests for convenience functions."""

    @patch("django_cloudflare.purge.get_purge_service")
    def test_purge_urls_function(self, mock_get_service):
        """Test purge_urls convenience function."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        purge_urls(["https://example.com/"])

        mock_service.purge_urls.assert_called_once()

    @patch("django_cloudflare.purge.get_purge_service")
    def test_purge_model_function(self, mock_get_service):
        """Test purge_model convenience function."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        instance = MockModel()
        purge_model(instance)

        mock_service.purge_model.assert_called_once()

    @patch("django_cloudflare.purge.get_purge_service")
    def test_purge_everything_function(self, mock_get_service):
        """Test purge_everything convenience function."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        purge_everything()

        mock_service.purge_everything.assert_called_once()
