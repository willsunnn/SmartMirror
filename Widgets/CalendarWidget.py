"https://developers.google.com/calendar/overview"

from BaseWidget import BaseWidget


class CalendarWidget(BaseWidget):
    @staticmethod
    def get_necesarry_config():
        import os
        return [os.path.join("config", "GoogleAPI", "credentials.json")]
