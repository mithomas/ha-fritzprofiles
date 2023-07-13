"""Data update coordinator for AVM FRITZ!Box device access profiles."""
import logging

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .fritz_profile_switch import FritzProfileSwitch, FritzProfileDeviceData

from .const import DOMAIN


SCAN_INTERVAL = timedelta(hours=1)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class HaFritzProfilesDataUpdateCoordinator(DataUpdateCoordinator): # pylint: disable=missing-class-docstring

    def __init__(
        self,
        hass: HomeAssistant,
        client: FritzProfileSwitch,
    ) -> None:
        self.client = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)


    async def _async_update_data(self) -> FritzProfileDeviceData: # pylint: disable=missing-function-docstring
        try:
            _LOGGER.info("Updating device profile data")
            return await self.hass.async_add_executor_job(self.client.load_device_profiles)
        except Exception as exception:
            _LOGGER.error(exception, exc_info=True)
            raise UpdateFailed() from exception