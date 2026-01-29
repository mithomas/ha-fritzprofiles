"""Global fixtures for AVM FRITZ!Box Access Profiles integration."""

from unittest.mock import patch

import pytest

from custom_components.ha_fritzprofiles.const import CONF_PASSWORD, CONF_USERNAME

pytest_plugins = "pytest_homeassistant_custom_component"


# This fixture is used to prevent HomeAssistant from attempting to create and
# dismiss persistent notifications. These calls would fail without this fixture
# since the persistent_notification integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with (
        patch("homeassistant.components.persistent_notification.async_create"),
        patch("homeassistant.components.persistent_notification.async_dismiss"),
    ):
        yield


# This fixture, when used, will result in calls to load_device_profiles to return
# None. To have the call return a value, we would add the
# `return_value=<VALUE_TO_RETURN>` parameter to the patch call.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.FritzProfileSwitch.load_device_profiles"
    ):
        yield


# In this fixture, we are forcing calls to load_device_profiles to raise an
# Exception. This is useful for exception handling.
@pytest.fixture(name="error_on_get_data")
def error_get_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.FritzProfileSwitch.load_device_profiles",
        side_effect=Exception,
    ):
        yield


@pytest.fixture(name="mock_config")
def mock_config_fixture():
    """Return a mock config dict."""
    return {CONF_USERNAME: "test_username", CONF_PASSWORD: "test_password"}
