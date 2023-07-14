"""HaFritzProfilesEntity class"""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HaFritzProfilesEntity(coordinator, device) for device in coordinator.data.devices_by_name.values()])


class HaFritzProfilesEntity(CoordinatorEntity, SelectEntity):
    """SelectEntity wrapping around a fritz profile device."""

    def __init__(self, coordinator, device):
        super().__init__(coordinator)

        self.device = None
        self._attr_current_option = None
        self._attr_options = None

        self._update_values(device)


    @property
    def unique_id(self): # pylint: disable=missing-function-docstring
        return self.device.name #add a comment here why on earth


    @property
    def name(self): # pylint: disable=missing-function-docstring
        return self.device.name


    @property
    def icon(self): # pylint: disable=missing-function-docstring
        return "mdi:web"


    def _update_values(self, device) -> None:
        self.device = device

        self._attr_current_option = self.coordinator.data.profiles_by_id[self.device.profile_id]
        self._attr_options = list(self.coordinator.data.profiles_by_id.values())


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_values(self.coordinator.data.devices_by_name[self.unique_id])
        self.async_write_ha_state()


    async def async_select_option(self, profile: str) -> None: # pylint: disable=missing-function-docstring
        """Handles a new selection.

        Performs a refresh first as device id might have changed after a new profile has been set outside of HA.
        (Device ids are generally 'landeviceNNNN' when using the standard profile and 'userNNNN' when using a custom one.)
        """
        _LOGGER.info("Selected profile '%s' for device %s", profile, self.unique_id)
        await self.coordinator.async_request_refresh()
        await self.coordinator.hass.async_add_executor_job(self.coordinator.client.set_device_profile, self.device.id, self.coordinator.data.profiles_by_name[profile])

        self._attr_current_option = profile
        self.async_write_ha_state()
