"""Test coordinator behavior."""

from unittest.mock import AsyncMock, MagicMock

from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest

from custom_components.ha_fritzprofiles.coordinator import (
    HaFritzProfilesCoordinatorData,
    HaFritzProfilesDataUpdateCoordinator,
)
from custom_components.ha_fritzprofiles.fritz_profile_switch import (
    FritzProfileDevice,
    FritzProfileDeviceData,
)


def test_coordinator_data_deduplicates_devices():
    """Test duplicate device names are removed."""
    devices = [
        FritzProfileDevice(id="id1", name="Phone", profile_id="profile1"),
        FritzProfileDevice(id="id2", name="Phone", profile_id="profile2"),
        FritzProfileDevice(id="id3", name="Laptop", profile_id="profile1"),
    ]
    profiles = {"profile1": "Standard", "profile2": "Limited"}
    raw_data = FritzProfileDeviceData(devices, profiles)

    data = HaFritzProfilesCoordinatorData(raw_data)

    assert data.devices_by_name == {"Laptop": devices[2]}
    assert data.profiles_by_id == profiles
    assert data.profiles_by_name == {"Standard": "profile1", "Limited": "profile2"}


def test_coordinator_data_empty():
    """Test empty data yields empty maps."""
    raw_data = FritzProfileDeviceData([], {})

    data = HaFritzProfilesCoordinatorData(raw_data)

    assert data.devices_by_name == {}
    assert data.profiles_by_id == {}
    assert data.profiles_by_name == {}


def test_coordinator_data_all_duplicates_removed():
    """Test all devices removed when names are duplicated."""
    devices = [
        FritzProfileDevice(id="id1", name="Phone", profile_id="profile1"),
        FritzProfileDevice(id="id2", name="Phone", profile_id="profile2"),
    ]
    profiles = {"profile1": "Standard", "profile2": "Limited"}
    raw_data = FritzProfileDeviceData(devices, profiles)

    data = HaFritzProfilesCoordinatorData(raw_data)

    assert data.devices_by_name == {}


@pytest.mark.asyncio
async def test_coordinator_update_success(hass, fritz_device_data):
    """Test coordinator update returns wrapped data."""
    client = MagicMock()
    coordinator = HaFritzProfilesDataUpdateCoordinator(hass, client=client)
    hass.async_add_executor_job = AsyncMock(return_value=fritz_device_data)

    data = await coordinator._async_update_data()  # noqa: SLF001

    assert isinstance(data, HaFritzProfilesCoordinatorData)
    assert "iPhone" in data.devices_by_name
    assert data.devices_by_name["iPhone"].profile_id == "profile1"
    hass.async_add_executor_job.assert_awaited_once_with(client.load_device_profiles)


@pytest.mark.asyncio
async def test_coordinator_update_failure_logs(hass, caplog):
    """Test coordinator update errors are wrapped."""
    client = MagicMock()
    coordinator = HaFritzProfilesDataUpdateCoordinator(hass, client=client)
    hass.async_add_executor_job = AsyncMock(side_effect=Exception("boom"))

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()  # noqa: SLF001

    assert "Failed to update device profile data" in caplog.text
