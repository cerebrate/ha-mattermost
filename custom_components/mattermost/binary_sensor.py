"""Binary sensor platform for the Mattermost integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import MattermostDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Mattermost binary sensor."""
    coordinator: MattermostDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([MattermostConnectivitySensor(coordinator, entry)])


class MattermostConnectivitySensor(
    CoordinatorEntity[MattermostDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor that reports whether the Mattermost server is reachable."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_translation_key = "connectivity"
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: MattermostDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the connectivity sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connectivity"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Mattermost",
            configuration_url=entry.data.get(CONF_URL),
        )

    @property
    def is_on(self) -> bool:
        """Return True if the server was reachable on the last update."""
        return self.coordinator.last_update_success

    @property
    def available(self) -> bool:
        """Connectivity sensor itself is always available."""
        return True
