# !/usr/bin/env python3

# Copyright 2020 Florian Pigorsch, Kevin Eifinger & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.
"""A (Python) script to remotely set device profiles of an AVM Fritz!Box"""

import argparse
import hashlib
import logging
import re
import sys

import lxml.etree
import lxml.html
import requests


class FritzProfileSwitch:
    """A (Python) script to remotely set device profiles of an AVM Fritz!Box"""

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password
        self.sid = ""
        self.profiles = []
        self.devices = []
        #self.fetch_profiles()
        #self.fetch_devices()
        #self.fetch_device_profiles()

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

    def fetch_device_profiles(self):
        """Fetch and store device profiles."""
        logging.info("FETCHING DEVICE PROFILES...")
        data = {
            "xhr": 1,
            "sid": self.sid,
            "cancel": "",
            "oldpage": "/internet/kids_userlist.lua",
        }
        url = self.url + "/data.lua"
        response = requests.post(url, data=data, allow_redirects=True)
        html = lxml.html.fromstring(response.text)
        for row in html.xpath('//table[@id="uiDevices"]/tr'):
            cell = row.xpath("td")
            if (not cell) or (len(cell) != 5):
                continue
            select = cell[3].xpath("select")
            if not select:
                select = cell[4].xpath("select")
            if not select:
                continue
            id2 = select[0].xpath("@name")[0].split(":")[1]
            device_name = cell[0].xpath("span/text()")[0]
            profile = select[0].xpath("option[@selected]/@value")[0]
            self._merge_device(device_name, id2, profile)

    def _merge_device(self, name, id2, profile):
        multi = False
        found = -1
        for index, device in enumerate(self.devices):
            if id2 == device["id1"]:
                if found >= 0:
                    multi = True
                found = index
            elif name == device["name"]:
                if found >= 0:
                    multi = True
                found = index
        if found < 0:
            logging.info("  NO MATCH FOR {:16} {}".format(id2, name))
        elif multi:
            logging.info("  MULTIPLE MATCHES FOR {:16} {}".format(id2, name))
        else:
            if self.devices[found]["id1"] != id2:
                self.devices[found]["id2"] = id2
            self.devices[found]["profile"] = profile

    def _get_device(self, device_id):
        for device in self.devices:
            if device_id in (device["id1"], device["id2"]):
                return device
        return None

    def _get_profile(self, profile_id):
        for profile in self.profiles:
            if profile["id"] == profile_id:
                return profile
        return None

    def fetch_devices(self):
        """Fetch and store all devices"""
        logging.info("FETCHING DEVICES...")
        data = {"xhr": 1, "sid": self.sid, "no_sidrenew": "", "page": "netDev"}
        url = self.url + "/data.lua"
        response = requests.post(url, data=data, allow_redirects=True)
        json = response.json()
        if "data" in json and "active" not in json["data"]:
            data["xhrId"] = "all"
            response = requests.post(url, data=data, allow_redirects=True)
            json = response.json()
        self.devices = []
        if "data" in json and "active" in json["data"]:
            for device in json["data"]["active"]:
                self.devices.append(
                    {
                        "name": device["name"],
                        "id1": device["UID"],
                        "id2": None,
                        "profile": None,
                        "active": True,
                    }
                )
        if "data" in json and "passive" in json["data"]:
            for device in json["data"]["passive"]:
                self.devices.append(
                    {
                        "name": device["name"],
                        "id1": device["UID"],
                        "id2": None,
                        "profile": None,
                        "active": False,
                    }
                )

    def fetch_profiles(self):
        """Fetch and store all profiles"""
        logging.info("FETCHING AVAILABLE PROFILES...")
        data = {"xhr": 1, "sid": self.sid, "no_sidrenew": "", "page": "kidPro"}
        url = self.url + "/data.lua"
        response = requests.post(url, data=data, allow_redirects=True)
        html = lxml.html.fromstring(response.text)
        self.profiles = []
        for row in html.xpath('//table[@id="uiProfileList"]/tr'):
            profile_name = row.xpath('td[@class="name"]/span/text()')
            if not profile_name:
                continue
            profile_name = profile_name[0]
            profile_id = row.xpath(
                'td[@class="btncolumn"]/button[@name="edit"]/@value'
            )[0]
            self.profiles.append({"name": profile_name, "id": profile_id})

    def get_devices(self):
        """Return a list of devices sorted by name."""
        return sorted(self.devices, key=lambda x: x["name"].lower())

    def print_devices(self):
        """Print all device information."""
        print("\n{:16} {:16} {}".format("DEVICE_ID", "PROFILE_ID", "DEVICE_NAME"))
        for device in self.get_devices():
            print(
                "{:16} {:16} {}{}".format(
                    device["id1"],
                    device["profile"] if device["profile"] else "NONE",
                    device["name"],
                    "" if device["active"] else " [NOT ACTIVE]",
                )
            )

    def get_profiles(self):
        """Getter for profiles."""
        return self.profiles

    def print_profiles(self):
        """Print all profiles."""
        print("\n{:16} {}".format("PROFILE_ID", "PROFILE_NAME"))
        for profile in self.profiles:
            print("{:16} {}".format(profile["id"], profile["name"]))

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

    def set_blacklist(self, url_file_name):
        """Update the blacklist profile on the FritzBox."""
        logging.info("\nUPDATING PROFILE BLACKLIST...")
        with open(url_file_name, "r") as myfile:
            url_list = myfile.read()
            data = {
                "xhr": 1,
                "sid": self.sid,
                "urllist": url_list,
                "apply": "",
                "listtype": "black",
                "lang": "en",
                "page": "kids_blacklist",
            }
            url = self.url + "/data.lua"
            requests.post(url, data=data, allow_redirects=True)


def get_sid_challenge(url):
    """Parse out sid and challenge from response of the login url."""
    response = requests.get(url, allow_redirects=True)
    data = lxml.etree.fromstring(response.content)  # pylint: disable=I1101
    sid = data.xpath("//SessionInfo/SID/text()")[0]
    challenge = data.xpath("//SessionInfo/Challenge/text()")[0]
    return sid, challenge


def parse_kv(arguments):
    """Parse key value from arguments"""
    if not re.match("^[^=]+=[^=]+$", arguments):
        raise argparse.ArgumentTypeError("Invalid format: '{}'.".format(arguments))
    return arguments.split("=")


def main():
    """main"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        metavar="URL",
        type=str,
        default="http://fritz.box",
        help="The URL of your Fritz!Box; default: http://fritz.box",
    )
    parser.add_argument(
        "--user",
        metavar="USER",
        type=str,
        default="",
        help="Login username; default: empty",
    )
    parser.add_argument(
        "--password", metavar="PASSWORD", type=str, required=True, help="Login password"
    )
    parser.add_argument(
        "--list-devices",
        dest="listdevices",
        action="store_true",
        help="List all known devices",
    )
    parser.add_argument(
        "--list-profiles",
        dest="listprofiles",
        action="store_true",
        help="List all available profiles",
    )
    parser.add_argument(
        "deviceProfiles",
        nargs="*",
        metavar="DEVICE=PROFILE",
        type=parse_kv,
        help="Desired device to profile mapping",
    )
    parser.add_argument(
        "--load_blacklist_from_file",
        type=str,
        default="",
        help="Valid filename containing URL List to blacklist",
    )
    args = parser.parse_args()

    fps = FritzProfileSwitch(args.url, args.user, args.password)
    if args.listdevices:
        fps.print_devices()
    if args.listprofiles:
        fps.print_profiles()
    if args.deviceProfiles:
        fps.set_profiles(args.deviceProfiles)
    if args.load_blacklist_from_file:
        fps.set_blacklist(args.load_blacklist_from_file)

