"""
Custom integration to integrate AVM FRITZ!Box Access Profiles with Home Assistant.

For more details about this integration, please refer to
https://github.com/mithomas/ha-fritzprofiles
"""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .coordinator import HaFritzProfilesDataUpdateCoordinator
from .fritz_profile_switch import FritzProfileSwitch

from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import CONF_URL
from .const import DOMAIN
from .const import PLATFORMS
from .const import STARTUP_MESSAGE

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    url = entry.data.get(CONF_URL)

    coordinator = HaFritzProfilesDataUpdateCoordinator(hass, client=FritzProfileSwitch(url, username, password))
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
