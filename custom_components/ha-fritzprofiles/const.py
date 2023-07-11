"""Constants for AVM FRITZ!Box Access Profiles."""
# Base component constants
NAME = "AVM FRITZ!Box Access Profiles"
DOMAIN = "ha-fritzprofiles"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"

ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/mithomas/ha-fritzprofiles/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
PLATFORMS = ["select"]


# Configuration and options
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_URL = "url"

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
