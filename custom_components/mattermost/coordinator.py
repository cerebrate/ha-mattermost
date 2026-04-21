"""DataUpdateCoordinator for the Mattermost integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

# Number of consecutive failed health checks before we tear the entry down
# and let Home Assistant mark it as "Failed to set up" (with auto-retry).
FAILURE_THRESHOLD = 3


class MattermostDataUpdateCoordinator(DataUpdateCoordinator[bool]):
    """Coordinator that periodically verifies the Mattermost server is reachable."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({entry.title})",
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.entry = entry
        self.client = client
        self._consecutive_failures = 0
        self._reload_scheduled = False

    async def _async_update_data(self) -> bool:
        """Ping the Mattermost server to verify connectivity."""
        if not await self.client.test_connection():
            self._consecutive_failures += 1
            _LOGGER.warning(
                "Mattermost connectivity check failed (%d/%d)",
                self._consecutive_failures,
                FAILURE_THRESHOLD,
            )

            if (
                self._consecutive_failures >= FAILURE_THRESHOLD
                and not self._reload_scheduled
            ):
                # Reload the config entry. async_setup_entry will re-run and call
                # async_config_entry_first_refresh, which raises ConfigEntryNotReady
                # if the server is still down -- causing HA to show the integration
                # as "Failed to set up" with automatic retry.
                self._reload_scheduled = True
                _LOGGER.error(
                    "Mattermost server unreachable after %d consecutive checks; "
                    "reloading config entry",
                    self._consecutive_failures,
                )
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(self.entry.entry_id)
                )

            raise UpdateFailed("Mattermost server is unreachable")

        # Success -- reset the failure counter.
        self._consecutive_failures = 0
        return True
