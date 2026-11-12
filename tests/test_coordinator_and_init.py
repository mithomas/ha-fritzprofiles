"""Unit tests for the coordinator and integration setup/unload lifecycle."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ha_fritzprofiles import (
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ha_fritzprofiles.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
)
from custom_components.ha_fritzprofiles.coordinator import (
    HaFritzProfilesDataUpdateCoordinator,
)
from custom_components.ha_fritzprofiles.fritz_profile_switch import (
    FritzProfileDevice,
    FritzProfileDeviceData,
)


async def test_coordinator_update_success() -> None:
    """Test coordinator fetches and indexes devices and profiles."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))

    client = MagicMock()
    client.load_device_profiles.return_value = FritzProfileDeviceData(
        devices=[
            FritzProfileDevice(
                id="landevice935",
                name="AC-Büro",
                profile_id="filtprof3",
                mac="B4:43:0D:B5:2A:1D",
            )
        ],
        profiles={"filtprof1": "Standard", "filtprof3": "Unbeschränkt"},
    )

    coordinator = HaFritzProfilesDataUpdateCoordinator(
        hass=hass,
        client=client,
        scan_interval=45,
    )
    data = await coordinator._async_update_data()

    assert "landevice935" in data.devices_by_id
    assert data.profiles_by_id["filtprof3"] == "Unbeschränkt"
    assert data.profiles_by_name["Unbeschränkt"] == "filtprof3"


async def test_coordinator_update_failure() -> None:
    """Test coordinator raises UpdateFailed when client raises an error."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=RuntimeError("Connection timeout")
    )
    client = MagicMock()

    coordinator = HaFritzProfilesDataUpdateCoordinator(hass=hass, client=client)

    with pytest.raises(Exception, match="Error communicating with FRITZ!Box"):
        await coordinator._async_update_data()


@patch(
    "custom_components.ha_fritzprofiles.HaFritzProfilesDataUpdateCoordinator."
    "async_config_entry_first_refresh",
    new_callable=AsyncMock,
)
@patch("custom_components.ha_fritzprofiles.dr.async_get")
@patch(
    "custom_components.ha_fritzprofiles.async_get_integration",
    new_callable=AsyncMock,
)
async def test_integration_setup_unload_and_reload(
    mock_get_integration: AsyncMock,
    mock_dr_get: MagicMock,
    mock_first_refresh: AsyncMock,
) -> None:
    """Test integration setup, entry setup, reload, and unload lifecycle."""
    assert await async_setup(MagicMock(), MagicMock()) is True

    mock_integration = MagicMock()
    mock_integration.name = "FRITZ!Box Access Profiles"
    mock_integration.version = "0.2.1"
    mock_get_integration.return_value = mock_integration

    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_reload = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry_abc"
    entry.data = {
        CONF_URL: "https://fritz.box",
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "secret",
    }
    entry.options = {CONF_SCAN_INTERVAL: 60}

    assert await async_setup_entry(hass, entry) is True
    assert DOMAIN in hass.data
    assert "entry_abc" in hass.data[DOMAIN]
    mock_dr_get.return_value.async_get_or_create.assert_called_once()
    mock_first_refresh.assert_awaited_once()
    hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
        entry, PLATFORMS
    )

    await async_reload_entry(hass, entry)
    hass.config_entries.async_reload.assert_awaited_once_with("entry_abc")

    assert await async_unload_entry(hass, entry) is True
    assert "entry_abc" not in hass.data[DOMAIN]
