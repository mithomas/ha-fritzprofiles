"""Select platform for ha_fritzprofiles backed by DataUpdateCoordinator."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HaFritzProfilesDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .fritz_profile_switch import FritzProfileDevice

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the FRITZ!Box Profile select entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    data = coordinator.data
    devices = list(data.devices_by_id.values())
    profiles_by_id = data.profiles_by_id
    profiles_by_name = data.profiles_by_name

    entities = [
        FritzDeviceProfileSelect(
            coordinator=coordinator,
            entry_id=entry.entry_id,
            device=device,
            profiles_by_id=profiles_by_id,
            profiles_by_name=profiles_by_name,
        )
        for device in devices
    ]

    async_add_entities(entities)


class FritzDeviceProfileSelect(
    CoordinatorEntity[HaFritzProfilesDataUpdateCoordinator], SelectEntity
):
    """Representation of a network device internet access profile selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "internet_profile"

    def __init__(
        self,
        coordinator: HaFritzProfilesDataUpdateCoordinator,
        entry_id: str,
        device: FritzProfileDevice,
        profiles_by_id: dict[str, str],
        profiles_by_name: dict[str, str],
    ) -> None:
        """Initialize the profile select entity."""
        super().__init__(coordinator)
        self._device_id = device.id
        self._profiles_by_id = profiles_by_id
        self._profiles_by_name = profiles_by_name

        # Unique ID based on physical landevice UID
        self._attr_unique_id = f"fritzprofile_select_{device.id}"
        self._attr_options = list(profiles_by_id.values())

        # Link entity to HA device registry (merges with existing MAC devices)
        connections: set[tuple[str, str]] = set()
        if device.mac:
            connections.add((CONNECTION_NETWORK_MAC, device.mac))

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.id)},
            connections=connections,
            name=device.name,
            via_device=(DOMAIN, entry_id),
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently active profile name from coordinator data."""
        if (
            self.coordinator.data
            and self._device_id in self.coordinator.data.devices_by_id
        ):
            dev = self.coordinator.data.devices_by_id[self._device_id]
            return self._profiles_by_id.get(dev.profile_id, "Standard")
        return "Standard"

    async def async_select_option(self, option: str) -> None:
        """Change the access profile on the FRITZ!Box and refresh coordinator state."""
        profile_id = self._profiles_by_name.get(option)
        if not profile_id:
            _LOGGER.error("Unknown profile selected: %s", option)
            return

        await self.hass.async_add_executor_job(
            self.coordinator.client.set_device_profile,
            self._device_id,
            profile_id,
        )

        # Trigger immediate background coordinator refresh
        await self.coordinator.async_request_refresh()
