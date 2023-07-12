# !/usr/bin/env python3

# Copyright 2020 Florian Pigorsch, Kevin Eifinger & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.
"""A (Python) script to remotely set device profiles of an AVM Fritz!Box"""

import hashlib
import logging

import lxml.etree
import lxml.html
import requests

from dataclasses import dataclass

INVALID_SID = "0000000000000000"


@dataclass
class FritzProfileDevice:
    """Data Type of FritzboxDataUpdateCoordinator's data."""
    id: str
    name: str
    profile: str


class FritzProfileDeviceData:
    """Data Type of FritzboxDataUpdateCoordinator's data."""

    devices: dict[str, FritzProfileDevice]
    profiles_by_id: dict[str, str]
    profiles_by_name: dict[str, str]

    def __init__(self, devices, profiles):
        self.devices = devices
        self.profiles_by_id = profiles
        self.profiles_by_name = {name:id for id,name in profiles.items()}


class FritzProfileSwitch: # rename to prepare later factoring out
    """A (Python) script to remotely set device profiles of an AVM Fritz!Box"""

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.sid = INVALID_SID
        self.password = password
        self.devices = {}  # devices by id
        self.profiles = {} # profiles by id


    def sync(self) -> FritzProfileDeviceData:
        """Logs in and fetches all data."""
        self.login()
        self.fetch_device_profiles()
        self.logout()
        return FritzProfileDeviceData(devices=self.devices, profiles=self.profiles)


    def check_credentials(self) -> bool:
        self.login()

        if self.sid == INVALID_SID:
            return False
        else:
            self.logout()
            return True


    def fetch_device_profiles(self):
        html = lxml.html.fromstring(self.load_device_profile_data())
        for i, row in enumerate(html.xpath('//table[@id="uiDevices"]/tr')):
            cell = row.xpath("td")

            if not is_data_cell(cell):
                continue

            name = cell[0].get('title')

            select = cell[3].xpath("select")
            if not select:
                select = cell[4].xpath("select")
            if not select:
                continue

            id = select[0].xpath("@name")[0].split(":")[1]
            profile = select[0].xpath("option[@selected]/@value")[0]

            if i == 1: # profiles look the same for each device
                self.profiles = {o.get('value'): o.text_content() for o in select[0].xpath("option")}

            self.devices[id] = FritzProfileDevice(id=id, name=name, profile=profile)


    def load_device_profile_data(self):
        """Fetch and store device profiles."""
        logging.info("FETCHING DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "cancel": "",
            "oldpage": "/internet/kids_userlist.lua",
        }
        url = self.url + "/data.lua"
        return requests.post(url, data=data, allow_redirects=True).text #TODO: check response


    def set_profile(self, device_id, profile_id):
        self.login()
        self._set_profile(device_id, profile_id)
        self.logout()

    def _set_profile(self, device_id, profile_id):
        """Update profiles on the FritzBox."""
        logging.info("\nUPDATING DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "apply": "",
            "oldpage": "/internet/kids_userlist.lua",
            "profile:" + device_id: profile_id,
        }
        requests.post(self.url + "/data.lua", data=data, allow_redirects=True) #TODO: check response


    def login(self):
        """Login and return session id."""
        logging.info("LOGGING IN TO FRITZ!BOX AT %s...", self.url)
        sid, challenge = get_sid_challenge(self.url + "/login_sid.lua")
        if sid == INVALID_SID:
            md5 = hashlib.md5()
            md5.update(challenge.encode("utf-16le"))
            md5.update("-".encode("utf-16le"))
            md5.update(self.password.encode("utf-16le"))
            response = challenge + "-" + md5.hexdigest()
            url = self.url + "/login_sid.lua?username=" + self.user + "&response=" + response
            sid, challenge = get_sid_challenge(url)
        if sid == INVALID_SID:
            raise PermissionError(
                "Cannot login to {} using the supplied credentials.".format(self.url)
            )
        self.sid = sid

    def logout(self):
        """Update profiles on the FritzBox."""
        logging.info("\LOGGING OUT DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "security:command/logout=": 42,
        }
        requests.post(self.url, data=data, allow_redirects=True) #TODO: check response
        self.sid = INVALID_SID


def get_sid_challenge(url):
    """Parse out sid and challenge from response of the login url."""
    response = requests.get(url, allow_redirects=True)
    data = lxml.etree.fromstring(response.content)  # pylint: disable=I1101
    sid = data.xpath("//SessionInfo/SID/text()")[0]
    challenge = data.xpath("//SessionInfo/Challenge/text()")[0]
    return sid, challenge


def is_data_cell(cell) -> bool:
    """Checks whether the given cell is a device-profile data cell. """
    return cell and len(cell) == 5