"""Test AVM FRITZ!Box Access Profiles switch."""
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=wrong-import-order
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from custom_components.ha_fritzprofiles import async_setup_entry
from custom_components.ha_fritzprofiles.const import DOMAIN
from custom_components.ha_fritzprofiles.fritz_profile_switch import FritzProfileDevice
from custom_components.ha_fritzprofiles.select import HaFritzProfilesEntity
from homeassistant.const import ATTR_ENTITY_ID
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .const import MOCK_CONFIG


class TestHaFritzProfilesEntity:
    class TestHandleCoordinatorUpdate:
        @pytest.fixture
        def coordinator(self):
            coordinator = MagicMock()
            coordinator.data.profiles_by_id = {
                "profile_id": "profile",
                "profile_id2": "profile2",
            }
            return coordinator

        @pytest.fixture
        def device(self):
            return FritzProfileDevice(id="id", name="Device", profile_id="profile_id")

        @pytest.fixture
        def entity(self, device, coordinator):
            entity = HaFritzProfilesEntity(coordinator, device)
            entity.hass = MagicMock()
            entity.entity_id = "select.ut"
            return entity

        def test_init(self, entity):
            assert entity.name == "Device"
            assert entity.unique_id == "Device"
            assert entity._attr_current_option == "profile"
            assert entity._attr_options == ["profile", "profile2"]

        def test_updated_id(self, entity, coordinator):
            coordinator.data.devices_by_name = {
                "Device": FritzProfileDevice(
                    id="id2", name="Device", profile_id="profile_id"
                )
            }

            entity._handle_coordinator_update()

            assert entity.name == "Device"
            assert entity.device.id == "id2"

        def test_updated_profile(self, entity, coordinator):
            coordinator.data.devices_by_name = {
                "Device": FritzProfileDevice(
                    id="id", name="Device", profile_id="profile_id2"
                )
            }

            entity._handle_coordinator_update()

            assert entity.name == "Device"
            assert entity._attr_current_option == "profile2"

        def test_unavailable_in_update(self, coordinator, entity):
            coordinator.data.devices_by_name = {}

            entity._handle_coordinator_update()

            assert entity.name == "Device"
            assert entity.device.id == "id"


@pytest.mark.skip
async def test_switch_services(hass):
    """Test switch services."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")
    assert await async_setup_entry(hass, config_entry)
    await hass.async_block_till_done()

    # Functions/objects can be patched directly in test code as well and can be used to test
    # additional things, like whether a function was called or what arguments it was called with
    with patch("custom_components.HaProfilesApiClient.async_set_title") as title_func:
        await hass.services.async_call(
            "SWITCH",
            "SERVICE_TURN_OFF",
            service_data={ATTR_ENTITY_ID: "SWITCH.DEFAULT_NAME_SWITCH"},
            blocking=True,
        )
        assert title_func.called
        assert title_func.call_args == call("foo")

        title_func.reset_mock()

        await hass.services.async_call(
            "SWITCH",
            "SERVICE_TURN_ON",
            service_data={ATTR_ENTITY_ID: "SWITCH.DEFAULT_NAME_SWITCH"},
            blocking=True,
        )
        assert title_func.called
        assert title_func.call_args == call("bar")
