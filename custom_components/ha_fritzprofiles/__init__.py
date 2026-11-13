"""Custom integration to integrate FRITZ!Box Access Profiles with Home Assistant."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, Platform
from homeassistant.helpers import device_registry as dr
from homeassistant.loader import async_get_integration

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, STARTUP_MESSAGE
from .coordinator import HaFritzProfilesDataUpdateCoordinator
from .fritz_profile_switch import FritzProfileSwitch

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.core_config import Config

PLATFORMS: list[Platform] = [Platform.SELECT]

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        integration = await async_get_integration(hass, DOMAIN)
        _LOGGER.info(
            STARTUP_MESSAGE,
            integration.name,
            integration.version,
        )

    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]
    url: str = entry.data[CONF_URL]
    scan_interval: int = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    client = FritzProfileSwitch(url=url, user=username, password=password)

    # Register the FRITZ!Box itself as parent hub device in the device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="FRITZ!",
        model="FRITZ!Box",
        name=f"FRITZ!Box ({url})",
        configuration_url=url,
    )

    coordinator = HaFritzProfilesDataUpdateCoordinator(
        hass=hass,
        client=client,
        scan_interval=scan_interval,
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
