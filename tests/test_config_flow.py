"""Tests for the FRITZ!Box Access Profiles config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME

from custom_components.ha_fritzprofiles.config_flow import HaFritzProfilesConfigFlow


@patch(
    "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
    return_value=True,
)
async def test_user_flow_success_and_http_preserved(mock_check: object) -> None:
    """Test successful user setup preserves http:// and creates entry."""
    flow = HaFritzProfilesConfigFlow()
    flow.context = {"source": "user"}
    result = await flow.async_step_user(
        {
            CONF_URL: "http://fritz.box/",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
        }
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "FRITZ!Box (http://fritz.box)"
    assert result["data"][CONF_URL] == "http://fritz.box"


@patch(
    "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
    return_value=True,
)
async def test_user_flow_schemeless_url_defaults_to_https(mock_check: object) -> None:
    """Test schemeless host gets https:// prepended."""
    flow = HaFritzProfilesConfigFlow()
    flow.context = {"source": "user"}
    result = await flow.async_step_user(
        {
            CONF_URL: "fritz.box/",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
        }
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "FRITZ!Box (https://fritz.box)"
    assert result["data"][CONF_URL] == "https://fritz.box"


@patch(
    "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
    return_value=False,
)
async def test_user_flow_invalid_auth(mock_check: object) -> None:
    """Test invalid credentials show base error."""
    flow = HaFritzProfilesConfigFlow()
    flow.context = {"source": "user"}
    result = await flow.async_step_user(
        {
            CONF_URL: "https://fritz.box",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "wrong",
        }
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


@patch(
    "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
    side_effect=RuntimeError("connection boom"),
)
async def test_user_flow_unexpected_exception(mock_check: object) -> None:
    """Test unexpected exception during credential check maps to invalid_auth."""
    flow = HaFritzProfilesConfigFlow()
    flow.context = {"source": "user"}
    result = await flow.async_step_user(
        {
            CONF_URL: "https://fritz.box",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
        }
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


@patch(
    "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
    return_value=True,
)
async def test_reconfigure_flow_success(mock_check: object) -> None:
    """Test reconfigure flow preserves http://, updates entry data and reloads."""
    flow = HaFritzProfilesConfigFlow()
    flow.context = {"source": "reconfigure"}
    entry = MagicMock()
    entry.data = {
        CONF_URL: "https://fritz.box",
        CONF_USERNAME: "old_user",
        CONF_PASSWORD: "old_password",
    }
    flow._get_reconfigure_entry = MagicMock(return_value=entry)
    flow.async_set_unique_id = MagicMock(side_effect=lambda _: _async_noop())
    flow._abort_if_unique_id_mismatch = MagicMock()
    flow.async_update_reload_and_abort = MagicMock(
        return_value={"type": "abort", "reason": "reconfigure_successful"}
    )

    form_result = await flow.async_step_reconfigure(None)
    assert form_result["type"] == "form"
    assert form_result["step_id"] == "reconfigure"

    update_result = await flow.async_step_reconfigure(
        {
            CONF_URL: "http://192.168.178.1/",
            CONF_USERNAME: "new_user",
            CONF_PASSWORD: "new_password",
        }
    )
    assert update_result["type"] == "abort"
    assert update_result["reason"] == "reconfigure_successful"
    call_kwargs = flow.async_update_reload_and_abort.call_args.kwargs
    updated_data = call_kwargs.get("data") or call_kwargs.get("data_updates")
    assert updated_data[CONF_URL] == "http://192.168.178.1"


@patch(
    "custom_components.ha_fritzprofiles.config_flow.FritzProfileSwitch.check_credentials",
    return_value=False,
)
async def test_reconfigure_flow_invalid_auth(mock_check: object) -> None:
    """Test reconfigure flow shows error on invalid credentials."""
    flow = HaFritzProfilesConfigFlow()
    flow.context = {"source": "reconfigure"}
    entry = MagicMock()
    entry.data = {
        CONF_URL: "https://fritz.box",
        CONF_USERNAME: "old_user",
        CONF_PASSWORD: "old_password",
    }
    flow._get_reconfigure_entry = MagicMock(return_value=entry)

    result = await flow.async_step_reconfigure(
        {
            CONF_URL: "https://fritz.box",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "wrong",
        }
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}


async def _async_noop() -> None:
    """Async no-op helper for mocked async methods."""
