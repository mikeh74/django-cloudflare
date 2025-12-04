"""
Cloudflare API client using API Tokens.

This module provides a client for interacting with the Cloudflare API
to manage cache purging operations.
"""

import logging
from typing import List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

from django_cloudflare import settings as cf_settings

logger = logging.getLogger(__name__)


class CloudflareAPIError(Exception):
    """Exception raised when Cloudflare API returns an error."""

    def __init__(self, message: str, errors: Optional[List[dict]] = None):
        super().__init__(message)
        self.errors = errors or []


class CloudflareClient:
    """
    Client for interacting with the Cloudflare API.

    Uses API Tokens for authentication (recommended over API keys).
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        zone_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the Cloudflare client.

        Args:
            api_token: Cloudflare API token. Defaults to settings.
            zone_id: Cloudflare zone ID. Defaults to settings.
            base_url: API base URL. Defaults to settings.
        """
        self.api_token = api_token or cf_settings.get_api_token()
        self.zone_id = zone_id or cf_settings.get_zone_id()
        self.base_url = base_url or cf_settings.get_api_base_url()

    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> dict:
        """
        Make a request to the Cloudflare API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.).
            endpoint: API endpoint (without base URL).
            data: Request body data.

        Returns:
            Response data as a dictionary.

        Raises:
            CloudflareAPIError: If the API returns an error.
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        request = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(request) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                error_data = json.loads(error_body)
                errors = error_data.get("errors", [])
                error_messages = [err.get("message", str(err)) for err in errors]
                raise CloudflareAPIError(
                    f"Cloudflare API error: {', '.join(error_messages)}", errors
                )
            except json.JSONDecodeError:
                raise CloudflareAPIError(f"Cloudflare API error: {error_body}")
        except URLError as e:
            raise CloudflareAPIError(f"Network error: {e.reason}")

        if not response_data.get("success", False):
            errors = response_data.get("errors", [])
            error_messages = [err.get("message", str(err)) for err in errors]
            raise CloudflareAPIError(
                f"Cloudflare API error: {', '.join(error_messages)}", errors
            )

        return response_data

    def purge_everything(self) -> dict:
        """
        Purge all cached content for the zone.

        Returns:
            API response data.

        Raises:
            CloudflareAPIError: If the API returns an error.
        """
        if not cf_settings.is_enabled():
            logger.info("Cloudflare purge is disabled. Skipping purge_everything.")
            return {"success": True, "result": {"id": "disabled"}}

        endpoint = f"/zones/{self.zone_id}/purge_cache"
        data = {"purge_everything": True}

        logger.info("Purging all cached content for zone %s", self.zone_id)
        return self._make_request("POST", endpoint, data)

    def purge_urls(self, urls: List[str]) -> dict:
        """
        Purge specific URLs from the cache.

        Args:
            urls: List of URLs to purge.

        Returns:
            API response data.

        Raises:
            CloudflareAPIError: If the API returns an error.
        """
        if not cf_settings.is_enabled():
            logger.info("Cloudflare purge is disabled. Skipping purge_urls.")
            return {"success": True, "result": {"id": "disabled"}}

        if not urls:
            logger.warning("No URLs provided for purging.")
            return {"success": True, "result": {"id": "empty"}}

        endpoint = f"/zones/{self.zone_id}/purge_cache"
        data = {"files": urls}

        logger.info("Purging %d URLs from cache: %s", len(urls), urls)
        return self._make_request("POST", endpoint, data)

    def purge_tags(self, tags: List[str]) -> dict:
        """
        Purge content by cache tags.

        Note: This requires an Enterprise plan.

        Args:
            tags: List of cache tags to purge.

        Returns:
            API response data.

        Raises:
            CloudflareAPIError: If the API returns an error.
        """
        if not cf_settings.is_enabled():
            logger.info("Cloudflare purge is disabled. Skipping purge_tags.")
            return {"success": True, "result": {"id": "disabled"}}

        if not tags:
            logger.warning("No tags provided for purging.")
            return {"success": True, "result": {"id": "empty"}}

        endpoint = f"/zones/{self.zone_id}/purge_cache"
        data = {"tags": tags}

        logger.info("Purging content by tags: %s", tags)
        return self._make_request("POST", endpoint, data)

    def purge_prefixes(self, prefixes: List[str]) -> dict:
        """
        Purge content by URL prefixes.

        Note: This requires an Enterprise plan.

        Args:
            prefixes: List of URL prefixes to purge.

        Returns:
            API response data.

        Raises:
            CloudflareAPIError: If the API returns an error.
        """
        if not cf_settings.is_enabled():
            logger.info("Cloudflare purge is disabled. Skipping purge_prefixes.")
            return {"success": True, "result": {"id": "disabled"}}

        if not prefixes:
            logger.warning("No prefixes provided for purging.")
            return {"success": True, "result": {"id": "empty"}}

        endpoint = f"/zones/{self.zone_id}/purge_cache"
        data = {"prefixes": prefixes}

        logger.info("Purging content by prefixes: %s", prefixes)
        return self._make_request("POST", endpoint, data)

    def verify_token(self) -> dict:
        """
        Verify the API token is valid.

        Returns:
            API response data with token status.

        Raises:
            CloudflareAPIError: If the API returns an error.
        """
        endpoint = "/user/tokens/verify"
        return self._make_request("GET", endpoint)


# Singleton instance for convenience
_client: Optional[CloudflareClient] = None


def get_client() -> CloudflareClient:
    """
    Get the default Cloudflare client instance.

    Returns:
        CloudflareClient instance.
    """
    global _client
    if _client is None:
        _client = CloudflareClient()
    return _client
