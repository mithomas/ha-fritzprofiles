"""Data update coordinator for AVM FRITZ!Box device access profiles."""
import logging
from collections import Counter
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN
from .fritz_profile_switch import FritzProfileDevice
from .fritz_profile_switch import FritzProfileDeviceData
from .fritz_profile_switch import FritzProfileSwitch


SCAN_INTERVAL = timedelta(minutes=60)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class HaFritzProfilesCoordinatorData:
    """Data class holding the complete set of device profile data."""

    devices_by_name: dict[str, FritzProfileDevice]
    profiles_by_id: dict[str, str]
    profiles_by_name: dict[str, str]

    def __init__(self, fritzProfileDeviceData):
        # remove duplicates per name since this is going to be our unique_id
        counts = Counter(
            getattr(device, "name") for device in fritzProfileDeviceData.devices
        )
        unique_devices_per_name = [
            device
            for device in fritzProfileDeviceData.devices
            if counts[getattr(device, "name")] == 1
        ]
        self.devices_by_name = {
            device.name: device for device in unique_devices_per_name
        }

        self.profiles_by_id = fritzProfileDeviceData.profiles_by_id
        self.profiles_by_name = {
            name: id for id, name in fritzProfileDeviceData.profiles_by_id.items()
        }


class HaFritzProfilesDataUpdateCoordinator(
    DataUpdateCoordinator
):  # pylint: disable=missing-class-docstring
    def __init__(
        self,
        hass: HomeAssistant,
        client: FritzProfileSwitch,
    ) -> None:
        self.client = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(
        self,
    ) -> FritzProfileDeviceData:  # pylint: disable=missing-function-docstring
        try:
            _LOGGER.info("Updating device profile data")
            data = HaFritzProfilesCoordinatorData(
                await self.hass.async_add_executor_job(self.client.load_device_profiles)
            )
            _LOGGER.info("Loaded %d unique devices", len(data.devices_by_name))
            return data
        except Exception as exception:
            _LOGGER.error(exception, exc_info=True)
            raise UpdateFailed() from exception
