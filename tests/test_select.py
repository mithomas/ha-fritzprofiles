"""Test AVM FRITZ!Box Access Profiles select entities."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.select import SERVICE_SELECT_OPTION
from homeassistant.const import ATTR_ENTITY_ID, ATTR_OPTION
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_fritzprofiles.const import DOMAIN
from custom_components.ha_fritzprofiles.fritz_profile_switch import FritzProfileDevice
from custom_components.ha_fritzprofiles.select import (
    HaFritzProfilesEntity,
    async_setup_entry,
)


@pytest.fixture(name="coordinator")
def coordinator_fixture(coordinator_data):
    coordinator = MagicMock()
    coordinator.data = coordinator_data
    coordinator.async_request_refresh = AsyncMock()
    coordinator.hass = MagicMock()
    return coordinator


def test_entity_properties_and_options(coordinator):
    """Test basic entity metadata and options."""
    device = FritzProfileDevice(id="id", name="iPhone", profile_id="profile1")
    entity = HaFritzProfilesEntity(coordinator, device)

    assert entity.name == "iPhone"
    assert entity.unique_id == "iPhone"
    assert entity.current_option == "Standard"
    assert set(entity.options) == {"Standard", "Limited"}
    assert entity.icon == "mdi:web"


def test_handle_coordinator_update_updates_profile(coordinator):
    """Test entity updates when coordinator data changes."""
    device = FritzProfileDevice(id="id", name="iPhone", profile_id="profile1")
    entity = HaFritzProfilesEntity(coordinator, device)
    entity.hass = MagicMock()
    entity.entity_id = "select.iphone"

    coordinator.data.devices_by_name = {
        "iPhone": FritzProfileDevice(id="id", name="iPhone", profile_id="profile2")
    }

    entity._handle_coordinator_update()  # noqa: SLF001

    assert entity.current_option == "Limited"


def test_handle_coordinator_update_missing_device(coordinator):
    """Test coordinator updates ignore missing devices."""
    device = FritzProfileDevice(id="id", name="iPhone", profile_id="profile1")
    entity = HaFritzProfilesEntity(coordinator, device)
    entity.hass = MagicMock()
    entity.entity_id = "select.iphone"
    coordinator.data.devices_by_name = {}

    entity._handle_coordinator_update()  # noqa: SLF001

    assert entity.current_option == "Standard"
    assert entity.device.id == "id"


@pytest.mark.asyncio
async def test_async_select_option_calls_refresh(coordinator):
    """Test select option triggers refresh and profile update."""
    device = FritzProfileDevice(id="id", name="iPhone", profile_id="profile1")
    entity = HaFritzProfilesEntity(coordinator, device)
    entity.hass = MagicMock()
    entity.entity_id = "select.iphone"
    coordinator.client = MagicMock()
    coordinator.hass.async_add_executor_job = AsyncMock()

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option("Limited")

    coordinator.async_request_refresh.assert_awaited_once()
    coordinator.hass.async_add_executor_job.assert_awaited_once_with(
        coordinator.client.set_device_profile, "id", "profile2"
    )
    assert entity.current_option == "Limited"


@pytest.mark.asyncio
async def test_select_service_calls_client(hass, mock_config, coordinator_data):
    """Test select service calls update the Fritz client."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=mock_config, entry_id="test")
    config_entry.add_to_hass(hass)

    async def _run_job(func, *args):
        func(*args)

    with (
        patch("custom_components.ha_fritzprofiles.asyncio.sleep", new=AsyncMock()),
        patch(
            "custom_components.ha_fritzprofiles.coordinator.HaFritzProfilesDataUpdateCoordinator._async_update_data",
            new=AsyncMock(return_value=coordinator_data),
        ),
        patch(
            "custom_components.ha_fritzprofiles.fritz_profile_switch.FritzProfileSwitch.set_device_profile",
            autospec=True,
        ) as set_device_profile,
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        with patch.object(
            coordinator.hass, "async_add_executor_job", new=AsyncMock(side_effect=_run_job)
        ) as async_add_executor_job:
            entity_id = "select.iphone"
            state = hass.states.get(entity_id)
            assert state
            assert state.state == "Standard"

            await hass.services.async_call(
                SELECT_DOMAIN,
                SERVICE_SELECT_OPTION,
                service_data={ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "Limited"},
                blocking=True,
            )

    async_add_executor_job.assert_called()
    set_device_profile.assert_called_once_with(ANY, "landevice1", "profile2")

    updated_state = hass.states.get(entity_id)
    assert updated_state.state == "Limited"
    assert "options" in updated_state.attributes


@pytest.mark.asyncio
async def test_select_setup_entry_no_devices(hass, mock_config, coordinator_data):
    """Test select setup skips when no devices are available."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=mock_config, entry_id="test")
    config_entry.add_to_hass(hass)

    coordinator_data.devices_by_name = {}
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = MagicMock(
        data=coordinator_data
    )

    add_entities = MagicMock()
    await async_setup_entry(hass, config_entry, add_entities)

    add_entities.assert_called_once_with([])


@pytest.mark.asyncio
async def test_select_option_unknown_profile_raises(coordinator):
    """Test selecting an unknown profile raises KeyError."""
    device = FritzProfileDevice(id="id", name="iPhone", profile_id="profile1")
    entity = HaFritzProfilesEntity(coordinator, device)
    entity.hass = MagicMock()
    entity.entity_id = "select.iphone"
    coordinator.client = MagicMock()
    coordinator.hass.async_add_executor_job = AsyncMock()
    coordinator.data.profiles_by_name = {"Standard": "profile1"}

    with patch.object(entity, "async_write_ha_state"):
        with pytest.raises(KeyError):
            await entity.async_select_option("Missing")
