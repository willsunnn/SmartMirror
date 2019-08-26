"""https://developers.google.com/calendar/overview"""

from Widgets.BaseWidget import BaseWidget
import urllib.request
import json


class WeatherWidget(BaseWidget):
    query_base = "https://samples.openweathermap.org/data/2.5/weather?zip={},{}&APPID={}"
    api_key_path = "config/OpenWeatherAPI/OpenWeatherAPIKey.txt"

    @staticmethod
    def get_necessary_config():
        """Ensures that all the necesarry files to run this widget are found in the directory"""
        return [WeatherWidget.api_key_path]

    def __init__(self, parent, subwidgets=[], constraints=[], props={}):
        BaseWidget.__init__(self, parent, subwidgets, constraints, props)
        self.zip_code = WeatherWidget.prop_get(props, "zip code", "92617")
        self.country_code = WeatherWidget.prop_get(props, "country code", "us")
        self.api_key = WeatherWidget.get_api_key_from_file()

    @staticmethod
    def get_api_key_from_file():
        with open(WeatherWidget.api_key_path, 'r') as api_txt:
            return api_txt.readline().strip()

    def update_values(self, *args, **kargs) -> ((), {}):
        url = WeatherWidget.query_base.format(self.zip_code, self.country_code, self.api_key)
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode(encoding="utf-8"))
        response.close()
        print(data)
        return args, kargs
