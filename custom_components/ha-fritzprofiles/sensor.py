"""Sensor platform for AVM FRITZ!Box Access Profiles."""
from .const import DEFAULT_NAME
from .const import DOMAIN
from .const import ICON
from .const import SENSOR
from .entity import HaProfilesEntity


async def async_setup_entry(hass, entry, async_add_devices):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices([HaProfilesSensor(coordinator, entry)])


class HaProfilesSensor(HaProfilesEntity):
    """https://github.com/mithomas/ha-fritzprofiles Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{SENSOR}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("body")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "https://github.com/mithomas/ha-fritzprofiles__custom_device_class"
