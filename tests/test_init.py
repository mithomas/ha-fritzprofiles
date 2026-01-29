"""Test AVM FRITZ!Box Access Profiles setup process."""

from unittest.mock import AsyncMock, patch

from homeassistant.exceptions import ConfigEntryNotReady
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_fritzprofiles import (
    async_reload_entry,
    async_setup,
    async_setup_entry,
)
from custom_components.ha_fritzprofiles.const import DOMAIN
from custom_components.ha_fritzprofiles.coordinator import (
    HaFritzProfilesDataUpdateCoordinator,
)


@pytest.mark.asyncio
async def test_async_setup_returns_true(hass):
    """Test YAML setup shortcut."""
    assert await async_setup(hass, {}) is True


@pytest.mark.asyncio
async def test_setup_and_unload_entry(hass, mock_config, coordinator_data):
    """Test entry setup and unload via config entries."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=mock_config, entry_id="test")
    config_entry.add_to_hass(hass)

    with (
        patch("custom_components.ha_fritzprofiles.asyncio.sleep", new=AsyncMock()),
        patch(
            "custom_components.ha_fritzprofiles.coordinator.HaFritzProfilesDataUpdateCoordinator._async_update_data",
            new=AsyncMock(return_value=coordinator_data),
        ),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert isinstance(
        hass.data[DOMAIN][config_entry.entry_id], HaFritzProfilesDataUpdateCoordinator
    )
    assert hass.data[DOMAIN][config_entry.entry_id].platforms == ["select"]

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_setup_entry_not_ready(hass, mock_config):
    """Test ConfigEntryNotReady when refresh fails."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=mock_config, entry_id="test")
    config_entry.add_to_hass(hass)

    async def _failed_refresh(self):
        self.last_update_success = False

    with (
        patch("custom_components.ha_fritzprofiles.asyncio.sleep", new=AsyncMock()),
        patch.object(
            HaFritzProfilesDataUpdateCoordinator,
            "async_refresh",
            _failed_refresh,
        ),
    ):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, config_entry)


@pytest.mark.asyncio
async def test_async_reload_entry_calls_helpers(hass, mock_config):
    """Test reload calls unload and setup helpers."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=mock_config, entry_id="test")

    with (
        patch(
            "custom_components.ha_fritzprofiles.async_unload_entry",
            new=AsyncMock(return_value=True),
        ) as unload_entry,
        patch(
            "custom_components.ha_fritzprofiles.async_setup_entry",
            new=AsyncMock(return_value=True),
        ) as setup_entry,
    ):
        await async_reload_entry(hass, config_entry)

    unload_entry.assert_awaited_once_with(hass, config_entry)
    setup_entry.assert_awaited_once_with(hass, config_entry)
