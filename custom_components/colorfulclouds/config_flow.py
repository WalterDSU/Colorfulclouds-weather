
"""Adds config flow for Colorfulclouds."""
import logging
import requests
import json
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME

from collections import OrderedDict
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN,
    CONF_HOURLYSTEPS,
    CONF_DAILYSTEPS,
    CONF_ALERT,
    CONF_LIFEINDEX,
    CONF_CUSTOM_UI,
    CONF_STARTTIME,
    CONF_UPDATE_INTERVAL,
    )
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

USER_AGENT = 'ColorfulCloudsPro/6.7.2 (iPhone; iOS 16.2; Scale/3.00)'
DEVICE_ID= 'D9AC88E9-B5CE-40FC-96CD-8E38CF5287B7'
headers = {'User-Agent': USER_AGENT,
          'device-id': DEVICE_ID,
          'Accept': 'application/json',
          'Accept-Language': 'zh-Hans-CN;q=1',
		  'app-version': '6.7.2',
		  'app_name': 'weather',
		  'app-name': 'weather'
          }
          
USER_AGENT_WX = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.42(0x18002a29) NetType/WIFI Language/zh_CN'    
wxheaders = {'User-Agent': USER_AGENT_WX,
          'Host': 'api.caiyunapp.com',
          'content-type': 'application/json',
          'Accept-Encoding': 'gzip,compress,br,deflate',
		  'Referer': 'https://servicewechat.com/wx487b4e7c415e06ff/93/page-frame.html'
          }

@config_entries.HANDLERS.register(DOMAIN)
class ColorfulcloudslowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ColorfulcloudsOptionsFlow(config_entry)

    def __init__(self):
        """Initialize."""
        self._errors = {}
    
    # @asyncio.coroutine
    def get_data(self, url, api_key):
        #json_text = requests.get(url).content
        json_text = requests.get(url, headers = headers if str(api_key)[0:4] == "UR8A" else (wxheaders if str(api_key)[0:8] == "Y2FpeXVu" else "") ).content
        resdata = json.loads(json_text)
        return resdata

    async def async_step_user(self, user_input={}):
        self._errors = {}
        if user_input is not None:
            # Check if entered host is already in HomeAssistant
            existing = await self._check_existing(user_input[CONF_NAME])
            if existing:
                return self.async_abort(reason="already_configured")

            # If it is not, continue with communication test
            url = str.format("https://api.caiyunapp.com/{}/{}/{},{}/weather.json?dailysteps=7&hourlysteps=24&alert=true", user_input["api_version"], user_input["api_key"], user_input["longitude"], user_input["latitude"])
            redata = await self.hass.async_add_executor_job(self.get_data, url, user_input["api_key"])
            status = redata['status']
            if status == "ok":
                await self.async_set_unique_id(f"{user_input['longitude']}-{user_input['latitude']}".replace(".","_"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                self._errors["base"] = "communication"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):

        # Defaults
        api_version = "v2.6"
        data_schema = OrderedDict()
        #data_schema[vol.Required(CONF_API_KEY)] = str
        data_schema[vol.Optional(CONF_API_KEY, default="Y2Fp")] = str
        data_schema[vol.Optional("api_version", default=api_version)] = str
        data_schema[vol.Optional(CONF_LONGITUDE, default=self.hass.config.longitude)] = cv.longitude
        data_schema[vol.Optional(CONF_LATITUDE, default=self.hass.config.latitude)] = cv.latitude
        data_schema[vol.Optional(CONF_NAME, default=self.hass.config.location_name)] = str
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_import(self, user_input):
        """Import a config entry.

        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})

    async def _check_existing(self, host):
        for entry in self._async_current_entries():
            if host == entry.data.get(CONF_NAME):
                return True

class ColorfulcloudsOptionsFlow(config_entries.OptionsFlow):
    """Config flow options for Colorfulclouds."""

    def __init__(self, config_entry):
        """Initialize Colorfulclouds options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, 10),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440)),
                    vol.Optional(
                        CONF_DAILYSTEPS,
                        default=self.config_entry.options.get(CONF_DAILYSTEPS, 7),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=16)),
                    vol.Optional(
                        CONF_HOURLYSTEPS,
                        default=self.config_entry.options.get(CONF_HOURLYSTEPS, 24),
                    ): vol.All(vol.Coerce(int), vol.Range(min=24, max=360)),
                    vol.Optional(
                        CONF_STARTTIME,
                        default=self.config_entry.options.get(CONF_STARTTIME, 0),
                    ): vol.All(vol.Coerce(int), vol.Range(min=-5, max=0)),
                    vol.Optional(
                        CONF_ALERT,
                        default=self.config_entry.options.get(CONF_ALERT, True),
                    ): bool,
                    vol.Optional(
                        CONF_LIFEINDEX,
                        default=self.config_entry.options.get(CONF_LIFEINDEX, False),
                    ): bool,
                    vol.Optional(
                        CONF_CUSTOM_UI,
                        default=self.config_entry.options.get(CONF_CUSTOM_UI, False),
                    ): bool
                }
            ),
        )

