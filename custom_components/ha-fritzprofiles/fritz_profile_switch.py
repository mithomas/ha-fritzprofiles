"""\
Client library to read and update AVM FRITZ!Box device access profiles by parsing kids_userlist.lua.

Loads the whole list in one and saves

Originally based on https://github.com/eifinger/fritz-switch-profiles by Florian Pigorsch, Kevin Eifinger & contributors.
"""

import hashlib
import logging

import lxml.etree
import lxml.html
import requests

from dataclasses import dataclass

INVALID_SID = "0000000000000000"


@dataclass
class FritzProfileDevice:
    """Data class for a single device."""

    id: str
    """Example: landevice4711"""

    name: str
    """Device name as listed in the FRITZ!Box web ui."""

    profile_id: str
    """Example: filtprof4627"""


class FritzProfileDeviceData:
    """Data class holding the complete set of device profile data."""

    devices: list[FritzProfileDevice]
    profiles_by_id: dict[str, str]
    profiles_by_name: dict[str, str]

    def __init__(self, devices, profiles):
        self.devices = devices
        self.profiles_by_id = profiles
        self.profiles_by_name = {name:id for id,name in profiles.items()}


class FritzProfileSwitch:
    """Client class for device profile loading."""

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.sid = INVALID_SID
        self.password = password
        self.devices = []
        self.profiles_by_id = {}


    def load_device_profiles(self) -> FritzProfileDeviceData:
        """Performs login, loads all device profile data and performs logout."""
        self._login()
        self._load_device_profiles()
        self._logout()
        return FritzProfileDeviceData(devices=self.devices, profiles=self.profiles_by_id)


    def _load_device_profiles(self):
        html = lxml.html.fromstring(self._load_device_profile_rawdata())
        for i, row in enumerate(html.xpath('//table[@id="uiDevices"]/tr')):
            cell = row.xpath("td")

            if not _is_data_cell(cell):
                continue

            name = cell[0].get('title')

            select = cell[3].xpath("select")
            if not select:
                select = cell[4].xpath("select")
            if not select:
                continue

            device_id = select[0].xpath("@name")[0].split(":")[1]
            profile = select[0].xpath("option[@selected]/@value")[0]

            if i == 1: # profiles look the same for each device
                self.profiles_by_id = {o.get('value'): o.text_content() for o in select[0].xpath("option")}

            self.devices.append(FritzProfileDevice(id=device_id, name=name, profile_id=profile))


    def _load_device_profile_rawdata(self):
        """Fetch and store device profiles."""
        logging.info("FETCHING DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "cancel": "",
            "oldpage": "/internet/kids_userlist.lua",
        }
        url = self.url + "/data.lua"
        return requests.post(url, data=data, allow_redirects=True, timeout=300).text #TODO: check response


    def set_device_profile(self, device_id, profile_id): # pylint: disable=missing-function-docstring
        self._login()
        self._set_device_profile(device_id, profile_id)
        self._logout()


    def _set_device_profile(self, device_id, profile_id):
        """Update profiles on the FritzBox."""
        logging.info("\nUPDATING DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "apply": "",
            "oldpage": "/internet/kids_userlist.lua",
            "profile:" + device_id: profile_id,
        }
        requests.post(self.url + "/data.lua", data=data, allow_redirects=True, timeout=300) #TODO: check response


    def check_credentials(self) -> bool: # pylint: disable=missing-function-docstring
        self._login()

        if self.sid == INVALID_SID:
            return False

        self._logout()
        return True


    def _login(self):
        """Login and return session id."""
        logging.info("LOGGING IN TO FRITZ!BOX AT %s...", self.url)
        sid, challenge = _get_sid_challenge(self.url + "/login_sid.lua")
        if sid == INVALID_SID:
            md5 = hashlib.md5()
            md5.update(challenge.encode("utf-16le"))
            md5.update("-".encode("utf-16le"))
            md5.update(self.password.encode("utf-16le"))
            response = challenge + "-" + md5.hexdigest()
            url = self.url + "/login_sid.lua?username=" + self.user + "&response=" + response
            sid, challenge = _get_sid_challenge(url)
        if sid == INVALID_SID:
            raise PermissionError(
                "Cannot login to {} using the supplied credentials.".format(self.url)
            )
        self.sid = sid


    def _logout(self):
        """Update profiles on the FritzBox."""
        logging.info("\LOGGING OUT DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "security:command/logout=": 42,
        }
        requests.post(self.url, data=data, allow_redirects=True, timeout=30) #TODO: check response
        self.sid = INVALID_SID


def _get_sid_challenge(url):
    """Parse out sid and challenge from response of the login url."""
    response = requests.get(url, allow_redirects=True, timeout=30)
    data = lxml.etree.fromstring(response.content)  # pylint: disable=I1101
    sid = data.xpath("//SessionInfo/SID/text()")[0]
    challenge = data.xpath("//SessionInfo/Challenge/text()")[0]
    return sid, challenge


def _is_data_cell(cell) -> bool:
    """Checks whether the given cell is a device-profile data cell. """
    return cell and len(cell) == 5