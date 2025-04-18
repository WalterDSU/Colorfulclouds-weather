import logging
import json
import time
from datetime import datetime, timedelta
from homeassistant.helpers.device_registry import DeviceEntryType
import homeassistant.util.dt as dt_util
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_EXCEPTIONAL,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
    ATTR_CONDITION_WINDY_VARIANT,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    CONF_NAME,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from .const import (
    ATTRIBUTION,
    COORDINATOR,
    ROOT_PATH,
    DOMAIN,
    NAME,
    MANUFACTURER,
    CONF_LIFEINDEX,
    CONF_CUSTOM_UI,
)

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)

CONDITION_MAP = {
    'CLEAR_DAY': 'sunny',
    'CLEAR_NIGHT': 'clear-night',
    'PARTLY_CLOUDY_DAY': 'partlycloudy',
    'PARTLY_CLOUDY_NIGHT':'partlycloudy',
    'CLOUDY': 'cloudy',
    'LIGHT_HAZE': 'fog',
    'MODERATE_HAZE': 'fog',
    'HEAVY_HAZE': 'fog',
    'LIGHT_RAIN': 'rainy',
    'MODERATE_RAIN': 'rainy',
    'HEAVY_RAIN': 'pouring',
    'STORM_RAIN': 'pouring',
    'FOG': 'fog',
    'LIGHT_SNOW': 'snowy',
    'MODERATE_SNOW': 'snowy',
    'HEAVY_SNOW': 'snowy',
    'STORM_SNOW': 'snowy',
    'DUST': 'fog',
    'SAND': 'fog',
    'THUNDER_SHOWER': 'lightning-rainy',
    'HAIL': 'hail',
    'SLEET': 'snowy-rainy',
    'WIND': 'windy',
    'HAZE': 'fog',
    'RAIN': 'rainy',
    'SNOW': 'snowy',
}

CONDITION_CN_MAP = {
    'CLEAR_DAY': '晴',
    'CLEAR_NIGHT': '晴',
    'PARTLY_CLOUDY_DAY': '多云',
    'PARTLY_CLOUDY_NIGHT':'多云',
    'CLOUDY': '阴',
    'LIGHT_HAZE': '轻雾',
    'MODERATE_HAZE': '中雾',
    'HEAVY_HAZE': '大雾',
    'LIGHT_RAIN': '小雨',
    'MODERATE_RAIN': '中雨',
    'HEAVY_RAIN': '大雨',
    'STORM_RAIN': '暴雨',
    'FOG': '雾',
    'LIGHT_SNOW': '小雪',
    'MODERATE_SNOW': '中雪',
    'HEAVY_SNOW': '大雪',
    'STORM_SNOW': '暴雪',
    'DUST': '浮尘',
    'SAND': '沙尘',
    'THUNDER_SHOWER': '雷阵雨',
    'HAIL': '冰雹',
    'SLEET': '雨夹雪',
    'WIND': '大风',
    'HAZE': '雾霾',
    'RAIN': '雨',
    'SNOW': '雪',
}

WINDDIRECTIONS =[
    '北', '北-东北', '东北', '东-东北', '东', '东-东南', '东南', '南-东南',
    '南', '南-西南', '西南', '西-西南', '西', '西-西北', '西北', '北-西北', '北'
]
      
TRANSLATE_SUGGESTION = {
    'AnglingIndex': '钓鱼指数',
    'AirConditionerIndex': '空调开机指数',
    'AllergyIndex': '过敏指数',
    'HeatstrokeIndex': '中暑指数',
    'RainGearIndex': '雨具指数',
    'DryingIndex': '晾晒指数',
    'WindColdIndex': '风寒指数',
    'KiteIndex': '风筝指数',
    'MorningExerciseIndex': '晨练指数',
    'UltravioletIndex': '紫外线指数',
    'DrinkingIndex': '饮酒指数',
    'ComfortIndex': '舒适指数',
    'CarWashingIndex': '洗车指数',
    'DressingIndex': '穿衣指数',
    'ColdRiskIndex': '感冒指数',
    'AQIIndex': '空气污染指数',
    'WashClothesIndex': '洗衣指数',
    'MakeUpIndex': '化妆指数',
    'MoodIndex': '情绪指数',
    'SportIndex': '运动指数',
    'TravelIndex': '旅游指数',
    'DatingIndex': '交友指数',
    'ShoppingIndex': '逛街指数',
    'HairdressingIndex': '美发指数',
    'NightLifeIndex': '夜生活指数',
    'BoatingIndex': '划船指数',
    'RoadConditionIndex': '路况指数',
    'TrafficIndex': '交通指数',
    'ultraviolet': '紫外线',
    'carWashing': '洗车指数',
    'dressing': '穿衣指数',
    'comfort': '舒适度指数',
    'coldRisk': '感冒指数',
    'TakeoutIndex': '送外卖指数',
    'StreetStallIndex': '摆摊指数',
}

ATTR_SUGGESTION = "suggestion"

async def async_setup_entry(hass, config_entry, async_add_entities):    
    """Add a Colorfulclouds weather entity from a config_entry."""
    name = config_entry.data[CONF_NAME]
    life = config_entry.options.get(CONF_LIFEINDEX, False)
    custom_ui = config_entry.options.get(CONF_CUSTOM_UI, False)

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    _LOGGER.debug("metric: %s", coordinator.data["is_metric"])

    async_add_entities([ColorfulCloudsEntity(name, life, custom_ui, coordinator)], False)
            
class ColorfulCloudsEntity(WeatherEntity):
    """Representation of a weather condition."""
    _attr_attribution = ATTRIBUTION
    _attr_should_poll = False

    def __init__(self, name, life, custom_ui, coordinator):
        self.coordinator = coordinator
        _LOGGER.debug("coordinator: %s", coordinator.data["server_time"])
        self._name = name
        self.life = life
        self.custom_ui = custom_ui
        self._attrs = {}
        self._hourly_data = []
        self.hourly_summary = ""
        forecast_daily = list[list] | None
        forecast_hourly = list[list] | None
        forecast_twice_daily = list[list] | None

        # self._unit_system = "Metric" if self.coordinator.data["is_metric"]=="metric:v2" else "Imperial"
        # Coordinator data is used also for sensors which don't have units automatically
        # converted, hence the weather entity's native units follow the configured unit
        # system
        self._attr_name = self._name
        self._attr_unique_id = f"colorfulclouds-weather-{self.coordinator.data['location_key'].lower()}"
        self._attr_device_info = {
            "identifiers":  {(DOMAIN, self.coordinator.data["location_key"])},
            "name": f"ColorfulClouds Weather {name}",
            "manufacturer": MANUFACTURER,
            "entry_type": DeviceEntryType.SERVICE,       
        }
        self._attr_entity_registry_enabled_default = True
        
        if self.coordinator.data["is_metric"]=="metric:v2":
            self._attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
            self._attr_native_pressure_unit = UnitOfPressure.HPA
            self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
            self._attr_native_visibility_unit = UnitOfLength.KILOMETERS
            self._attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
            self._unit_system = "Metric"
        else:
            self._unit_system = "Imperial"
            self._attr_native_precipitation_unit = UnitOfLength.INCHES
            self._attr_native_pressure_unit = UnitOfPressure.INHG
            self._attr_native_temperature_unit = UnitOfTemperature.FAHRENHEIT
            self._attr_native_visibility_unit = UnitOfLength.MILES
            self._attr_native_wind_speed_unit = UnitOfSpeed.MILES_PER_HOUR
            
        self.get_forecast()    
    

    @property
    def native_temperature(self) -> float:
        """Return the temperature."""
        return self.coordinator.data["result"]['realtime']['temperature']

    @property
    def humidity(self) -> float:
        """Return the humidity."""
        return float(self.coordinator.data["result"]['realtime']['humidity']) * 100

    @property
    def native_wind_speed(self) -> float:
        """Return the wind speed."""
        return self.coordinator.data["result"]['realtime']['wind']['speed']
    

    @property
    def native_pressure(self) -> float:
        """Return the pressure."""
        return round(float(self.coordinator.data["result"]['realtime']['pressure'])/100)
    

    @property
    def condition(self) -> str:
        """Return the weather condition."""
        return CONDITION_MAP[self.coordinator.data["result"]["realtime"]["skycon"]]
        
    @property
    def available(self):
        """Return True if entity is available."""
        #return self.coordinator.last_update_success
        return (int(datetime.now().timestamp()) - int(self.coordinator.data["server_time"]) < 1800)
    
    ##更多属性
    
    @property
    def wind_bearing(self):
        """风向"""
        return self.coordinator.data["result"]['realtime']['wind']['direction']

    @property
    def native_visibility(self):
        """能见度"""
        return self.coordinator.data["result"]['realtime']['visibility']


    @property
    def pm25(self):
        """pm25，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['pm25']

    @property
    def pm10(self):
        """pm10，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['pm10']

    @property
    def o3(self):
        """臭氧，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['o3']

    @property
    def no2(self):
        """二氧化氮，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['no2']

    @property
    def so2(self):
        """二氧化硫，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['so2']

    @property
    def co(self):
        """一氧化碳，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['co']

    @property
    def aqi(self):
        """AQI（国标）"""
        return self.coordinator.data["result"]['realtime']['air_quality']['aqi']['chn']

    @property
    def aqi_description(self):
        """AQI（国标）"""
        return self.coordinator.data["result"]['realtime']['air_quality']['description']['chn']

    @property
    def aqi_usa(self):
        """AQI USA"""
        return self.coordinator.data["result"]['realtime']['air_quality']['aqi']['usa']
    
    @property
    def aqi_usa_description(self):
        """AQI USA"""
        return self.coordinator.data["result"]['realtime']['air_quality']['description']['usa']
    
    @property
    def forecast_hourly(self):
        """实时天气预报描述-小时"""
        return self.coordinator.data['result']['hourly']['description']

    @property
    def forecast_minutely(self):
        """实时天气预报描述-分钟"""
        return self.coordinator.data['result']['minutely']['description'] if self.coordinator.data['result'].get('minutely') else ""

    @property
    def forecast_minutely_probability(self):
        """分钟概率"""
        return self.coordinator.data['result']['minutely']['probability'] if self.coordinator.data['result'].get('minutely') else ""

    @property
    def forecast_alert(self):
        """天气预警"""
        alert = self.coordinator.data['result']['alert'] if 'alert' in self.coordinator.data['result'] else ""
        return alert
        
    @property
    def forecast_keypoint(self):
        """实时天气预报描述-注意事项"""
        return self.coordinator.data['result']['forecast_keypoint']        
        
    @property
    def updatetime(self):
        """实时天气预报获取时间."""
        return datetime.fromtimestamp(self.coordinator.data['server_time'])
        
    def get_forecast(self):
        forecast_daily = []
        for i in range(len(self.coordinator.data['result']['daily']['temperature'])):
            if self.coordinator.data['result']['daily']['precipitation'][i].get("probability"):
                pop = str(round(self.coordinator.data['result']['daily']['precipitation'][i].get("probability")))
            else:
                pop = 0
            time_str = self.coordinator.data['result']['daily']['temperature'][i]['date'][:10]
            data_item = [
                datetime.strptime(time_str, '%Y-%m-%d'),
                CONDITION_MAP[self.coordinator.data['result']['daily']['skycon'][i]['value']],
                self.coordinator.data['result']['daily']['precipitation'][i]['avg'],
                round(self.coordinator.data['result']['daily']['temperature'][i]['max']),
                round(self.coordinator.data['result']['daily']['temperature'][i]['min']),
                float(self.coordinator.data['result']['daily']['humidity'][i]['avg'])*100,
                pop,
                self.coordinator.data['result']['daily']['wind'][i]['avg']['direction'],
                self.coordinator.data['result']['daily']['wind'][i]['avg']['speed'],
                self.coordinator.data['result']['daily']['skycon'][i]['value'],
                CONDITION_CN_MAP[self.coordinator.data['result']['daily']['skycon'][i]['value']],
                self.getWindDir(self.coordinator.data['result']['daily']['wind'][i]['avg']['direction']),
                self.getWindLevel(self.coordinator.data['result']['daily']['wind'][i]['avg']['speed']),
                self.coordinator.data['result']['daily']['temperature_08h_20h'][i],
                self.coordinator.data['result']['daily']['temperature_20h_32h'][i],
                self.coordinator.data['result']['daily']['wind_08h_20h'][i],
                self.coordinator.data['result']['daily']['wind_20h_32h'][i],
                self.coordinator.data['result']['daily']['precipitation_08h_20h'][i],
                self.coordinator.data['result']['daily']['precipitation_20h_32h'][i],
                self.coordinator.data['result']['daily']['astro'][i]
            ]  
            forecast_daily.append(data_item)
             
        forecast_hourly = []
        for i in range(len(self.coordinator.data['result']['hourly']['precipitation'])):
            if self.coordinator.data['result']['hourly']['precipitation'][i].get("probability"):
                pop = str(round(self.coordinator.data['result']['hourly']['precipitation'][i].get("probability")))
            else:
                pop = 0
            date_obj = datetime.fromisoformat(self.coordinator.data['result']['hourly']['precipitation'][i].get("datetime").replace('Z', '+00:00'))
            formatted_date = datetime.strftime(date_obj, '%Y-%m-%d %H:%M')
            data_item = [
                formatted_date,
                CONDITION_MAP[self.coordinator.data['result']['hourly']['skycon'][i]['value']],
                self.coordinator.data['result']['hourly']['precipitation'][i]['value'],
                int(self.coordinator.data['result']['hourly']['temperature'][i]['value']),
                float(self.coordinator.data['result']['hourly']['humidity'][i]['value'])*100,
                pop,
                self.coordinator.data['result']['hourly']['wind'][i]['direction'],
                self.coordinator.data['result']['hourly']['wind'][i]['speed'],                
                self.coordinator.data['result']['hourly']['skycon'][i]['value'],
                CONDITION_CN_MAP[self.coordinator.data['result']['hourly']['skycon'][i]['value']],
                self.getWindDir(self.coordinator.data['result']['hourly']['wind'][i]['direction']),
                self.getWindLevel(self.coordinator.data['result']['hourly']['wind'][i]['speed']),
                round(self.coordinator.data['result']['hourly']['apparent_temperature'][i]['value']),                
            ]  
            forecast_hourly.append(data_item)
            
        forecast_twice_daily = []
        for i in range(len(self.coordinator.data['result']['daily']['precipitation'])):
            if self.coordinator.data['result']['daily']['precipitation'][i].get("probability"):
                pop = str(round(self.coordinator.data['result']['daily']['precipitation'][i].get("probability")))
            else:
                pop = 0
            time_str = self.coordinator.data['result']['daily']['temperature'][i]['date'][:10]                
            data_item = [
                datetime.strptime(time_str, '%Y-%m-%d').replace(hour=8, minute=00),
                CONDITION_MAP[self.coordinator.data['result']['hourly']['skycon'][i]['value']],
                self.coordinator.data['result']['daily']['precipitation_08h_20h'][i]['avg'],
                int(self.coordinator.data['result']['daily']['temperature_08h_20h'][i]['max']),
                int(self.coordinator.data['result']['daily']['temperature_08h_20h'][i]['min']),
                pop,
                True,
                self.coordinator.data['result']['daily']['wind_08h_20h'][i]['avg']['direction'],
                self.coordinator.data['result']['daily']['wind_08h_20h'][i]['avg']['speed'],
            ]  
            forecast_twice_daily.append(data_item)
            data_item = [
                datetime.strptime(time_str, '%Y-%m-%d').replace(hour=20, minute=00),
                CONDITION_MAP[self.coordinator.data['result']['hourly']['skycon'][i]['value']],
                self.coordinator.data['result']['daily']['precipitation_20h_32h'][i]['avg'],
                int(self.coordinator.data['result']['daily']['temperature_20h_32h'][i]['max']),
                int(self.coordinator.data['result']['daily']['temperature_20h_32h'][i]['min']),
                pop,
                False,
                self.coordinator.data['result']['daily']['wind_20h_32h'][i]['avg']['direction'],
                self.coordinator.data['result']['daily']['wind_20h_32h'][i]['avg']['speed'],
            ]  
            forecast_twice_daily.append(data_item)
            
            
        self._forecast_daily = forecast_daily
        self._forecast_hourly = forecast_hourly
        self._forecast_twice_daily = forecast_twice_daily
        self._attr_supported_features = 0
        if self._forecast_daily:
            self._attr_supported_features |= WeatherEntityFeature.FORECAST_DAILY
        if self._forecast_hourly:
            self._attr_supported_features |= WeatherEntityFeature.FORECAST_HOURLY
        if self._forecast_twice_daily:
            self._attr_supported_features |= WeatherEntityFeature.FORECAST_TWICE_DAILY

            
    async def async_forecast_daily(self) -> list[Forecast]:
        """Return the daily forecast."""
        #reftime = dt_util.now().replace(hour=16, minute=00)
        forecast_data = []
        assert self._forecast_daily is not None
        for entry in self._forecast_daily:
            data_dict = Forecast(
                datetime=entry[0],
                condition=entry[1],
                precipitation=entry[2],
                native_temperature=entry[3],
                native_templow=entry[4],
                humidity=entry[5],
                precipitation_probability=entry[6],
                wind_bearing=entry[7],
                native_wind_speed=entry[8],
            )
            #reftime = reftime + timedelta(hours=24)
            forecast_data.append(data_dict)

        return forecast_data


    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        #reftime = dt_util.now().replace(hour=16, minute=00)
        forecast_data = []
        assert self._forecast_hourly is not None
        for entry in self._forecast_hourly:
            data_dict = Forecast(
                datetime=entry[0],
                condition=entry[1],
                precipitation=entry[2],
                native_temperature=entry[3],
                humidity=entry[4],
                precipitation_probability=entry[5],
            )
            #reftime = reftime + timedelta(hours=1)
            forecast_data.append(data_dict)

        return forecast_data

    async def async_forecast_twice_daily(self) -> list[Forecast]:
        """Return the twice daily forecast."""
        #reftime = dt_util.now().replace(hour=8, minute=00)

        forecast_data = []
        assert self._forecast_twice_daily is not None
        for entry in self._forecast_twice_daily:
            data_dict = Forecast(
                datetime=entry[0],
                condition=entry[1],
                precipitation=entry[2],
                native_temperature=entry[3],
                native_templow=entry[4],
                precipitation_probability=entry[5],
                is_daytime=entry[6],
                wind_bearing=entry[7],
                native_wind_speed=entry[8],
            )
            #reftime = reftime + timedelta(hours=12)
            forecast_data.append(data_dict)

        return forecast_data

        
    @property
    def state_attributes(self):
        _LOGGER.debug(self.coordinator.data)
        data = super(ColorfulCloudsEntity, self).state_attributes
        data['forecast_hourly'] = self.forecast_hourly
        data['forecast_minutely'] = self.forecast_minutely
        data['forecast_probability'] = self.forecast_minutely_probability
        data['forecast_keypoint'] = self.forecast_keypoint
        data['forecast_alert'] = self.forecast_alert
        data['pm25'] = self.pm25
        data['pm10'] = self.pm10
        data['skycon'] = self.coordinator.data['result']['realtime']['skycon']
        data['o3'] = self.o3
        data['no2'] = self.no2
        data['so2'] = self.so2
        data['co'] = self.co
        data['aqi'] = self.aqi
        data['aqi_description'] = self.aqi_description
        data['aqi_usa'] = self.aqi_usa
        data['aqi_usa_description'] = self.aqi_usa_description
        data['update_time'] = self.updatetime
        
        data['daily_forecast'] = self.daily_forecast()
        data['hourly_forecast'] = self.hourly_forecast()
        data['forecast_hourly_summary'] = self.hourly_summary
        
        data['winddir'] = self.getWindDir(self.coordinator.data['result']['realtime']['wind']['direction'])
        data['windscale'] = self.getWindLevel(self.coordinator.data['result']['realtime']['wind']['speed'])
        
        data['sunrise'] = self.coordinator.data['result']['daily']['astro'][0]['sunrise']['time']
        data['sunset'] = self.coordinator.data['result']['daily']['astro'][0]['sunset']['time']
        
        data['city'] = self.coordinator.data['result']['alert']['adcodes'][len(self.coordinator.data['result']['alert']['adcodes'])-1]['name'] if self.coordinator.data['result'].get('alert') else ''
        
        if self.life == True:
            data[ATTR_SUGGESTION] = [{'title': k, 'title_cn': TRANSLATE_SUGGESTION.get(k,k), 'brf': v.get('desc'), 'txt': v.get('detail') } for k, v in self.coordinator.data['lifeindex'].items()]
        if self.custom_ui == True:
            data["custom_ui_more_info"] = "colorfulclouds-weather-more-info"
        return data    

    def daily_forecast(self):
        forecast_data = []
        for i in range(len(self.coordinator.data['result']['daily']['temperature'])):
            time_str = self.coordinator.data['result']['daily']['temperature'][i]['date'][:10]
            data_dict = {
                ATTR_FORECAST_TIME: datetime.strptime(time_str, '%Y-%m-%d'),
                ATTR_FORECAST_CONDITION: CONDITION_MAP[self.coordinator.data['result']['daily']['skycon'][i]['value']],
                "skycon": self.coordinator.data['result']['daily']['skycon'][i]['value'],
                "condition_cn": CONDITION_CN_MAP[self.coordinator.data['result']['daily']['skycon'][i]['value']],
                ATTR_FORECAST_NATIVE_PRECIPITATION: self.coordinator.data['result']['daily']['precipitation'][i]['avg'],
                ATTR_FORECAST_NATIVE_TEMP: int(self.coordinator.data['result']['daily']['temperature'][i]['max']),
                ATTR_FORECAST_NATIVE_TEMP_LOW: int(self.coordinator.data['result']['daily']['temperature'][i]['min']),
                ATTR_FORECAST_HUMIDITY: round(self.coordinator.data['result']['daily']['humidity'][i]['avg'],2),
                ATTR_FORECAST_WIND_BEARING: self.coordinator.data['result']['daily']['wind'][i]['avg']['direction'],
                ATTR_FORECAST_NATIVE_WIND_SPEED: self.coordinator.data['result']['daily']['wind'][i]['avg']['speed'],
                "winddir": self.getWindDir(self.coordinator.data['result']['daily']['wind'][i]['avg']['direction']),
                "windscale": self.getWindLevel(self.coordinator.data['result']['daily']['wind'][i]['avg']['speed']),
                "temperature_08h_20h": self.coordinator.data['result']['daily']['temperature_08h_20h'][i],
                "temperature_20h_32h": self.coordinator.data['result']['daily']['temperature_20h_32h'][i],
                "wind_08h_20h": self.coordinator.data['result']['daily']['wind_08h_20h'][i],
                "wind_20h_32h": self.coordinator.data['result']['daily']['wind_20h_32h'][i],
                "precipitation_08h_20h": self.coordinator.data['result']['daily']['precipitation_08h_20h'][i],
                "precipitation_20h_32h": self.coordinator.data['result']['daily']['precipitation_20h_32h'][i],
                "sundata": self.coordinator.data['result']['daily']['astro'][i]
            }
            forecast_data.append(data_dict)

        return forecast_data
        
    
    def hourly_forecast(self):
        
        hourly_data = {}
        hourly_data['hourly_precipitation'] = self.coordinator.data['result']['hourly']['precipitation']
        hourly_data['hourly_temperature'] = self.coordinator.data['result']['hourly']['temperature']
        hourly_data['hourly_apparent_temperature'] = self.coordinator.data['result']['hourly']['apparent_temperature']
        hourly_data['hourly_humidity'] = self.coordinator.data['result']['hourly']['humidity']
        hourly_data['hourly_cloudrate'] = self.coordinator.data['result']['hourly']['cloudrate']
        hourly_data['hourly_skycon'] = self.coordinator.data['result']['hourly']['skycon']
        hourly_data['hourly_wind'] = self.coordinator.data['result']['hourly']['wind']
        hourly_data['hourly_visibility'] = self.coordinator.data['result']['hourly']['visibility']
        hourly_data['hourly_aqi'] = self.coordinator.data['result']['hourly']['air_quality']['aqi']
        hourly_data['hourly_pm25'] = self.coordinator.data['result']['hourly']['air_quality']['pm25']        

        if hourly_data['hourly_precipitation']:
            summarystr = ""
            summarymaxprecipstr = ""
            summaryendstr = ""
            summaryday = ""
            summarystart = 0
            summaryend = 0
            summaryprecip = 0
            
            hourly_forecast_data = []
            for i in range(len(hourly_data['hourly_precipitation'])):
                #_LOGGER.debug("datetime: %s", hourly_data['hourly_precipitation'][i].get("datetime"))
                date_obj = datetime.fromisoformat(hourly_data['hourly_precipitation'][i].get("datetime").replace('Z', '+00:00'))
                formatted_date = datetime.strftime(date_obj, '%Y-%m-%d %H:%M')
                if hourly_data['hourly_precipitation'][i].get("probability"):
                    pop = str(round(hourly_data['hourly_precipitation'][i].get("probability")))
                else:
                    pop = 0
                    
                hourly_forecastItem = {
                    'skycon': hourly_data['hourly_skycon'][i]['value'],
                    ATTR_FORECAST_NATIVE_TEMP: round(hourly_data['hourly_temperature'][i]['value']),
                    ATTR_FORECAST_HUMIDITY: round(hourly_data['hourly_humidity'][i]['value'],2),
                    'cloudrate': hourly_data['hourly_cloudrate'][i]['value'],
                    ATTR_FORECAST_NATIVE_WIND_SPEED: hourly_data['hourly_wind'][i]['speed'],
                    ATTR_FORECAST_WIND_BEARING: hourly_data['hourly_wind'][i]['direction'],
                    'visibility': hourly_data['hourly_visibility'][i]['value'],
                    'aqi': hourly_data['hourly_aqi'][i]['value'],
                    'pm25': hourly_data['hourly_pm25'][i]['value'],
                    'datetime': formatted_date, #hourly_data['hourly_precipitation'][i]['datetime'][:16].replace('T', ' '),
                    ATTR_FORECAST_NATIVE_PRECIPITATION: hourly_data['hourly_precipitation'][i]['value'],
                    'probable_precipitation': pop,
                    'condition': CONDITION_MAP[hourly_data['hourly_skycon'][i]['value']],
                    'condition_cn': CONDITION_CN_MAP[hourly_data['hourly_skycon'][i]['value']],
                    "winddir": self.getWindDir(hourly_data['hourly_wind'][i]['direction']),
                    "windscale": self.getWindLevel(hourly_data['hourly_wind'][i]['speed'])                    
                }
                hourly_forecast_data.append(hourly_forecastItem)
                
            return hourly_forecast_data
            
            
    def getWindDir(self, deg):
        #_LOGGER.debug(int((deg + 11.25) / 22.5))
        return WINDDIRECTIONS[int((deg + 11.25) / 22.5)]

    
    def getWindLevel(self, res):
        res2, res3, res4 = None, None, None
        if float(res) < 1:
            res2 = "0"
            res3 = "无风"
            res4 = "静，烟直上"
        elif float(res) < 6:
            res2 = "1"
            res3 = "软风"
            res4 = "烟示风向"
        elif float(res) < 12:
            res2 = "2"
            res3 = "轻风"
            res4 = "感觉有风"
        elif float(res) < 20:
            res2 = "3"
            res3 = "微风"
            res4 = "旌旗展开"
        elif float(res) < 29:
            res2 = "4"
            res3 = "和风"
            res4 = "吹起尘土"
        elif float(res) < 39:
            res2 = "5"
            res3 = "清风"
            res4 = "小树摇摆"
        elif float(res) < 50:
            res2 = "6"
            res3 = "强风"
            res4 = "电线有声"
        elif float(res) < 62:
            res2 = "7"
            res3 = "劲风（疾风）"
            res4 = "步行困难"
        elif float(res) < 75:
            res2 = "8"
            res3 = "狂风大作"
            res4 = "狂风大作"
        elif float(res) < 88:
            res2 = "9"
            res3 = "狂风呼啸"
            res4 = "狂风呼啸"
        elif float(res) < 103:
            res2 = "10"
            res3 = "暴风毁树"
            res4 = "暴风毁树"
        elif float(res) < 118:
            res2 = "11"
            res3 = "暴风毁树"
            res4 = "暴风毁树"
        elif float(res) < 134:
            res2 = "12"
            res3 = "飓风"
            res4 = "飓风"
        elif float(res) < 150:
            res2 = "13"
            res3 = "台风"
            res4 = "台风"
        elif float(res) < 167:
            res2 = "14"
            res3 = "强台风"
            res4 = "强台风"
        elif float(res) < 184:
            res2 = "15"
            res3 = "强台风"
            res4 = "强台风"
        elif float(res) < 202:
            res2 = "16"
            res3 = "超强台风"
            res4 = "超强台风"
        else:
            res2 = "17+"
            res3 = "超强台风"
            res4 = "超强台风"
        return res2
    
    
    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        """Set up a timer updating the forecasts."""

        async def update_forecasts(_: datetime) -> None:
            # if self._forecast_daily:
                # self._forecast_daily = (
                    # self._forecast_daily[1:] + self._forecast_daily[:1]
                # )
            # if self._forecast_hourly:
                # self._forecast_hourly = (
                    # self._forecast_hourly[1:] + self._forecast_hourly[:1]
                # )
            # if self._forecast_twice_daily:
                # self._forecast_twice_daily = (
                    # self._forecast_twice_daily[1:] + self._forecast_twice_daily[:1]
                # )
            self.get_forecast() 
            await self.async_update_listeners(None)

        self._update_forecasts_handle = async_track_time_interval(
            self.hass, update_forecasts, timedelta(minutes=5)
        )

        self._write_ha_state_handle = self.coordinator.async_add_listener(
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self):
        """Cancel the timers when the entity is removed."""
        self._update_forecasts_handle.cancel()
        self._write_ha_state_handle.cancel()

    async def async_update(self):
        """Update Colorfulclouds entity."""
        await self.coordinator.async_request_refresh()        
              