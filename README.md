# FRITZ!Box Access Profiles

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![Community Forum][forum-shield]][forum]

Switch your FRITZ!Box device access profiles from Home Assistant.
* **FRITZ!OS 8+ Compatible:** Uses the native `/api/v0/generic/` REST API instead of legacy HTML scraping.
* **Automatic Profile Assignment:** Seamlessly updates existing device rules (`PUT`) or creates new user profile rules (`POST`) for previously unconfigured devices.
* **Session Reuse:** Keeps the `AVM-SID` active across polling intervals with automatic `403` re-authentication to avoid flooding the FRITZ!Box event log.
* **Smart Device Registry Integration:**
  * Registers the FRITZ!Box as a parent hub device.
  * Links network devices via `CONNECTION_NETWORK_MAC` to merge cleanly with existing devices from *FRITZ!Box Tools*, *Tasmota*, *ESPHome*, etc.
  * Prioritizes user-defined `friendly_name` over raw hostnames.
* **Full UI Configuration:**
  * Initial setup flow with automatic HTTPS enforcement.
  * **Reconfigure flow** to update credentials or URL without losing entity IDs.
  * **Options flow** to customize the polling interval (10–3600 seconds, default: 30s).
* **Localized:** Full English and German translations included.

**This component will set up the following platforms.**

| Platform | Description                                                          |
| -------- | -------------------------------------------------------------------- |
| `select` | Show current access profile per network device and select a new one. |

## Installation

### Via Marketplace (previously HACS) (preferred)

1. [Install HACS](https://hacs.xyz/docs/setup/prerequisites/) if you use Homeassistant version before 2026-11
2. Add `https://github.com/mithomas/ha-fritzprofiles/` [as a custom repository](https://hacs.xyz/docs/setup/prerequisites/)
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "FRITZ!Box Access Profiles", enter url, user and password to access your FRITZ!Box.

### Manually

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `https://github.com/mithomas/ha-fritzprofiles`.
4. Download _all_ the files from the `custom_components/https://github.com/mithomas/ha-fritzprofiles/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "FRITZ!Box Access Profiles", enter url, user and password to access your FRITZ!Box.

## Usage

All your uniquely named network devices will be set up as `select` entities, showing the currently chosen profile and allow you to change it. ⚠️ Please keep in mind that updates will take up to 1 minute.

It is not advised to change the profiles of multiple devices at once (e.g. via a scene, script or automation) as this may likely overstrain your FRITZ!Box - if you actually have such a use case, the implementation of a respective service within this integration would be the far better way. Feel free to raise a PR or an issue for that :-).

## Managing New or Removed Devices

To keep background polling fast and lightweight, new or deleted FRITZ!Box network devices are loaded during integration startup. If you add new devices to your network, simply select **Reload** from the integration's three-dot menu in Home Assistant.

## FAQ

### Why don't all of my network device show up?

This integration uses the device name (as defined in your FRITZ!Box) as the device key.

It can be that a device name is used more then once in your FRITZ!Box, usually when it is/was connected both via WIFI & cable LAN: Each network adapter has its own MAC address and as such a dedicated entry in your network device list.

In such a case simply [rename](https://fritz.com/en/apps/knowledge-base/fritz-box-7560/791_Network-device-cannot-be-renamed) them so that their names are different and wait for the next synchronization or restart Home Assistant.

### What is my user name?

Even if you only log into your FRITZ!Box with password only, there's a standard admin user account associated with this - it's named `fritzNNNN` (the numbers are random) and you find it in your FRITZ!Box web interface under System > FRITZ!Box User.

### I changed my password, how do I update it in the device configuration?

Simply remove and re-add the integration with the new credentials. Don't worry, since the names of the devices haven't changed their history is preserved.

### Why has the name been chosen as device id?

The FRITZ!Box changes the device id on the respective form, depending on whether these device use the standard profile (then it's something like `landeviceNNNN`) or a user-defined profile (then it's something like `userNNNN`) - thus this not usable as an id as new entities would pop uup after every change. Also, there's no mapping from one to the other except the name so we might as well us that directly.


### Why not integrate this into the official [FRITZ!Box Tools](https://www.home-assistant.io/integrations/fritz/) integration?

Feel free to create a PR.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template. Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template.

The backend code for communicating with the FRITZ!Box is based on the _fritz-switch-profiles_ script, originally from [flopp](https://github.com/flopp/fritz-switch-profiles), adapted by [eifinger](https://github.com/eifinger/fritz-switch-profiles)

## Links

- https://github.com/flopp/fritz-switch-profiles
- https://github.com/eifinger/fritz-switch-profiles
- https://github.com/AaronDavidSchneider/fritzprofiles
- https://boxmatrix.info/wiki/Property:kids_userlist.lua

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/mithomas/ha-fritzprofiles.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40mithomas-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/mithomas/ha-fritzprofiles.svg?style=for-the-badge
[releases]: https://github.com/mithomas/ha-fritzprofiles/releases
[user_profile]: https://github.com/mithomas
