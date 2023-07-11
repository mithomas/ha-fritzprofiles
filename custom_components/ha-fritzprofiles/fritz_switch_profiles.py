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


class FritzProfileSwitch:
    """A (Python) script to remotely set device profiles of an AVM Fritz!Box"""

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.sid = None
        self.password = password
        self.devices = {}  # devices by id
        self.profiles = {} # profiles by id

    def sync(self):
        """Logs in and fetches all data."""
        self.login()
        self.fetch_device_profiles()

    def fetch_device_profiles(self):
        html = lxml.html.fromstring(self.load_device_profile_data)
        for i, row in enumerate(html.xpath('//table[@id="uiDevices"]/tr')):
            cell = row.xpath("td")
            if (not cell) or (len(cell) != 5):
                continue

            name = cell[0].xpath("@title")

            select = cell[3].xpath("select")
            if not select:
                select = cell[4].xpath("select")
            if not select:
                continue

            id = select[0].xpath("@name")[0].split(":")[1]
            profile = select[0].xpath("option[@selected]/@value")[0]

            if i == 0:
                self.profiles = {o.xpath("@value"): o.xpath("text()") for o in select[0].xpath("option")}

            self.devices[id] = {
                        "id": id,
                        "name": name,
                        "profile": profile,
                    }

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
        return requests.post(url, data=data, allow_redirects=True).text


    def set_profiles(self, device_profiles):
        """Update profiles on the FritzBox."""
        logging.info("\nUPDATING DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "apply": "",
            "oldpage": "/internet/kids_userlist.lua",
        }
        updates = 0
        for device_id, profile_id in device_profiles:
            device = self._get_device(device_id)
            if not device:
                logging.error("  CANNOT IDENTIFY DEVICE %s", device_id)
                continue
            profile = self._get_profile(profile_id)
            if not profile:
                logging.error("  CANNOT IDENTIFY PROFILE %s", profile_id)
                continue
            logging.info(
                "  CHANGING PROFILE OF %s/%s TO %s/%s",
                device_id,
                device["name"],
                profile_id,
                profile["name"],
            )
            if device["id2"]:
                device_id = device["id2"]
            updates += 1
            data["profile:" + device_id] = profile_id
        if updates > 0:
            url = self.url + "/data.lua"
            requests.post(url, data=data, allow_redirects=True)

    def login(self):
        """Login and return session id."""
        logging.info("LOGGING IN TO FRITZ!BOX AT %s...", self.url)
        sid, challenge = get_sid_challenge(self.url + "/login_sid.lua")
        if sid == "0000000000000000":
            md5 = hashlib.md5()
            md5.update(challenge.encode("utf-16le"))
            md5.update("-".encode("utf-16le"))
            md5.update(self.password.encode("utf-16le"))
            response = challenge + "-" + md5.hexdigest()
            url = self.url + "/login_sid.lua?username=" + self.user + "&response=" + response
            sid, challenge = get_sid_challenge(url)
        if sid == "0000000000000000":
            raise PermissionError(
                "Cannot login to {} using the supplied credentials.".format(self.url)
            )
        self.sid = sid

def get_sid_challenge(url):
    """Parse out sid and challenge from response of the login url."""
    response = requests.get(url, allow_redirects=True)
    data = lxml.etree.fromstring(response.content)  # pylint: disable=I1101
    sid = data.xpath("//SessionInfo/SID/text()")[0]
    challenge = data.xpath("//SessionInfo/Challenge/text()")[0]
    return sid, challenge
