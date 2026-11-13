"""DataUpdateCoordinator for ha_fritzprofiles."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .fritz_profile_switch import (
        FritzProfileDevice,
        FritzProfileDeviceData,
        FritzProfileSwitch,
    )

_LOGGER: logging.Logger = logging.getLogger(__package__)


class HaFritzProfilesCoordinatorData:
    """Structured data provided by the coordinator to entities."""

    def __init__(self, raw_data: FritzProfileDeviceData) -> None:
        """Index devices by UID and profiles by UID and display name."""
        self.devices_by_id: dict[str, FritzProfileDevice] = {
            dev.id: dev for dev in raw_data.devices
        }
        self.profiles_by_id: dict[str, str] = dict(raw_data.profiles_by_id)
        self.profiles_by_name: dict[str, str] = {
            name: uid for uid, name in raw_data.profiles_by_id.items()
        }


class HaFritzProfilesDataUpdateCoordinator(
    DataUpdateCoordinator[HaFritzProfilesCoordinatorData]
):
    """Class to manage fetching FRITZ!Box device and profile data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: FritzProfileSwitch,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> HaFritzProfilesCoordinatorData:
        """Fetch latest device and profile data from FRITZ!Box."""
        try:
            raw_data = await self.hass.async_add_executor_job(
                self.client.load_device_profiles
            )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with FRITZ!Box: {err}") from err

        return HaFritzProfilesCoordinatorData(raw_data)
