# Overview
Home Assistant BOM Weather Component Mod to include forcast data. 
Mashup of current [BOM Component](https://github.com/home-assistant/home-assistant/tree/dev/homeassistant/components/bom) and BOM Forecast Sensor from https://github.com/bremor/bom_forecast

The `bomweather' weather platform uses the Australian Bureau of Meteorology (BOM) as a source for current observational and forecast meteorological data.

The configuration variables are the same as the existing BOM Component with the addtion of the forecast variables shown the example below.

```yaml
# Example configuration.yaml entry
weather:
  - platform: bomweather
    station: IDN60901.94767
    forecast_product_id: IDN11060
    forecast_product_aac: NSW_PW005
```


Obtain the Product ID and Area Code for any BOM location using the following method:
- Go to [this](http://reg.bom.gov.au/catalogue/data-feeds.shtml) website and find the Precis Forecast XML link for your state in the "Long form forecasts" table or see the Table below.
- The Product ID (forecast_product_id) for your city is the name of the XML file and will look like "IDN11060"
- To find the Area Code (forecast_product_aac), download the XML mentioned in the previous steps. Open the XMl file in any text editor and browse or search the file looking for your area name. The Area Code will be in the same line as the area name and look like "NSW_PW005"

### Installation

To add the BOM Weather Mod Component to your installation, create this following folder structure in your config directory (if not already existing):

    “custom_components/bom_mod”.

Then, drop the following files into that folder:

    __init__.py
    camera.py
    manifest.json
    sensor.py
    weather.py
    
### BOM State Precis Product ID's
| State   | Value |
| :------- | :-------:|
| NSW/ACT | IDN11060 |
| NT      | IDD10207 |
| QLD     | IDQ11295 |
| SA      | IDS10044 |
| TAS     | IDT16710 |
| VIC     | IDV10753 |
| WA      | IDW14199 |


