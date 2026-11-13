"""Config flow for FRITZ!Box Access Profiles integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
import voluptuous as vol

from .const import DEFAULT_URL, DOMAIN
from .fritz_profile_switch import FritzProfileSwitch

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def _normalize_url(raw_url: str) -> str:
    """Strip whitespace/trailing slash and prepend https:// if no scheme is given."""
    url = raw_url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _test_credentials(url: str, username: str, password: str) -> bool:
    """Validate FRITZ!Box credentials in executor thread."""
    try:
        client = FritzProfileSwitch(url, username, password)
        return client.check_credentials()
    except Exception:
        _LOGGER.exception("Unexpected error connecting to FRITZ!Box at %s", url)
        return False


class HaFritzProfilesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FRITZ!Box Access Profiles."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = _normalize_url(user_input[CONF_URL])
            user_input[CONF_URL] = url
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            valid = await self.hass.async_add_executor_job(
                _test_credentials, url, username, password
            )
            if valid:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"FRITZ!Box ({url})",
                    data=user_input,
                )

            errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing FRITZ!Box entry."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            url = _normalize_url(user_input[CONF_URL])
            user_input[CONF_URL] = url
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            valid = await self.hass.async_add_executor_job(
                _test_credentials, url, username, password
            )
            if valid:
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data={
                        CONF_URL: url,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )

            errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=reconfigure_entry.data.get(CONF_URL, DEFAULT_URL),
                    ): str,
                    vol.Required(
                        CONF_USERNAME,
                        default=reconfigure_entry.data.get(CONF_USERNAME, ""),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
