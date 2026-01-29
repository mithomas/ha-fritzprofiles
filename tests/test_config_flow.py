"""Test AVM FRITZ!Box Access Profiles config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import requests

from custom_components.ha_fritzprofiles.const import DOMAIN


@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent integration setup during config flow tests."""
    with (
        patch(
            "custom_components.ha_fritzprofiles.async_setup",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.ha_fritzprofiles.async_setup_entry",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.ha_fritzprofiles.async_unload_entry",
            new=AsyncMock(return_value=True),
        ),
    ):
        yield


@pytest.mark.asyncio
async def test_config_flow_shows_form(hass):
    """Test the initial form is shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_config_flow_success(hass, mock_config):
    """Test a successful config flow."""
    with patch(
        "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
        return_value=True,
        autospec=True,
    ) as check_credentials:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=mock_config
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "FRITZ!Box (test_username @ http://fritz.box)"
    assert result["data"] == mock_config
    assert result["result"]
    check_credentials.assert_called_once()


@pytest.mark.asyncio
async def test_config_flow_auth_error(hass, mock_config):
    """Test a failed config flow due to credential validation failure."""
    with patch(
        "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
        side_effect=PermissionError,
        autospec=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=mock_config
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}


@pytest.mark.asyncio
async def test_config_flow_request_exception(hass, mock_config):
    """Test a failed config flow due to request exceptions."""
    with patch(
        "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
        side_effect=requests.RequestException,
        autospec=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=mock_config
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}


@pytest.mark.asyncio
async def test_config_flow_single_instance_abort(hass, mock_config):
    """Test only one instance can be configured."""
    entry = MockConfigEntry(domain=DOMAIN, data=mock_config, entry_id="test")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
