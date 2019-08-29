from tkinter import Label
from Widgets.BaseWidget import BaseWidget
import urllib.request
import json
from PIL import ImageTk, Image


class WeatherWidget(BaseWidget):
    query_base = "https://api.openweathermap.org/data/2.5/weather?zip={},{}&APPID={}"
    img_link = "http://openweathermap.org/img/wn/{}@2x.png"
    api_key_path = "config/OpenWeatherAPI/OpenWeatherAPIKey.txt"
    font = ("Helvetica", 14)

    @staticmethod
    def get_necessary_config():
        """Ensures that all the necessary files to run this widget are found in the directory"""
        return [WeatherWidget.api_key_path]

    @staticmethod
    def get_api_key_from_file():
        with open(WeatherWidget.api_key_path, 'r') as api_txt:
            return api_txt.readline().strip()

    def __init__(self, parent, subwidgets=[], constraints=[], props={}):
        BaseWidget.__init__(self, parent, subwidgets, constraints, props)
        self.config(bg=self.get_bg())
        self.zip_code = WeatherWidget.prop_get(props, "zip code", "92617")
        self.country_code = WeatherWidget.prop_get(props, "country code", "us")
        self.units = WeatherWidget.prop_get(props, "temperature units", "celsius", lambda x: x in ["celsius", "fahrenheit"])
        self.rounding = WeatherWidget.prop_get(props, "rounding", 0, lambda x: x >= 0)
        self.api_key = WeatherWidget.get_api_key_from_file()
        self.data = {}

        self.city_label = Label(self, font=self.get_font("Large"), bg=self.get_bg(), fg=self.get_fg())
        self.icon_label = Label(self, bg=self.get_bg(), fg=self.get_fg())
        self.temp_label = Label(self, font=self.get_font("huge"), bg=self.get_bg(), fg=self.get_fg())
        self.update_values()

    def place(self, *args, **kargs):
        BaseWidget.place(self, *args, **kargs)
        self.city_label.grid(row=0)
        self.icon_label.grid(row=1)
        self.temp_label.grid(row=2)

    def update_values(self, *args, **kargs) -> ((), {}):
        url = WeatherWidget.query_base.format(self.zip_code, self.country_code, self.api_key)
        with urllib.request.urlopen(url) as response:
            self.data = json.loads(response.read().decode(encoding="utf-8"))
        self.update_labels()
        return args, kargs

    def update_labels(self):
        self.city_label.config(text=self.data.get("name", "City not found in recieved data"))
        self.temp_label.config(text=round(self.convert_temperature(self.data.get("main", {"temp": 0}).get("temp", 0)), self.rounding))   # defaults to 0 kelvin
        self.icon_label.photo_ref = ImageTk.PhotoImage(self.get_icon())
        self.icon_label.config(image=self.icon_label.photo_ref)

    def convert_temperature(self, num, to=None):
        if to is None:
            return self.convert_temperature(num, to=self.units)
        if to == "celsius":
            return num - 273.15
        else:
            return self.convert_temperature(num, to="celsius") * 9/5 + 32

    def get_icon(self):
        """ gets an icon that represents the weather from the API provider
        https://openweathermap.org/weather-conditions"""
        icon_id = self.data.get("weather", [{"icon": "01d"}])[0].get("icon", "01d")     # defaults to clear day icon
        with urllib.request.urlopen(WeatherWidget.img_link.format(icon_id)) as response:
            return Image.open(response)
