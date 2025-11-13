"""Data update coordinator for Poltava Air Monitor."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    PoltavaAirMonitorApiClient,
    PoltavaAirMonitorApiConnectionError,
    PoltavaAirMonitorApiError,
)
from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POST_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class PoltavaAirMonitorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Poltava Air Monitor data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        session = async_get_clientsession(hass)
        self.api = PoltavaAirMonitorApiClient(session)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            # If coordinates are provided, find nearest post
            if CONF_LATITUDE in self.entry.data and CONF_LONGITUDE in self.entry.data:
                latitude = self.entry.data[CONF_LATITUDE]
                longitude = self.entry.data[CONF_LONGITUDE]
                
                nearest_post = await self.api.find_nearest_post(latitude, longitude)
                if not nearest_post:
                    raise UpdateFailed("No monitoring posts found")
                
                post_id = nearest_post["id"]
            else:
                # Use configured post ID
                post_id = self.entry.data[CONF_POST_ID]
            
            _LOGGER.debug("Fetching data for post_id: %s", post_id)
            
            # Get detailed data for the post
            data = await self.api.get_post_detail(post_id)
            
            _LOGGER.debug("Received data: %s", data)
            _LOGGER.info("Successfully fetched data for post %s with %d params", 
                        data.get("name", "Unknown"), 
                        len(data.get("params", [])))
            
            return data
            
        except PoltavaAirMonitorApiConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except PoltavaAirMonitorApiError as err:
            raise UpdateFailed(f"Error from API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

