"""Adds config flow for AVM FRITZ!Box Access Profiles."""
import voluptuous as vol

from .fritz_switch_profiles import FritzProfileSwitch

from homeassistant import config_entries

from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import CONF_URL
from .const import DOMAIN


class HaFritzProfilesFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for https://github.com/mithomas/ha-fritzprofiles."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_URL],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)



    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default="http://fritz.box"): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, url, username, password):
        """Return true if credentials is valid."""
        try:
            sid = await self.hass.async_add_executor_job(FritzProfileSwitch(url, username, password).login)
            return sid != "0000000000000000"
        except Exception:  # pylint: disable=broad-except
            pass
        return False
