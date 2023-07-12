"""Data update coordinator for AVM FRITZ!SmartHome devices."""
import logging

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .fritz_profile_switch import FritzProfileSwitch, FritzProfileDeviceData

from .const import DOMAIN


SCAN_INTERVAL = timedelta(hours=1)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class HaFritzProfilesDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: FritzProfileSwitch,
    ) -> None:
        """Initialize."""
        self.client = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)


    async def _async_update_data(self) -> FritzProfileDeviceData:
        """Update data via library."""
        try:
            _LOGGER.info("Load data")
            return await self.hass.async_add_executor_job(self.client.sync)
        except Exception as exception:
            _LOGGER.info("Loading failed")
            raise UpdateFailed() from exception