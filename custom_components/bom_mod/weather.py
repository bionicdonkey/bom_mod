"""Support for Australian BOM (Bureau of Meteorology) weather service."""
import logging

import voluptuous as vol

from homeassistant.components.weather import PLATFORM_SCHEMA, ATTR_FORECAST_CONDITION, ATTR_FORECAST_PRECIPITATION, ATTR_FORECAST_TEMP, ATTR_FORECAST_TEMP_LOW, ATTR_FORECAST_TIME, ATTR_WEATHER_VISIBILITY, WeatherEntity
from homeassistant.const import (
    CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, TEMP_CELSIUS)
from homeassistant.helpers import config_validation as cv
from typing import Dict, List

# Reuse data and API logic from the sensor implementation
from .sensor import (
    CONF_STATION, BOMCurrentData, BOMForecastData, closest_station, validate_station, validate_days)
    
SENSOR_TYPES = {
    'max': ['air_temperature_maximum', 'Max Temp C', TEMP_CELSIUS, 'mdi:thermometer'],
    'min': ['air_temperature_minimum', 'Min Temp C', TEMP_CELSIUS, 'mdi:thermometer'],
    'chance_of_rain': ['probability_of_precipitation', 'Chance of Rain', '%', 'mdi:water-percent'],
    'possible_rainfall': ['precipitation_range', 'Possible Rainfall', 'mm', 'mdi:water'],
    'summary': ['precis', 'Summary', None, 'mdi:text'],
    'icon': ['forecast_icon_code', 'Icon', None, None]
}

CONDITION_CLASSES = {
    'clear-night': [2],
    'cloudy': [4],
    'fog': [6, 10],
    'hail': [16],
    'lightning': [],
    'lightning-rainy': [16],
    'partlycloudy': [3],
    'pouring': [11],
    'rainy': [8, 17, 18],
    'snowy': [15],
    'snowy-rainy': [],
    'sunny': [1],
    'windy': [9],
    'windy-variant': [13],
    'exceptional': [19],
}

FORECASTED_DAYS = 7
CONF_FORECAST_PRODUCT_ID = 'forecast_product_id'
CONF_FORECAST_PRODUCT_AAC = 'forecast_product_aac'

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_STATION): validate_station,
    vol.Optional(CONF_FORECAST_PRODUCT_ID): cv.string,
    vol.Optional(CONF_FORECAST_PRODUCT_AAC, default=''): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the BOM weather platform."""
    station = config.get(CONF_STATION) or closest_station(
        config.get(CONF_LATITUDE),
        config.get(CONF_LONGITUDE),
        hass.config.config_dir)
    if station is None:
        _LOGGER.error("Could not get BOM weather station from lat/lon")
        return False
    
    iForcastedDays = FORECASTED_DAYS
    sProductID = config.get(CONF_FORECAST_PRODUCT_ID)
    sProductAAC = config.get(CONF_FORECAST_PRODUCT_AAC)

    if sProductID is not None:
        oBOMForecastData = BOMForecastData(sProductID, sProductAAC, iForcastedDays)
        try:
            oBOMForecastData.update()
        except ValueError as err:
            _LOGGER.error("Received error from BOM_Forecast: %s", err)
    
    bom_data = BOMCurrentData(station)
    try:
        bom_data.update()
    except ValueError as err:
        _LOGGER.error("Received error from BOM_Current: %s", err)
        return False
    add_entities([BOMWeatherMod(bom_data, config.get(CONF_NAME), oBOMForecastData)], True)


class BOMWeatherMod(WeatherEntity):

    """Representation of a weather condition."""

    def __init__(self, bom_data, stationname=None, pBOMForecastData=None):
        """Initialise the platform with a data instance and station name."""
        self.bom_data = bom_data
        self.stationname = stationname or self.bom_data.latest_data.get('name')
        self._BOMForecastData = pBOMForecastData

    def update(self):
        """Update current conditions."""
        self.bom_data.update()
        if self._BOMForecastData is not None:
            self._BOMForecastData.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'BOM {}'.format(self.stationname or '(unknown station)')

    @property
    def condition(self):
        """Return the current condition."""
        if self._BOMForecastData is not None:
            return next((
                k for k, v in CONDITION_CLASSES.items()
                if int(self._BOMForecastData.GetReading('forecast_icon_code', 0)) in v), None)
        return next((
                k for k, v in CONDITION_CLASSES.items()
                if self.bom_data.get_reading('weather') in v), None)
        

    # Now implement the WeatherEntity interface

    @property
    def temperature(self):
        """Return the platform temperature."""
        return self.bom_data.get_reading('air_temp')

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def pressure(self):
        """Return the mean sea-level pressure."""
        return self.bom_data.get_reading('press_msl')

    @property
    def humidity(self):
        """Return the relative humidity."""
        return self.bom_data.get_reading('rel_hum')

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return self.bom_data.get_reading('wind_spd_kmh')
    
    @property   
    def visibility(self):
        """Return the visibility."""
        return self.bom_data.get_reading('vis_km')  

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        directions = ['N', 'NNE', 'NE', 'ENE',
                      'E', 'ESE', 'SE', 'SSE',
                      'S', 'SSW', 'SW', 'WSW',
                      'W', 'WNW', 'NW', 'NNW']
        wind = {name: idx * 360 / 16 for idx, name in enumerate(directions)}
        return wind.get(self.bom_data.get_reading('wind_dir'))

    @property
    def attribution(self):
        """Return the attribution."""
        return "Data provided by the Australian Bureau of Meteorology"
        
    @property
    def forecast(self) -> List:
        """Return the forecast."""
        if self._BOMForecastData is None:
            return None

        data = []
        
        for index in range(1, self._BOMForecastData.ForecastedDays):
            try:
                conditionIcon = next((
                    k for k, v in CONDITION_CLASSES.items()
                    if int(self._BOMForecastData.GetReading('forecast_icon_code', index)) in v), None)
                data.append({
                    ATTR_FORECAST_TIME: self._BOMForecastData.GetForcastPeriodStartTime(index),
                    ATTR_FORECAST_TEMP: int(self._BOMForecastData.GetReading('air_temperature_maximum', index)),
                    ATTR_FORECAST_TEMP_LOW: int(self._BOMForecastData.GetReading('air_temperature_minimum', index)),
                    ATTR_FORECAST_PRECIPITATION: self._BOMForecastData.GetReading('probability_of_precipitation', index).strip('%'),
                    ATTR_FORECAST_CONDITION: conditionIcon,
                })
            except ValueError as err:
                _LOGGER.error("Forecast out of range: %s", err)

        return data

