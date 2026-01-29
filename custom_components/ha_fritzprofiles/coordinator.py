"""Data update coordinator for AVM FRITZ!Box device access profiles."""

from collections import Counter
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .fritz_profile_switch import (
    FritzProfileDevice,
    FritzProfileDeviceData,
    FritzProfileSwitch,
)

SCAN_INTERVAL = timedelta(minutes=60)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class HaFritzProfilesCoordinatorData:
    """Data class holding the complete set of device profile data."""

    devices_by_name: dict[str, FritzProfileDevice]
    profiles_by_id: dict[str, str]
    profiles_by_name: dict[str, str]

    def __init__(self, fritz_profile_device_data):
        # Remove duplicates per name since this is going to be our unique_id.
        counts = Counter(device.name for device in fritz_profile_device_data.devices)
        unique_devices_per_name = [
            device
            for device in fritz_profile_device_data.devices
            if counts[device.name] == 1
        ]
        self.devices_by_name = {
            device.name: device for device in unique_devices_per_name
        }

        self.profiles_by_id = fritz_profile_device_data.profiles_by_id
        self.profiles_by_name = {
            name: profile_id
            for profile_id, name in fritz_profile_device_data.profiles_by_id.items()
        }


class HaFritzProfilesDataUpdateCoordinator(DataUpdateCoordinator):
    """Manage updates for Fritz profile data."""

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
    ) -> FritzProfileDeviceData:
        """Fetch data from the Fritz client."""
        try:
            _LOGGER.info("Updating device profile data")
            data = HaFritzProfilesCoordinatorData(
                await self.hass.async_add_executor_job(self.client.load_device_profiles)
            )
            _LOGGER.info("Loaded %d unique devices", len(data.devices_by_name))
        except Exception as exception:
            _LOGGER.exception("Failed to update device profile data")
            raise UpdateFailed from exception
        else:
            return data
