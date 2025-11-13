"""API client for Poltava Air Monitor."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout

from .const import API_BASE_URL, API_POST_DETAIL_ENDPOINT, API_POSTS_ENDPOINT

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class PoltavaAirMonitorApiError(Exception):
    """Exception to indicate a general API error."""


class PoltavaAirMonitorApiConnectionError(PoltavaAirMonitorApiError):
    """Exception to indicate a connection error."""


class PoltavaAirMonitorApiClient:
    """API client for Poltava Air Monitor."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._session = session

    async def get_posts(self) -> list[dict[str, Any]]:
        """Get all monitoring posts summary."""
        url = f"{API_BASE_URL}{API_POSTS_ENDPOINT}"
        return await self._api_request(url)

    async def get_post_detail(self, post_id: int) -> dict[str, Any]:
        """Get detailed information for a specific post."""
        url = f"{API_BASE_URL}{API_POST_DETAIL_ENDPOINT.format(post_id=post_id)}"
        data = await self._api_request(url)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            raise PoltavaAirMonitorApiError(f"No data returned for post {post_id}")
        
        return data[0]

    async def find_nearest_post(
        self, latitude: float, longitude: float
    ) -> dict[str, Any] | None:
        """Find the nearest monitoring post to given coordinates."""
        posts = await self.get_posts()
        
        if not posts:
            return None
        
        def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculate simple Euclidean distance."""
            return ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5
        
        nearest_post = min(
            posts,
            key=lambda p: distance(latitude, longitude, p["lat"], p["lng"]),
        )
        
        return nearest_post

    async def _api_request(self, url: str) -> Any:
        """Make a request to the API."""
        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                response = await self._session.get(url)
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to Poltava Air Monitor API: %s", err)
            raise PoltavaAirMonitorApiConnectionError(
                f"Error connecting to API: {err}"
            ) from err
        except TimeoutError as err:
            _LOGGER.error("Timeout connecting to Poltava Air Monitor API: %s", err)
            raise PoltavaAirMonitorApiConnectionError(
                f"Timeout connecting to API: {err}"
            ) from err
        except Exception as err:
            _LOGGER.error("Unexpected error from Poltava Air Monitor API: %s", err)
            raise PoltavaAirMonitorApiError(
                f"Unexpected error from API: {err}"
            ) from err

