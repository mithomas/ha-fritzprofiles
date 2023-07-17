"""
Custom integration for AVM FRITZ!Box device access profiles in Home Assistant.

For more details about this integration, please see https://github.com/mithomas/ha-fritzprofiles
"""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_PASSWORD
from .const import CONF_URL
from .const import CONF_USERNAME
from .const import DOMAIN
from .const import PLATFORMS
from .const import VERSION
from .coordinator import HaFritzProfilesDataUpdateCoordinator
from .fritz_profile_switch import FritzProfileSwitch

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info("Starting up custom integration ha-fritzprofiles %s", VERSION)

    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    url = entry.data.get(CONF_URL)

    coordinator = HaFritzProfilesDataUpdateCoordinator(
        hass, client=FritzProfileSwitch(url, username, password)
    )

    # Wait a bit so login doesn't clash with the AVM FRITZ!SmartHome integration (which is likely
    # also installed) - running at the same time causes the other one to timeout during HA start-up,
    # requiring manual intervention. (This means longer setup and start-up time here.)
    await asyncio.sleep(10)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
