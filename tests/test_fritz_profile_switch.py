"""Test FritzProfileSwitch client parsing and auth."""

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import call, patch

import pytest

from custom_components.ha_fritzprofiles.fritz_profile_switch import (
    DATA_CELL_COLUMNS,
    INVALID_SID,
    FritzProfileDeviceData,
    FritzProfileSwitch,
    _get_sid_challenge,
    _is_data_cell,
)


@dataclass
class _Response:
    text: str = ""
    content: bytes = b""

    def raise_for_status(self):
        return None


def _sid_response_xml(sid: str, challenge: str) -> bytes:
    return (
        f"<SessionInfo><SID>{sid}</SID><Challenge>{challenge}</Challenge></SessionInfo>"
    ).encode()


def _load_fixture(name: str) -> str:
    path = Path(__file__).parent / "resources" / name
    return path.read_text(encoding="utf-8")


def test_is_data_cell():
    """Test data cell detection."""
    assert _is_data_cell([1] * DATA_CELL_COLUMNS)
    assert not _is_data_cell([])
    assert not _is_data_cell([1] * (DATA_CELL_COLUMNS - 1))


def test_get_sid_challenge_parses_xml():
    """Test parsing of SID and challenge from XML."""
    response = _Response(content=_sid_response_xml("sid123", "challenge456"))

    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.requests.get",
        return_value=response,
    ):
        sid, challenge = _get_sid_challenge("http://example.local/login_sid.lua")

    assert sid == "sid123"
    assert challenge == "challenge456"


def test_login_success_with_challenge_flow():
    """Test login path that requires a challenge response."""
    responses = [
        _Response(content=_sid_response_xml(INVALID_SID, "challenge123")),
        _Response(content=_sid_response_xml("validsid", "unused")),
    ]

    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.requests.get",
        side_effect=responses,
    ) as get_request:
        client = FritzProfileSwitch("http://fritz.box", "user", "pass")
        client._login()  # noqa: SLF001

    assert client.sid == "validsid"
    assert "response=" in get_request.call_args_list[1].args[0]


def test_login_invalid_credentials():
    """Test login error when SID stays invalid."""
    responses = [
        _Response(content=_sid_response_xml(INVALID_SID, "challenge123")),
        _Response(content=_sid_response_xml(INVALID_SID, "challenge123")),
    ]

    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.requests.get",
        side_effect=responses,
    ):
        client = FritzProfileSwitch("http://fritz.box", "user", "pass")
        with pytest.raises(PermissionError):
            client._login()  # noqa: SLF001


def test_check_credentials_true_and_logout_called():
    """Test check_credentials returns True for valid SID."""
    client = FritzProfileSwitch("http://fritz.box", "user", "pass")

    with (
        patch.object(client, "_login") as login,
        patch.object(client, "_logout") as logout,
    ):
        client.sid = "validsid"
        assert client.check_credentials() is True

    login.assert_called_once()
    logout.assert_called_once()


def test_check_credentials_false_when_sid_invalid():
    """Test check_credentials returns False when SID stays invalid."""
    client = FritzProfileSwitch("http://fritz.box", "user", "pass")

    with (
        patch.object(client, "_login") as login,
        patch.object(client, "_logout") as logout,
    ):
        client.sid = INVALID_SID
        assert client.check_credentials() is False

    login.assert_called_once()
    logout.assert_not_called()


def test_load_device_profiles_parses_html():
    """Test HTML parsing of devices and profiles."""
    client = FritzProfileSwitch("http://fritz.box", "user", "pass")
    html = _load_fixture("kids_userlist.lua")

    with patch.object(client, "_load_device_profile_rawdata", return_value=html):
        devices, profiles = client._load_device_profiles()  # noqa: SLF001

    assert any(device.name == "iPhone" for device in devices)
    assert profiles["filtprof1"] == "Standard"


def test_load_device_profile_rawdata_posts():
    """Test raw data retrieval uses requests.post."""
    response = _Response(text="payload")

    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.requests.post",
        return_value=response,
    ) as post_request:
        client = FritzProfileSwitch("http://fritz.box", "user", "pass")
        text = client._load_device_profile_rawdata()  # noqa: SLF001

    assert text == "payload"
    post_request.assert_called_once()


def test_set_device_profile_posts():
    """Test setting device profile posts expected data."""
    response = _Response()

    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.requests.post",
        return_value=response,
    ) as post_request:
        client = FritzProfileSwitch("http://fritz.box", "user", "pass")
        client.sid = "sid123"
        client._set_device_profile("landevice1", "profile2")  # noqa: SLF001

    assert post_request.call_args == call(
        "http://fritz.box/data.lua",
        data={
            "xhr": 1,
            "sid": "sid123",
            "apply": "",
            "oldpage": "/internet/kids_userlist.lua",
            "profile:landevice1": "profile2",
        },
        allow_redirects=True,
        timeout=300,
    )


def test_logout_posts():
    """Test logout posts data and resets SID."""
    response = _Response()

    with patch(
        "custom_components.ha_fritzprofiles.fritz_profile_switch.requests.post",
        return_value=response,
    ):
        client = FritzProfileSwitch("http://fritz.box", "user", "pass")
        client.sid = "sid123"
        client._logout()  # noqa: SLF001

    assert client.sid == INVALID_SID


def test_load_device_profiles_calls_login_and_logout():
    """Test load_device_profiles wraps login and logout."""
    client = FritzProfileSwitch("http://fritz.box", "user", "pass")
    devices = []
    profiles = {"profile1": "Standard"}

    with (
        patch.object(client, "_login") as login,
        patch.object(client, "_logout") as logout,
        patch.object(client, "_load_device_profiles", return_value=(devices, profiles)),
    ):
        data = client.load_device_profiles()

    assert isinstance(data, FritzProfileDeviceData)
    assert data.devices == devices
    assert data.profiles_by_id == profiles
    login.assert_called_once()
    logout.assert_called_once()


def test_set_device_profile_calls_login_and_logout():
    """Test set_device_profile wraps login and logout."""
    client = FritzProfileSwitch("http://fritz.box", "user", "pass")

    with (
        patch.object(client, "_login") as login,
        patch.object(client, "_logout") as logout,
        patch.object(client, "_set_device_profile") as set_profile,
    ):
        client.set_device_profile("landevice1", "profile2")

    login.assert_called_once()
    logout.assert_called_once()
    set_profile.assert_called_once_with("landevice1", "profile2")
