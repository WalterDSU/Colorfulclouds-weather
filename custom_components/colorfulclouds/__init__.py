'''
Author        : fineemb
Github        : https://github.com/fineemb
Description   : 
Date          : 2020-06-07 16:40:38
LastEditors   : fineemb,dscao
LastEditTime  : 2020-11-21 20:07:33
'''
"""
Component to integrate with 彩云天气.

For more details about this component, please refer to
https://github.com/fineemb/Colorfulclouds-weather
"""
import asyncio
import requests
import json
import datetime
import logging

from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout

from homeassistant.const import CONF_API_KEY
from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import (
    ATTR_FORECAST,
    CONF_DAILYSTEPS,
    CONF_HOURLYSTEPS,
    CONF_ALERT,
    CONF_LIFEINDEX,
    CONF_API_VERSION,
    CONF_LONGITUDE,
    CONF_LATITUDE,
    CONF_STARTTIME,
    COORDINATOR,
    VERSION,
    ROOT_PATH,
    DOMAIN,
    UNDO_UPDATE_LISTENER,
    CONF_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "weather"]

USER_AGENT = 'ColorfulCloudsPro/6.7.2 (iPhone; iOS 16.2; Scale/3.00)'
DEVICE_ID= 'D9AB80E9-B5CE-40FD-96CD-8E38CF5287B7'
headers = {'User-Agent': USER_AGENT,
          'device-id': DEVICE_ID,
          'Accept': 'application/json',
          'Accept-Language': 'zh-Hans-CN;q=1',
		  'app-version': '6.7.2',
		  'app_name': 'weather',
		  'app-name': 'weather'}
          
async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up configured Colorfulclouds."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass, config_entry) -> bool:
    
    hass.http.register_static_path(ROOT_PATH, hass.config.path('custom_components/colorfulclouds/local'), False)
    _LOGGER.debug(f"register_static_path: {ROOT_PATH + ':custom_components/colorfulclouds/local'}")
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/colorfulclouds-weather-card/colorfulclouds-weather-card.js?ver='+VERSION)
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/colorfulclouds-weather-card/colorfulclouds-weather-card-chart.js?ver='+VERSION)
    hass.components.frontend.add_extra_js_url(hass, ROOT_PATH + '/colorfulclouds-weather-card/colorfulclouds-weather-card-more.js?ver='+VERSION)
    
    _LOGGER.info("setup platform weather.colorfulclouds...")
    
    """Set up Colorfulclouds as config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    location_key = config_entry.unique_id
    longitude = config_entry.data[CONF_LONGITUDE]
    latitude = config_entry.data[CONF_LATITUDE]
    #api_version = config_entry.data[CONF_API_VERSION]
    api_version = "v2.6"
    dailysteps = config_entry.options.get(CONF_DAILYSTEPS, 5)
    hourlysteps = config_entry.options.get(CONF_HOURLYSTEPS, 24)
    alert = config_entry.options.get(CONF_ALERT, True)
    life = config_entry.options.get(CONF_LIFEINDEX, False)
    starttime = config_entry.options.get(CONF_STARTTIME, 0)
    update_interval_minutes = config_entry.options.get(CONF_UPDATE_INTERVAL, 10)

    _LOGGER.debug("Using location_key: %s, get forecast: %s", location_key, api_version)

    websession = async_get_clientsession(hass)

    coordinator = ColorfulcloudsDataUpdateCoordinator(
        hass, websession, api_key, api_version, location_key, longitude, latitude, dailysteps, hourlysteps, alert, life, starttime, update_interval_minutes
    )
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = config_entry.add_update_listener(update_listener)

    hass.data[DOMAIN][config_entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True

async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, component)
                for component in PLATFORMS
            ]
        )
    )

    hass.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass, config_entry):
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class ColorfulcloudsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Colorfulclouds data API."""

    def __init__(self, hass, session, api_key, api_version, location_key, longitude, latitude, dailysteps: int, hourlysteps: int, alert: bool, life: bool, starttime: int, update_interval_minutes: int):
        """Initialize."""
        self.location_key = location_key
        self.longitude = longitude
        self.latitude = latitude
        self.dailysteps = dailysteps
        self.alert = alert
        self.life = life
        self.hourlysteps = hourlysteps
        self.api_version = api_version
        self.api_key = api_key
        self.starttime = starttime
        self.update_interval_minutes = update_interval_minutes
        self._lifeindextime = 0
        self._lifeindex = {}
        is_metric = hass.config.units is METRIC_SYSTEM
        if is_metric:
            self.is_metric = "metric:v2"
        else:
            self.is_metric = "imperial"

        update_interval = (
            datetime.timedelta(minutes=2 if str(self.api_key)[0:6] == "UR8ASa" else self.update_interval_minutes)
        )
        _LOGGER.debug("Data will be update every %s", update_interval)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    # @asyncio.coroutine
    def get_data(self, url):
        json_text = requests.get(url, headers = headers if str(self.api_key)[0:6] == "UR8ASa" else "").content
        resdata = json.loads(json_text)
        return resdata

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with timeout(10):
                start_timestamp = int((datetime.datetime.now()+datetime.timedelta(days=self.starttime)).timestamp())
                url = str.format("https://api.caiyunapp.com/{}/{}/{},{}/weather.json?dailysteps={}&hourlysteps={}&alert={}&unit={}&timestamp={}", self.api_version, self.api_key, self.longitude, self.latitude, self.dailysteps, self.hourlysteps, str(self.alert).lower(), self.is_metric, start_timestamp)
                _LOGGER.debug("Requests remaining: %s", url)
                # json_text = requests.get(url).content
                resdata =  await self.hass.async_add_executor_job(self.get_data, url)
        except (
            ClientConnectorError
        ) as error:
            raise UpdateFailed(error)       
        
        
        
        if self.life == True and (int(datetime.datetime.now().timestamp()) - int(self._lifeindextime)) >= 3600:
            lifeindexnewdata = {}
            try:
                async with timeout(10):
                    url = str.format("http://api.caiyunapp.com/v1/lifeindex/?token={}&lng={}&lat={}", self.api_key, self.longitude, self.latitude)
                    _LOGGER.debug("Requests remaining: %s", url)
                    # json_text = requests.get(url).content
                    resdatalifeindex =  await self.hass.async_add_executor_job(self.get_data, url)
            except (
                ClientConnectorError
            ) as error:
                raise UpdateFailed(error)
                    
            if resdatalifeindex.get("result"):
                lifeindexdata = resdatalifeindex.get("result")
            else:        
                lifeindexdata = resdata.get("result")['daily']['life_index']
            for lifeindex in lifeindexdata:
                if lifeindex != "meta":
                    lifeindexk = {}
                    if int(datetime.datetime.now().strftime("%H")) >= 18:
                        #lifeindexnewdata[lifeindex] = lifeindexdata[lifeindex][1]                         
                        for k in lifeindexdata[lifeindex][1]:
                            if k == "date":
                                lifeindexk["datetime"] = lifeindexdata[lifeindex][1].get("date")
                            elif k == "detail":
                                lifeindexk[k] = lifeindexdata[lifeindex][1].get(k).replace("今日","明日")                      
                            else:
                                lifeindexk[k] = lifeindexdata[lifeindex][1].get(k)
                        lifeindexnewdata[lifeindex] = lifeindexk
                    else:
                        for k in lifeindexdata[lifeindex][1]:
                            if k == "date":
                                lifeindexk["datetime"] = lifeindexdata[lifeindex][0].get("date")
                            else:
                                lifeindexk[k] = lifeindexdata[lifeindex][0].get(k)
                        lifeindexnewdata[lifeindex] = lifeindexk
            self._lifeindex = lifeindexnewdata
            self._lifeindextime = int(datetime.datetime.now().timestamp())
            
        
        return {**resdata,"lifeindex":self._lifeindex,"location_key":self.location_key,"is_metric":self.is_metric}

