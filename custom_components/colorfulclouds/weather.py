import logging
import json
import time
from datetime import datetime, timedelta
from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    WeatherEntity,
)
from homeassistant.const import (
    CONF_NAME,
    LENGTH_INCHES,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    LENGTH_MILLIMETERS,
    PRESSURE_HPA,
    PRESSURE_INHG,
    SPEED_KILOMETERS_PER_HOUR,
    SPEED_MILES_PER_HOUR,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from .const import (
    ATTRIBUTION,
    COORDINATOR,
    ROOT_PATH,
    DOMAIN,
    NAME,
    MANUFACTURER,
    CONF_LIFEINDEX,
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
    'NightLifeIndex': '夜生活',
    'BoatingIndex': '划船指数',
    'RoadConditionIndex': '路况指数',
    'TrafficIndex': '交通指数',
    'ultraviolet': '紫外线',
    'carWashing': '洗车指数',
    'dressing': '穿衣指数',
    'comfort': '舒适度指数',
    'coldRisk': '感冒指数',
}

ATTR_SUGGESTION = "suggestion"

async def async_setup_entry(hass, config_entry, async_add_entities):    
    """Add a Colorfulclouds weather entity from a config_entry."""
    name = config_entry.data[CONF_NAME]
    life = config_entry.options.get(CONF_LIFEINDEX, False)

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    _LOGGER.debug("metric: %s", coordinator.data["is_metric"])

    async_add_entities([ColorfulCloudsEntity(name, life, coordinator)], False)
            
class ColorfulCloudsEntity(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, name, life, coordinator):
        
        self.coordinator = coordinator
        _LOGGER.debug("coordinator: %s", coordinator.data["server_time"])
        self._name = name
        self.life = life
        self._attrs = {}
        self._hourly_data = []
        self.hourly_summary = ""

        # self._unit_system = "Metric" if self.coordinator.data["is_metric"]=="metric:v2" else "Imperial"
        # Coordinator data is used also for sensors which don't have units automatically
        # converted, hence the weather entity's native units follow the configured unit
        # system
        if self.coordinator.data["is_metric"]=="metric:v2":
            self._attr_native_precipitation_unit = LENGTH_MILLIMETERS
            self._attr_native_pressure_unit = PRESSURE_HPA
            self._attr_native_temperature_unit = TEMP_CELSIUS
            self._attr_native_visibility_unit = LENGTH_KILOMETERS
            self._attr_native_wind_speed_unit = SPEED_KILOMETERS_PER_HOUR
            self._unit_system = "Metric"
        else:
            self._unit_system = "Imperial"
            self._attr_native_precipitation_unit = LENGTH_INCHES
            self._attr_native_pressure_unit = PRESSURE_INHG
            self._attr_native_temperature_unit = TEMP_FAHRENHEIT
            self._attr_native_visibility_unit = LENGTH_MILES
            self._attr_native_wind_speed_unit = SPEED_MILES_PER_HOUR
        

    @property
    def name(self):
        return self._name
        
    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION
        
    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        _LOGGER.debug("weather_unique_id: %s", self.coordinator.data["location_key"])
        return self.coordinator.data["location_key"]

    @property
    def device_info(self):
        """Return the device info."""
        info = {
            "identifiers": {(DOMAIN, self.coordinator.data["location_key"])},
            "name": self._name,
            "manufacturer": MANUFACTURER,
        }        
        from homeassistant.helpers.device_registry import DeviceEntryType
        info["entry_type"] = DeviceEntryType.SERVICE        
        return info

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        #return self.coordinator.last_update_success
        return (int(datetime.now().timestamp()) - int(self.coordinator.data["server_time"]) < 1800)
        
    @property
    def condition(self):
        """Return the weather condition."""
        skycon = self.coordinator.data["result"]["realtime"]["skycon"]
        return CONDITION_MAP[skycon]

    @property
    def native_temperature(self):
        return self.coordinator.data["result"]['realtime']['temperature']

    @property
    def humidity(self):
        return float(self.coordinator.data["result"]['realtime']['humidity']) * 100

    @property
    def native_wind_speed(self):
        """风速"""
        return self.coordinator.data["result"]['realtime']['wind']['speed']

    @property
    def wind_bearing(self):
        """风向"""
        return self.coordinator.data["result"]['realtime']['wind']['direction']

    @property
    def native_visibility(self):
        """能见度"""
        return self.coordinator.data["result"]['realtime']['visibility']

    @property
    def native_pressure(self):
        return round(float(self.coordinator.data["result"]['realtime']['pressure'])/100)

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
        return self.coordinator.data['result']['minutely']['description']

    @property
    def forecast_minutely_probability(self):
        """分钟概率"""
        return self.coordinator.data['result']['minutely']['probability']

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
        
        data['hourly_forecast'] = self.hourly_forecast()
        data['forecast_hourly_summary'] = self.hourly_summary
        
        data['winddir'] = self.getWindDir(self.coordinator.data['result']['realtime']['wind']['direction'])
        data['windscale'] = self.getWindLevel(self.coordinator.data['result']['realtime']['wind']['speed'])

        data['hourly_precipitation'] = self.coordinator.data['result']['hourly']['precipitation']
        data['hourly_temperature'] = self.coordinator.data['result']['hourly']['temperature']
        data['hourly_cloudrate'] = self.coordinator.data['result']['hourly']['cloudrate']
        data['hourly_skycon'] = self.coordinator.data['result']['hourly']['skycon']
        data['hourly_wind'] = self.coordinator.data['result']['hourly']['wind']
        data['hourly_visibility'] = self.coordinator.data['result']['hourly']['visibility']
        data['hourly_aqi'] = self.coordinator.data['result']['hourly']['air_quality']['aqi']
        data['hourly_pm25'] = self.coordinator.data['result']['hourly']['air_quality']['pm25']
        
        if self.life == True:
            data[ATTR_SUGGESTION] = [{'title': k, 'title_cn': TRANSLATE_SUGGESTION.get(k,k), 'brf': v.get('desc'), 'txt': v.get('detail') } for k, v in self.coordinator.data['lifeindex'].items()]
            data["custom_ui_more_info"] = "colorfulclouds-weather-more-info"        
        return data  

    @property
    def forecast(self):
        forecast_data = []
        for i in range(len(self.coordinator.data['result']['daily']['temperature'])):
            time_str = self.coordinator.data['result']['daily']['temperature'][i]['date'][:10]
            data_dict = {
                ATTR_FORECAST_TIME: datetime.strptime(time_str, '%Y-%m-%d'),
                ATTR_FORECAST_CONDITION: CONDITION_MAP[self.coordinator.data['result']['daily']['skycon'][i]['value']],
                "skycon": self.coordinator.data['result']['daily']['skycon'][i]['value'],
                "condition_cn": CONDITION_CN_MAP[self.coordinator.data['result']['daily']['skycon'][i]['value']],
                ATTR_FORECAST_NATIVE_PRECIPITATION: self.coordinator.data['result']['daily']['precipitation'][i]['avg'],
                ATTR_FORECAST_NATIVE_TEMP: self.coordinator.data['result']['daily']['temperature'][i]['max'],
                ATTR_FORECAST_NATIVE_TEMP_LOW: self.coordinator.data['result']['daily']['temperature'][i]['min'],
                ATTR_FORECAST_WIND_BEARING: self.coordinator.data['result']['daily']['wind'][i]['avg']['direction'],
                ATTR_FORECAST_NATIVE_WIND_SPEED: self.coordinator.data['result']['daily']['wind'][i]['avg']['speed'],
                "winddir": self.getWindDir(self.coordinator.data['result']['daily']['wind'][i]['avg']['direction']),
                "windscale": self.getWindLevel(self.coordinator.data['result']['daily']['wind'][i]['avg']['speed'])
            }
            forecast_data.append(data_dict)

        return forecast_data
        
    
    def hourly_forecast(self):
        
        hourly_data = {}
        hourly_data['hourly_precipitation'] = self.coordinator.data['result']['hourly']['precipitation']
        hourly_data['hourly_temperature'] = self.coordinator.data['result']['hourly']['temperature']
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
                _LOGGER.debug("datetime: %s", hourly_data['hourly_precipitation'][i].get("datetime"))
                date_obj = datetime.fromisoformat(hourly_data['hourly_precipitation'][i].get("datetime").replace('Z', '+00:00'))
                formatted_date = datetime.strftime(date_obj, '%Y-%m-%d %H:%M')
                if hourly_data['hourly_precipitation'][i].get("probability"):
                    pop = str(round(hourly_data['hourly_precipitation'][i].get("probability")))
                else:
                    pop = 0
                    
                hourly_forecastItem = {
                    'skycon': hourly_data['hourly_skycon'][i]['value'],
                    ATTR_FORECAST_NATIVE_TEMP: round(hourly_data['hourly_temperature'][i]['value']),
                    'humidity': round(hourly_data['hourly_humidity'][i]['value'],2),
                    'cloudrate': hourly_data['hourly_cloudrate'][i]['value'],
                    ATTR_FORECAST_NATIVE_WIND_SPEED: hourly_data['hourly_wind'][i]['speed'],
                    ATTR_FORECAST_WIND_BEARING: hourly_data['hourly_wind'][i]['direction'],
                    'visibility': hourly_data['hourly_visibility'][i]['value'],
                    'aqi': hourly_data['hourly_aqi'][i]['value'],
                    'pm25': hourly_data['hourly_pm25'][i]['value'],
                    'datetime': hourly_data['hourly_precipitation'][i]['datetime'][:16].replace('T', ' '),
                    ATTR_FORECAST_NATIVE_PRECIPITATION: hourly_data['hourly_precipitation'][i]['value'],
                    'probable_precipitation': pop,
                    'condition': CONDITION_MAP[hourly_data['hourly_skycon'][i]['value']],
                    'condition_cn': CONDITION_CN_MAP[hourly_data['hourly_skycon'][i]['value']],
                    "winddir": self.getWindDir(hourly_data['hourly_wind'][i]['direction']),
                    "windscale": self.getWindLevel(hourly_data['hourly_wind'][i]['speed'])
                }
                hourly_forecast_data.append(hourly_forecastItem)    
                            
                if float(hourly_data['hourly_precipitation'][i]['value'])>0.1 and summarystart > 0:
                    if summarystart < 4:
                        summarystr = str(summarystart)+"小时后转"+ CONDITION_CN_MAP[hourly_data['hourly_skycon'][i]['value']] +"。"
                    else:
                        if int(datetime.strftime(date_obj, '%H')) > int(datetime.now().strftime("%H")):
                            summaryday = "今天"
                        else:
                            summaryday = "明天"
                        summarystr = summaryday + str(int(datetime.strftime(date_obj, '%H')))+"点后转"+ CONDITION_CN_MAP[hourly_data['hourly_skycon'][i]['value']] +"。"
                    summarystart = -1000
                    summaryprecip = float(hourly_data['hourly_precipitation'][i]['value'])
                if float(hourly_data['hourly_precipitation'][i]['value'])>0.1 and float(hourly_data['hourly_precipitation'][i]['value']) > summaryprecip:
                    if int(datetime.strftime(date_obj, '%H')) > int(datetime.now().strftime("%H")):
                        summaryday = "今天"
                    else:
                        summaryday = "明天"
                    probablestr = ""
                    summarymaxprecipstr = summaryday + str(int(datetime.strftime(date_obj, '%H')))+"点为"+CONDITION_CN_MAP[hourly_data['hourly_skycon'][i]['value']] + "！"
                    summaryprecip = float(hourly_data['hourly_precipitation'][i]['value'])
                    summaryend ==0
                    summaryendstr = ""
                # _LOGGER.debug("hourly precip：%s", hourly_data['hourly_precipitation'][i]['value'])
                if float(hourly_data['hourly_precipitation'][i]['value']) == 0 and summaryprecip>0 and summaryend ==0:
                    if int(datetime.strftime(date_obj, '%H')) > int(datetime.now().strftime("%H")):
                        summaryday = "今天"
                    else:
                        summaryday = "明天"
                    summaryendstr = summaryday + str(int(datetime.strftime(date_obj, '%H')))+"点后转"+CONDITION_CN_MAP[hourly_data['hourly_skycon'][i]['value']]+"。"
                    summaryend += 1
                summarystart += 1
            if summarystr:
                hourly_summary = summarystr + summarymaxprecipstr + summaryendstr
            else:
                hourly_summary = "未来24小时内无降水"
                
            self.hourly_summary = hourly_summary    
            
            return hourly_forecast_data

    
    def getWindDir(self, deg):
        _LOGGER.debug(int((deg + 11.25) / 22.5))
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
        else:
            res2 = "7+"
            res3 = "大风以上"
            res4 = "有破坏性"
        return res2
    
    
    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Colorfulclouds entity."""
        await self.coordinator.async_request_refresh()
        