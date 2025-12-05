"""
Tests for Django signals integration.
"""

from unittest.mock import patch, MagicMock

from django.test import TestCase

from django_cloudflare.signals import (
    register_model,
    unregister_model,
    is_model_registered,
    get_registered_models,
)


class MockModel:
    """Mock Django model for testing."""

    class _meta:
        app_label = "testapp"
        model_name = "mockmodel"


class SignalsTestCase(TestCase):
    """Tests for signal handling."""

    def tearDown(self):
        """Clean up after tests."""
        # Unregister any registered models
        for model in get_registered_models():
            unregister_model(model)

    def test_register_model(self):
        """Test registering a model."""
        self.assertFalse(is_model_registered(MockModel))

        register_model(MockModel)

        self.assertTrue(is_model_registered(MockModel))

    def test_unregister_model(self):
        """Test unregistering a model."""
        register_model(MockModel)
        self.assertTrue(is_model_registered(MockModel))

        unregister_model(MockModel)

        self.assertFalse(is_model_registered(MockModel))

    def test_get_registered_models(self):
        """Test getting list of registered models."""
        register_model(MockModel)

        models = get_registered_models()

        self.assertIn(MockModel, models)

    @patch("django_cloudflare.signals.purge_model")
    def test_signal_triggers_purge_on_save(self, mock_purge):
        """Test that saving a model triggers cache purge."""
        from django.db.models.signals import post_save

        register_model(MockModel)

        instance = MockModel()

        # Simulate post_save signal
        post_save.send(sender=MockModel, instance=instance, created=True)

        mock_purge.assert_called_once()

    @patch("django_cloudflare.signals.purge_model")
    def test_signal_triggers_purge_on_delete(self, mock_purge):
        """Test that deleting a model triggers cache purge."""
        from django.db.models.signals import post_delete

        register_model(MockModel)

        instance = MockModel()

        # Simulate post_delete signal
        post_delete.send(sender=MockModel, instance=instance)

        mock_purge.assert_called_once()

    @patch("django_cloudflare.signals.purge_model")
    def test_custom_url_func(self, mock_purge):
        """Test using a custom URL function."""
        from django.db.models.signals import post_save

        def get_custom_urls(obj):
            return ["https://custom.com/url"]

        register_model(MockModel, get_url_func=get_custom_urls)

        instance = MockModel()
        post_save.send(sender=MockModel, instance=instance, created=True)

        # Verify the custom function config was passed
        call_kwargs = mock_purge.call_args[1]
        self.assertEqual(call_kwargs["get_url_func"], get_custom_urls)
