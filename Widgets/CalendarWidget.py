"""https://developers.google.com/calendar/overview"""

from Widgets.BaseWidget import BaseWidget
import pickle


class CalendarWidget(BaseWidget):
    scope = 'https://www.googleapis.com/auth/calendar.readonly'
    credentials_path = "config/GoogleAPI/credentials.json"
    token_path = "config/GoogleAPI/token.pickle"

    @staticmethod
    def get_necessary_config():
        """Ensures that all the necesarry files to run this widget are found in the directory"""
        return [CalendarWidget.credentials_path]

    @staticmethod
    def get_credentials():
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if BaseWidget.check_file_exists(CalendarWidget.credentials_path):
            with open(CalendarWidget.token_path, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CalendarWidget.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(CalendarWidget.token_path, 'wb') as token:
                pickle.dump(creds, token)
        return creds

    @staticmethod
    def main():
        pass


import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = CalendarWidget.get_credentials()

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

if __name__ == '__main__':
    main()