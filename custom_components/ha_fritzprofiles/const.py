"""Constants for ha_fritzprofiles."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "ha_fritzprofiles"

PLATFORMS: list[Platform] = [Platform.SELECT]

CONF_URL = "url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_URL = "https://fritz.box"
DEFAULT_SCAN_INTERVAL = 30

STARTUP_MESSAGE = """
-------------------------------------------------------------------
%s
Version: %s
This is a custom integration!
-------------------------------------------------------------------
"""
