"""Unit tests for the FRITZ!Box Access Profiles select platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from custom_components.ha_fritzprofiles.const import DOMAIN
from custom_components.ha_fritzprofiles.coordinator import (
    HaFritzProfilesCoordinatorData,
)
from custom_components.ha_fritzprofiles.fritz_profile_switch import (
    FritzProfileDevice,
    FritzProfileDeviceData,
)
from custom_components.ha_fritzprofiles.select import (
    FritzDeviceProfileSelect,
    async_setup_entry,
)


def _build_coordinator() -> MagicMock:
    """Create a mock coordinator populated with sample devices and profiles."""
    raw = FritzProfileDeviceData(
        devices=[
            FritzProfileDevice(
                id="landevice935",
                name="AC-Büro",
                profile_id="filtprof3",
                mac="B4:43:0D:B5:2A:1D",
            ),
            FritzProfileDevice(
                id="landevice999",
                name="Tablet",
                profile_id="filtprof1",
                mac=None,
            ),
        ],
        profiles={
            "filtprof1": "Standard",
            "filtprof3": "Unbeschränkt",
        },
    )
    coordinator = MagicMock()
    coordinator.data = HaFritzProfilesCoordinatorData(raw)
    coordinator.client = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


async def test_select_setup_and_device_info() -> None:
    """Test entity creation, unique_id, MAC connection, and parent via_device."""
    coordinator = _build_coordinator()
    hass = MagicMock()
    hass.data = {DOMAIN: {"entry_123": coordinator}}
    entry = MagicMock()
    entry.entry_id = "entry_123"

    added_entities: list[FritzDeviceProfileSelect] = []
    await async_setup_entry(hass, entry, added_entities.extend)

    assert len(added_entities) == 2

    office_entity = added_entities[0]
    assert office_entity.unique_id == "fritzprofile_select_landevice935"
    assert office_entity.current_option == "Unbeschränkt"
    assert office_entity.options == ["Standard", "Unbeschränkt"]
    assert office_entity.device_info == {
        "identifiers": {(DOMAIN, "landevice935")},
        "connections": {("mac", "B4:43:0D:B5:2A:1D")},
        "name": "AC-Büro",
        "via_device": (DOMAIN, "entry_123"),
    }

    tablet_entity = added_entities[1]
    assert tablet_entity.device_info["connections"] == set()
    assert tablet_entity.current_option == "Standard"


async def test_select_option_updates_profile_and_refreshes() -> None:
    """Test selecting a profile calls client.set_device_profile and refreshes."""
    coordinator = _build_coordinator()
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))

    device = coordinator.data.devices_by_id["landevice935"]
    entity = FritzDeviceProfileSelect(
        coordinator=coordinator,
        entry_id="entry_123",
        device=device,
        profiles_by_id=coordinator.data.profiles_by_id,
        profiles_by_name=coordinator.data.profiles_by_name,
    )
    entity.hass = hass

    await entity.async_select_option("Standard")

    coordinator.client.set_device_profile.assert_called_once_with(
        "landevice935", "filtprof1"
    )
    coordinator.async_request_refresh.assert_awaited_once()


async def test_select_fallback_and_unknown_option() -> None:
    """Test fallback option when data is missing and ignoring unknown options."""
    coordinator = _build_coordinator()
    device = coordinator.data.devices_by_id["landevice935"]
    entity = FritzDeviceProfileSelect(
        coordinator=coordinator,
        entry_id="entry_123",
        device=device,
        profiles_by_id=coordinator.data.profiles_by_id,
        profiles_by_name=coordinator.data.profiles_by_name,
    )

    # Selecting an unknown profile name should log an error and not call the API
    await entity.async_select_option("NonExistentProfile")
    coordinator.client.set_device_profile.assert_not_called()

    # Missing coordinator data falls back to "Standard"
    coordinator.data = None
    assert entity.current_option == "Standard"
