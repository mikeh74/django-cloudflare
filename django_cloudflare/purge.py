"""
Cache purge service with dependency-aware logic.

This module provides high-level functions for purging cache with support
for dependency tracking and background operations.
"""

import logging
import threading
from typing import Callable, List, Optional, Set

from django_cloudflare import settings as cf_settings
from django_cloudflare.client import CloudflareClient, CloudflareAPIError, get_client

logger = logging.getLogger(__name__)


class PurgeService:
    """
    Service for managing cache purge operations.

    Provides dependency-aware purging and background operation support.
    """

    def __init__(self, client: Optional[CloudflareClient] = None):
        """
        Initialize the purge service.

        Args:
            client: Cloudflare client instance. Uses default if not provided.
        """
        self.client = client or get_client()
        self._pending_urls: Set[str] = set()
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None

    def _get_url_dependencies(self, model_identifier: str) -> List[str]:
        """
        Get URL dependencies for a model.

        Args:
            model_identifier: Model identifier in format 'app_label.ModelName'.

        Returns:
            List of URL patterns that depend on this model.
        """
        dependencies = cf_settings.get_url_dependencies()
        return dependencies.get(model_identifier, [])

    def _build_full_url(self, path: str) -> str:
        """
        Build a full URL from a path.

        Args:
            path: URL path (e.g., '/blog/').

        Returns:
            Full URL with site domain.
        """
        site_url = cf_settings.get_site_url().rstrip("/")
        if not site_url:
            return path
        return f"{site_url}{path}"

    def purge_urls(
        self, urls: List[str], background: Optional[bool] = None
    ) -> Optional[dict]:
        """
        Purge specific URLs from cache.

        Args:
            urls: List of URLs to purge.
            background: Whether to run in background. Defaults to settings.

        Returns:
            API response if synchronous, None if background.
        """
        if background is None:
            background = cf_settings.use_background_purge()

        if background:
            self._schedule_background_purge(urls)
            return None

        return self._do_purge_urls(urls)

    def _do_purge_urls(self, urls: List[str]) -> dict:
        """
        Actually perform the URL purge.

        Args:
            urls: List of URLs to purge.

        Returns:
            API response.
        """
        batch_size = cf_settings.get_purge_batch_size()
        results = []

        # Cloudflare limits to 30 URLs per request
        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            try:
                result = self.client.purge_urls(batch)
                results.append(result)
            except CloudflareAPIError as e:
                logger.error("Failed to purge URLs: %s", e)
                raise

        return {"success": True, "results": results}

    def _schedule_background_purge(self, urls: List[str]) -> None:
        """
        Schedule URLs for background purging.

        Batches URLs and purges after a delay to combine multiple requests.

        Args:
            urls: List of URLs to purge.
        """
        with self._lock:
            self._pending_urls.update(urls)

            # Cancel existing timer if any
            if self._timer is not None:
                self._timer.cancel()

            # Schedule new purge
            delay = cf_settings.get_purge_delay_seconds()
            self._timer = threading.Timer(delay, self._execute_background_purge)
            self._timer.daemon = True
            self._timer.start()

        logger.debug("Scheduled background purge for %d URLs", len(urls))

    def _execute_background_purge(self) -> None:
        """Execute the pending background purge."""
        with self._lock:
            urls = list(self._pending_urls)
            self._pending_urls.clear()
            self._timer = None

        if urls:
            try:
                self._do_purge_urls(urls)
                logger.info("Background purge completed for %d URLs", len(urls))
            except CloudflareAPIError as e:
                logger.error("Background purge failed: %s", e)

    def purge_model(
        self,
        instance,
        include_dependencies: bool = True,
        get_url_func: Optional[Callable] = None,
    ) -> Optional[dict]:
        """
        Purge cache for a model instance.

        Args:
            instance: Django model instance.
            include_dependencies: Whether to include dependent URLs.
            get_url_func: Custom function to get URL(s) for the instance.

        Returns:
            API response if synchronous, None if background.
        """
        urls = []

        # Get the instance's URL
        if get_url_func:
            instance_urls = get_url_func(instance)
            if isinstance(instance_urls, str):
                instance_urls = [instance_urls]
            urls.extend(instance_urls)
        elif hasattr(instance, "get_absolute_url"):
            try:
                url = instance.get_absolute_url()
                urls.append(self._build_full_url(url))
            except Exception as e:
                logger.warning("Failed to get URL for %s: %s", instance, e)

        # Get dependency URLs
        if include_dependencies:
            model_identifier = f"{instance._meta.app_label}.{instance._meta.model_name}"
            dep_urls = self._get_url_dependencies(model_identifier)
            for url in dep_urls:
                urls.append(self._build_full_url(url))

        if not urls:
            logger.debug("No URLs to purge for %s", instance)
            return None

        return self.purge_urls(urls)

    def purge_everything(self, background: Optional[bool] = None) -> Optional[dict]:
        """
        Purge all cached content.

        Args:
            background: Whether to run in background.

        Returns:
            API response if synchronous, None if background.
        """
        if background is None:
            background = cf_settings.use_background_purge()

        if background:
            thread = threading.Thread(target=self._do_purge_everything)
            thread.daemon = True
            thread.start()
            return None

        return self._do_purge_everything()

    def _do_purge_everything(self) -> dict:
        """Actually perform the full cache purge."""
        try:
            result = self.client.purge_everything()
            logger.info("Full cache purge completed")
            return result
        except CloudflareAPIError as e:
            logger.error("Full cache purge failed: %s", e)
            raise


# Singleton instance
_service: Optional[PurgeService] = None


def get_purge_service() -> PurgeService:
    """
    Get the default purge service instance.

    Returns:
        PurgeService instance.
    """
    global _service
    if _service is None:
        _service = PurgeService()
    return _service


# Convenience functions
def purge_urls(urls: List[str], background: Optional[bool] = None) -> Optional[dict]:
    """
    Purge specific URLs from cache.

    Args:
        urls: List of URLs to purge.
        background: Whether to run in background.

    Returns:
        API response if synchronous, None if background.
    """
    return get_purge_service().purge_urls(urls, background)


def purge_model(
    instance,
    include_dependencies: bool = True,
    get_url_func: Optional[Callable] = None,
) -> Optional[dict]:
    """
    Purge cache for a model instance.

    Args:
        instance: Django model instance.
        include_dependencies: Whether to include dependent URLs.
        get_url_func: Custom function to get URL(s) for the instance.

    Returns:
        API response if synchronous, None if background.
    """
    return get_purge_service().purge_model(instance, include_dependencies, get_url_func)


def purge_everything(background: Optional[bool] = None) -> Optional[dict]:
    """
    Purge all cached content.

    Args:
        background: Whether to run in background.

    Returns:
        API response if synchronous, None if background.
    """
    return get_purge_service().purge_everything(background)
