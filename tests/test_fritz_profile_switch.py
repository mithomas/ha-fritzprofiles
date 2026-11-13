"""Unit tests for the FritzProfileSwitch REST API client."""

from __future__ import annotations

import hashlib
from unittest.mock import MagicMock, patch

import pytest
import requests

from custom_components.ha_fritzprofiles.fritz_profile_switch import (
    BLOCKED_PROFILE_UID,
    FritzProfileSwitch,
    _build_challenge_response,
)


def _xml_session(sid: str, challenge: str = "12345678") -> bytes:
    """Build a minimal FRITZ!Box login_sid.lua XML response."""
    return (
        f'<?xml version="1.0" encoding="utf-8"?>'
        f"<SessionInfo><SID>{sid}</SID><Challenge>{challenge}</Challenge></SessionInfo>"
    ).encode()


def test_url_normalization() -> None:
    """Test http:// is preserved and schemeless hosts default to https://."""
    http_client = FritzProfileSwitch("http://fritz.box/", "user", "pass")
    assert http_client.url == "http://fritz.box"

    schemeless_client = FritzProfileSwitch("fritz.box/", "user", "pass")
    assert schemeless_client.url == "https://fritz.box"


def test_build_challenge_response_pbkdf2_and_md5() -> None:
    """Test PBKDF2 (FRITZ!OS 7.24+/8+) and legacy MD5 challenge-response math."""
    # PBKDF2 (version=2)
    challenge_v2 = (
        "2$60000$b766b9c3aedd5c053369d598862407c5$6000$a0f25b9a0b084ac338c8b2b8e10323b5"
    )
    response_v2 = _build_challenge_response(challenge_v2, "secret")
    h1 = hashlib.pbkdf2_hmac(
        "sha256",
        b"secret",
        bytes.fromhex("b766b9c3aedd5c053369d598862407c5"),
        60000,
    )
    h2 = hashlib.pbkdf2_hmac(
        "sha256",
        h1,
        bytes.fromhex("a0f25b9a0b084ac338c8b2b8e10323b5"),
        6000,
    )
    assert response_v2 == f"a0f25b9a0b084ac338c8b2b8e10323b5${h2.hex()}"

    # Legacy MD5 fallback
    response_v1 = _build_challenge_response("12345678", "secret")
    expected_md5 = hashlib.md5(
        b"12345678".decode("utf-8").encode("utf-16le")
        + b"-"
        + b"secret".decode("utf-8").encode("utf-16le")
    ).hexdigest()
    assert response_v1 == f"12345678-{expected_md5}"


@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.get")
def test_login_and_session_reuse(mock_get: MagicMock) -> None:
    """Test PBKDF2 login succeeds, caches SID, and reuses it on subsequent calls."""
    challenge = (
        "2$100$00112233445566778899aabbccddeeff$10$ffeeddccbbaa99887766554433221100"
    )
    resp_challenge = MagicMock(content=_xml_session("0000000000000000", challenge))
    resp_sid = MagicMock(content=_xml_session("abcdef1234567890", "00000000"))
    mock_get.side_effect = [resp_challenge, resp_sid]

    client = FritzProfileSwitch("https://fritz.box", "admin", "secret")
    assert client.check_credentials() is True
    assert client.sid == "abcdef1234567890"
    assert mock_get.call_count == 2

    # Second call reuses active SID without additional HTTP requests
    client._ensure_login()
    assert mock_get.call_count == 2


@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.get")
def test_login_failure(mock_get: MagicMock) -> None:
    """Test failed authentication returns False in check_credentials."""
    resp_challenge = MagicMock(content=_xml_session("0000000000000000", "12345678"))
    resp_failed = MagicMock(content=_xml_session("0000000000000000", "87654321"))
    mock_get.side_effect = [resp_challenge, resp_failed]

    client = FritzProfileSwitch("https://fritz.box", "admin", "wrong")
    assert client.check_credentials() is False

    mock_get.side_effect = requests.ConnectionError("Unreachable")
    assert client.check_credentials() is False


@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.request")
@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.get")
def test_load_device_profiles_and_naming(
    mock_get: MagicMock, mock_request: MagicMock
) -> None:
    """Test loading profiles, user rules, friendly_name priority, and blocked status."""
    mock_get.side_effect = [
        MagicMock(content=_xml_session("0000000000000000", "12345678")),
        MagicMock(content=_xml_session("1111222233334444", "00000000")),
    ]

    profiles_json = {
        "profile": [
            {"UID": "filtprof1", "name": "Standard"},
            {"UID": "filtprof3", "name": "Unbeschränkt"},
        ]
    }
    users_json = {
        "user": [
            {"type": "3", "name": "(default)", "filter_profile_UID": "filtprof1"},
            {
                "UID": "user1",
                "landeviceUID": "landevice10",
                "filter_profile_UID": "filtprof3",
                "disallowed": "0",
            },
            {
                "UID": "user2",
                "landeviceUID": "landevice20",
                "filter_profile_UID": "filtprof1",
                "disallowed": "1",
            },
        ]
    }
    devices_json = {
        "landevice": [
            {
                "UID": "landevice10",
                "name": "esp32-node",
                "friendly_name": "Büro-Sensor",
                "mac": "AA:BB:CC:DD:EE:01",
            },
            {
                "UID": "landevice20",
                "name": "gast-laptop",
                "friendly_name": "",
                "mac": "",
            },
            {
                "UID": "landevice30",
                "name": "default-tv",
            },
            {
                "UID": "",
                "name": "invalid-without-uid",
            },
        ]
    }

    mock_request.side_effect = [
        MagicMock(status_code=200, content=b"{}", json=lambda: profiles_json),
        MagicMock(status_code=200, content=b"{}", json=lambda: users_json),
        MagicMock(status_code=200, content=b"{}", json=lambda: devices_json),
    ]

    client = FritzProfileSwitch("https://fritz.box", "admin", "secret")
    data = client.load_device_profiles()

    assert data.profiles_by_id["filtprof1"] == "Standard"
    assert data.profiles_by_id["filtprof3"] == "Unbeschränkt"
    assert data.profiles_by_id[BLOCKED_PROFILE_UID] == "Gesperrt"

    assert len(data.devices) == 3
    by_id = {d.id: d for d in data.devices}
    assert by_id["landevice10"].name == "Büro-Sensor"
    assert by_id["landevice10"].profile_id == "filtprof3"
    assert by_id["landevice10"].mac == "AA:BB:CC:DD:EE:01"

    assert by_id["landevice20"].name == "gast-laptop"
    assert by_id["landevice20"].profile_id == BLOCKED_PROFILE_UID
    assert by_id["landevice20"].mac is None

    assert by_id["landevice30"].name == "default-tv"
    assert by_id["landevice30"].profile_id == "filtprof1"


@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.request")
@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.get")
def test_403_session_retry(mock_get: MagicMock, mock_request: MagicMock) -> None:
    """Test expired SID (HTTP 403) triggers automatic re-authentication and retry."""
    mock_get.side_effect = [
        MagicMock(content=_xml_session("0000000000000000", "11111111")),
        MagicMock(content=_xml_session("new_sid_99999999", "00000000")),
    ]
    mock_request.side_effect = [
        MagicMock(status_code=403, content=b""),
        MagicMock(status_code=200, content=b"{}", json=lambda: {"profile": []}),
    ]

    client = FritzProfileSwitch("https://fritz.box", "admin", "secret")
    client.sid = "expired_sid_0000"

    res = client._request_api("GET", "filter_profile")
    assert res == {"profile": []}
    assert client.sid == "new_sid_99999999"
    assert mock_request.call_count == 2


@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.request")
def test_set_device_profile_put_and_post(mock_request: MagicMock) -> None:
    """Test updating existing user rule via PUT and creating new rule via POST."""
    client = FritzProfileSwitch("https://fritz.box", "admin", "secret")
    client.sid = "valid_sid_123456"

    users_json = {
        "user": [
            {"UID": "user_existing", "landeviceUID": "landevice10"},
        ]
    }

    mock_request.side_effect = [
        MagicMock(status_code=200, content=b"{}", json=lambda: users_json),
        MagicMock(status_code=200, content=b""),
    ]
    client.set_device_profile("landevice10", "filtprof3")
    assert mock_request.call_args_list[1].args[0] == "PUT"
    assert mock_request.call_args_list[1].args[1].endswith("/user/user/user_existing")
    assert mock_request.call_args_list[1].kwargs["json"] == {
        "filter_profile_UID": "filtprof3",
        "disallowed": "0",
    }

    mock_request.reset_mock()
    mock_request.side_effect = [
        MagicMock(status_code=200, content=b"{}", json=lambda: users_json),
        MagicMock(status_code=200, content=b""),
    ]
    client.set_device_profile("landevice99", BLOCKED_PROFILE_UID)
    assert mock_request.call_args_list[1].args[0] == "POST"
    assert mock_request.call_args_list[1].args[1].endswith("/user/user")
    assert mock_request.call_args_list[1].kwargs["json"] == {
        "landeviceUID": "landevice99",
        "disallowed": "1",
        "type": "1",
    }


@patch("custom_components.ha_fritzprofiles.fritz_profile_switch.requests.request")
def test_set_device_profile_put_blocked_and_post_regular(
    mock_request: MagicMock,
) -> None:
    """Test blocking existing rule via PUT and adding regular profile via POST."""
    client = FritzProfileSwitch("https://fritz.box", "admin", "secret")
    client.sid = "valid_sid_123456"

    users_json = {
        "user": [
            {"UID": "user_existing", "landeviceUID": "landevice10"},
        ]
    }

    mock_request.side_effect = [
        MagicMock(status_code=200, content=b"{}", json=lambda: users_json),
        MagicMock(status_code=200, content=b""),
    ]
    client.set_device_profile("landevice10", BLOCKED_PROFILE_UID)
    assert mock_request.call_args_list[1].args[0] == "PUT"
    assert mock_request.call_args_list[1].kwargs["json"] == {"disallowed": "1"}

    mock_request.reset_mock()
    mock_request.side_effect = [
        MagicMock(status_code=200, content=b"{}", json=lambda: users_json),
        MagicMock(status_code=200, content=b""),
    ]
    client.set_device_profile("landevice77", "filtprof2")
    assert mock_request.call_args_list[1].args[0] == "POST"
    assert mock_request.call_args_list[1].kwargs["json"] == {
        "landeviceUID": "landevice77",
        "disallowed": "0",
        "type": "1",
        "filter_profile_UID": "filtprof2",
    }

    err_resp = MagicMock(status_code=500, content=b"")
    err_resp.raise_for_status.side_effect = requests.HTTPError("Server error")
    mock_request.side_effect = [err_resp]
    with pytest.raises(requests.HTTPError):
        client._request_api("GET", "landevice")
