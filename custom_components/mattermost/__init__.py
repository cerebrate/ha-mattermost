"""The Mattermost integration."""

from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType

from .api import MattermostHTTPClient, normalize_base_url
from .const import DATA_CLIENT, DATA_COORDINATOR, DATA_HASS_CONFIG, DOMAIN
from .coordinator import MattermostDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR]

# Config entry only - no YAML configuration supported
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Mattermost component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mattermost from a config entry."""
    config = entry.data

    try:
        url = normalize_base_url(config[CONF_URL])

        # Create HTTP client
        client = MattermostHTTPClient(hass, url, config[CONF_API_KEY])

        # Set up the coordinator and perform the initial connectivity check.
        # async_config_entry_first_refresh raises ConfigEntryNotReady on failure.
        coordinator = MattermostDataUpdateCoordinator(hass, entry, client)
        await coordinator.async_config_entry_first_refresh()

    except ConfigEntryNotReady:
        raise
    except Exception as err:
        _LOGGER.error("Failed to connect to Mattermost: %s", err)
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
        DATA_HASS_CONFIG: config,
    }

    # Set up the binary_sensor platform via the standard config-entry mechanism.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up notify platform using discovery (legacy notify pattern).
    discovery_data = hass.data[DOMAIN][entry.entry_id].copy()
    discovery_data[CONF_NAME] = "mattermost"

    await discovery.async_load_platform(
        hass,
        Platform.NOTIFY,
        DOMAIN,
        discovery_data,
        config,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
