"""Config flow for Poltava Air Monitor integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import (
    PoltavaAirMonitorApiClient,
    PoltavaAirMonitorApiConnectionError,
    PoltavaAirMonitorApiError,
)
from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POST_ID,
    CONF_POST_NAME,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = PoltavaAirMonitorApiClient(session)
    
    # Try to fetch posts to verify API connectivity
    try:
        posts = await api.get_posts()
        if not posts:
            raise PoltavaAirMonitorApiError("No monitoring posts available")
    except PoltavaAirMonitorApiConnectionError as err:
        raise PoltavaAirMonitorApiConnectionError(
            "Cannot connect to Poltava Air Monitor API"
        ) from err
    
    return {"title": data[CONF_NAME], "posts": posts}


class PoltavaAirMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Poltava Air Monitor."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._posts: list[dict[str, Any]] = []
        self._name: str = DEFAULT_NAME

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                self._posts = info["posts"]
                self._name = user_input[CONF_NAME]
                return await self.async_step_station()
            except PoltavaAirMonitorApiConnectionError:
                errors["base"] = "cannot_connect"
            except PoltavaAirMonitorApiError:
                errors["base"] = "unknown"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle station selection step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            selection = user_input.get("selection")
            
            if selection == "list":
                return await self.async_step_station_list()
            elif selection == "coordinates":
                return await self.async_step_coordinates()
        
        schema = vol.Schema(
            {
                vol.Required("selection"): vol.In(
                    {
                        "list": "Select from list of stations",
                        "coordinates": "Find nearest to coordinates",
                    }
                ),
            }
        )
        
        return self.async_show_form(
            step_id="station",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_station_list(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle station list selection."""
        if user_input is not None:
            post_id = user_input[CONF_POST_ID]
            selected_post = next(
                (post for post in self._posts if post["id"] == post_id), None
            )
            
            if selected_post is None:
                return self.async_abort(reason="station_not_found")
            
            await self.async_set_unique_id(f"{DOMAIN}_{post_id}")
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"{self._name} - {selected_post['name']}",
                data={
                    CONF_NAME: self._name,
                    CONF_POST_ID: post_id,
                    CONF_POST_NAME: selected_post["name"],
                },
            )
        
        # Create schema with available posts
        post_options = {
            post["id"]: f"{post['name']} - {post['address']}"
            for post in self._posts
        }
        
        schema = vol.Schema(
            {
                vol.Required(CONF_POST_ID): vol.In(post_options),
            }
        )
        
        return self.async_show_form(
            step_id="station_list",
            data_schema=schema,
        )

    async def async_step_coordinates(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle coordinates input."""
        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]
            
            # Find nearest post
            session = async_get_clientsession(self.hass)
            api = PoltavaAirMonitorApiClient(session)
            
            try:
                nearest_post = await api.find_nearest_post(latitude, longitude)
                
                if nearest_post is None:
                    return self.async_abort(reason="no_stations_found")
                
                post_id = nearest_post["id"]
                
                await self.async_set_unique_id(f"{DOMAIN}_{post_id}_coords")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=f"{self._name} - {nearest_post['name']} (nearest)",
                    data={
                        CONF_NAME: self._name,
                        CONF_POST_ID: post_id,
                        CONF_POST_NAME: nearest_post["name"],
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                    },
                )
            except Exception:
                _LOGGER.exception("Error finding nearest post")
                return self.async_abort(reason="unknown")
        
        schema = vol.Schema(
            {
                vol.Required(CONF_LATITUDE): cv.latitude,
                vol.Required(CONF_LONGITUDE): cv.longitude,
            }
        )
        
        return self.async_show_form(
            step_id="coordinates",
            data_schema=schema,
            description_placeholders={
                "home_latitude": str(self.hass.config.latitude),
                "home_longitude": str(self.hass.config.longitude),
            },
        )

