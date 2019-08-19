"""https://developers.google.com/calendar/overview"""

from Widgets.BaseWidget import BaseWidget
import pickle
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class CalendarWidget(BaseWidget):
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']
    credentials_path = "config/GoogleCalendarAPI/credentials.json"
    token_path = "config/GoogleCalendarAPI/token.pickle"

    @staticmethod
    def get_necessary_config():
        """Ensures that all the necesarry files to run this widget are found in the directory"""
        return [CalendarWidget.credentials_path]

    @staticmethod
    def get_credentials():
        """gets valid credentials that are required to access the Google Calendar API
        modified code from https://developers.google.com/calendar/quickstart/python"""
        creds = None
        if BaseWidget.check_file_exists(CalendarWidget.token_path):
            with open(CalendarWidget.token_path, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CalendarWidget.credentials_path, CalendarWidget.scopes)
                creds = flow.run_local_server(port=0)
            with open(CalendarWidget.token_path, 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def update_values(self, *args, **kargs) -> ((), {}):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        service = build('calendar', 'v3', credentials=CalendarWidget.get_credentials())

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                            maxResults=10, singleEvents=True,
                                            orderBy='startTime').execute()
        print(events_result)
        """
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
        """
        return args, kargs