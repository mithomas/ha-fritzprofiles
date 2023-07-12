"""HaFritzProfilesEntity class"""
import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.select import SelectEntity

from .fritz_switch_profiles import FritzProfileSwitch

from .const import ATTRIBUTION
from .const import DOMAIN
from .const import NAME
from .const import VERSION
from .const import ICON

_LOGGER: logging.Logger = logging.getLogger(__package__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HaFritzProfilesEntity(coordinator, device) for device in coordinator.client.devices.values()])


class HaFritzProfilesEntity(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator)

        self.device = device

        self._attr_current_option = self.coordinator.client.profiles[self.device['profile']]
        self._attr_options = list(self.coordinator.client.profiles.values())

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return self.device['id']

    @property
    def name(self):
        """Return the name of the switch."""
        return self.device['name']

    @property
    def icon(self):
        """Return the icon of this switch."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "attribution": ATTRIBUTION,
            "id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        fps = self.coordinator.client
        fps.login()
