"""Client library to read and update AVM FRITZ!Box device access profiles."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging
from typing import Any

import lxml.etree
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER: logging.Logger = logging.getLogger(__package__)

INVALID_SID = "0000000000000000"
BLOCKED_PROFILE_UID = "filtprof4996"
HTTP_FORBIDDEN = 403


@dataclass
class FritzProfileDevice:
    """Data class representing a single network device."""

    id: str
    name: str
    profile_id: str
    mac: str | None = None


class FritzProfileDeviceData:
    """Data class holding the complete set of device profile data."""

    def __init__(
        self,
        devices: list[FritzProfileDevice],
        profiles: dict[str, str],
    ) -> None:
        """Initialize device profile data container."""
        self.devices = devices
        self.profiles_by_id = profiles


class FritzProfileSwitch:
    """Client class for reading and updating device profiles via REST API."""

    def __init__(self, url: str, user: str, password: str) -> None:
        """Initialize the FRITZ!Box REST API client."""
        base = url.rstrip("/")
        if not base.startswith(("http://", "https://")):
            base = f"https://{base}"
        self.url = base
        self.user = user
        self.password = password
        self.sid = INVALID_SID

    def _headers(self) -> dict[str, str]:
        """Build HTTP headers including active AVM-SID."""
        return {
            "AUTHORIZATION": f"AVM-SID {self.sid}",
            "Client-Name": "WebGUI",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": self.url,
            "Referer": f"{self.url}/",
        }

    def _ensure_login(self) -> None:
        """Reuse existing SID or authenticate via challenge-response if needed."""
        if self.sid != INVALID_SID:
            return

        resp = requests.get(
            f"{self.url}/login_sid.lua",
            params={"version": "2"},
            verify=False,
            timeout=10,
        )
        resp.raise_for_status()
        sid, challenge = _get_sid_challenge(resp.content)

        if sid == INVALID_SID:
            response = _build_challenge_response(challenge, self.password)
            login_resp = requests.get(
                f"{self.url}/login_sid.lua",
                params={"username": self.user, "response": response},
                verify=False,
                timeout=10,
            )
            login_resp.raise_for_status()
            sid, _ = _get_sid_challenge(login_resp.content)

        if sid == INVALID_SID:
            raise PermissionError(
                f"Authentication failed for {self.url} using provided credentials."
            )

        self.sid = sid

    def _request_api(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request against the REST API with 403 session retry."""
        self._ensure_login()
        url = f"{self.url}/api/v0/generic/{endpoint}"

        resp = requests.request(
            method,
            url,
            json=payload,
            headers=self._headers(),
            verify=False,
            timeout=30,
        )

        # Refresh SID once if the session expired on the FRITZ!Box
        if resp.status_code == HTTP_FORBIDDEN:
            _LOGGER.debug("Session expired on FRITZ!Box, re-authenticating")
            self.sid = INVALID_SID
            self._ensure_login()
            resp = requests.request(
                method,
                url,
                json=payload,
                headers=self._headers(),
                verify=False,
                timeout=30,
            )

        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def _parse_filter_profiles(self, profiles_raw: dict[str, Any]) -> dict[str, str]:
        """Parse filter profiles response into a UID-to-name mapping."""
        default_names = {
            "filtprof1": "Standard",
            "filtprof2": "Gast",
            "filtprof3": "Unbeschränkt",
            BLOCKED_PROFILE_UID: "Gesperrt",
        }
        profiles_by_id: dict[str, str] = {}
        for profile in profiles_raw.get("profile", []):
            uid = profile.get("UID")
            if uid:
                profiles_by_id[uid] = profile.get("name") or default_names.get(uid, uid)
        profiles_by_id.setdefault(BLOCKED_PROFILE_UID, "Gesperrt")
        return profiles_by_id

    def _parse_user_mappings(
        self, user_list: list[dict[str, Any]]
    ) -> tuple[str, dict[str, str]]:
        """Extract default profile UID and per-device profile assignments."""
        default_profile = "filtprof1"
        for user_entry in user_list:
            if user_entry.get("type") == "3" or user_entry.get("name") == "(default)":
                default_profile = user_entry.get("filter_profile_UID", "filtprof1")
                break

        device_to_profile: dict[str, str] = {}
        for user_entry in user_list:
            dev_uid = user_entry.get("landeviceUID")
            if dev_uid:
                if user_entry.get("disallowed") == "1":
                    device_to_profile[dev_uid] = BLOCKED_PROFILE_UID
                else:
                    device_to_profile[dev_uid] = user_entry.get(
                        "filter_profile_UID", default_profile
                    )

        return default_profile, device_to_profile

    def load_device_profiles(self) -> FritzProfileDeviceData:
        """Fetch all filter profiles, active user mappings, and network devices."""
        profiles_raw = self._request_api("GET", "filter_profile")
        profiles_by_id = self._parse_filter_profiles(profiles_raw)

        user_raw = self._request_api("GET", "user")
        default_profile, device_to_profile = self._parse_user_mappings(
            user_raw.get("user", [])
        )

        devices_raw = self._request_api("GET", "landevice")
        devices: list[FritzProfileDevice] = []

        for dev in devices_raw.get("landevice", []):
            dev_uid = dev.get("UID")
            if not dev_uid:
                continue

            # Prioritize user-configured friendly_name over technical hostname
            display_name = dev.get("friendly_name") or dev.get("name") or dev_uid
            mac_address = dev.get("mac") or None
            profile_id = device_to_profile.get(dev_uid, default_profile)

            devices.append(
                FritzProfileDevice(
                    id=dev_uid,
                    name=display_name,
                    profile_id=profile_id,
                    mac=mac_address,
                )
            )

        _LOGGER.debug(
            "Loaded %d profiles and %d devices via FRITZ!OS REST API",
            len(profiles_by_id),
            len(devices),
        )
        return FritzProfileDeviceData(devices=devices, profiles=profiles_by_id)

    def set_device_profile(self, device_id: str, profile_id: str) -> None:
        """Assign an access profile to a device UID (landeviceUID)."""
        _LOGGER.info("Setting device %s to profile %s", device_id, profile_id)

        user_raw = self._request_api("GET", "user")
        user_uid: str | None = None
        for user_entry in user_raw.get("user", []):
            if user_entry.get("landeviceUID") == device_id:
                user_uid = user_entry.get("UID")
                break

        is_blocked = profile_id == BLOCKED_PROFILE_UID

        if user_uid:
            # Update existing device profile rule via PUT
            endpoint = f"user/user/{user_uid}"
            if is_blocked:
                payload: dict[str, Any] = {"disallowed": "1"}
            else:
                payload = {"filter_profile_UID": profile_id, "disallowed": "0"}
            self._request_api("PUT", endpoint, payload=payload)
        else:
            # Create new device profile rule via POST
            endpoint = "user/user"
            payload = {
                "landeviceUID": device_id,
                "disallowed": "1" if is_blocked else "0",
                "type": "1",
            }
            if not is_blocked:
                payload["filter_profile_UID"] = profile_id
            self._request_api("POST", endpoint, payload=payload)

    def check_credentials(self) -> bool:
        """Validate credentials against the FRITZ!Box."""
        try:
            self._ensure_login()
        except (requests.RequestException, PermissionError, OSError):
            return False
        else:
            return self.sid != INVALID_SID


def _build_challenge_response(challenge: str, password: str) -> str:
    """Compute PBKDF2 (FRITZ!OS 7.24+/8+) or legacy MD5 challenge response."""
    if challenge.startswith("2$"):
        _, iter1, salt1, iter2, salt2 = challenge.split("$")
        hash1 = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt1),
            int(iter1),
        )
        hash2 = hashlib.pbkdf2_hmac(
            "sha256",
            hash1,
            bytes.fromhex(salt2),
            int(iter2),
        )
        return f"{salt2}${hash2.hex()}"

    md5 = hashlib.md5()
    md5.update(challenge.encode("utf-16le"))
    md5.update(b"-")
    md5.update(password.encode("utf-16le"))
    return f"{challenge}-{md5.hexdigest()}"


def _get_sid_challenge(content: bytes) -> tuple[str, str]:
    """Extract SID and Challenge from login_sid.lua XML response."""
    data = lxml.etree.fromstring(content)
    sid = data.xpath("//SessionInfo/SID/text()")[0]
    challenge = data.xpath("//SessionInfo/Challenge/text()")[0]
    return sid, challenge
