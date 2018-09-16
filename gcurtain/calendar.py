# coding: utf-8
import googleapiclient.discovery
from google.oauth2 import service_account

from .core import conf

with conf.declare_group('calendar') as cg:
    cg.service_account_file = 'path-to-file'
    cg.delegated_subject = 'email-of-someone'


class Calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, service_account_file, delegated_subject=None):

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=self.SCOPES)
        if delegated_subject is not None:
            credentials = credentials.with_subject(delegated_subject)
        self.credentials = credentials

        self.service = googleapiclient.discovery.build(
            'calendar', 'v3', credentials=self.credentials)

    def list_recent_updated(self, calendar_id, updated_min):
        events_result = self.service.events().list(
            calendarId=calendar_id,
            updatedMin=updated_min.isoformat(),
            maxResults=100,
            singleEvents=True,
            orderBy='updated').execute()
        return events_result


client = Calendar(conf.calendar.service_account_file,
                  conf.calendar.delegated_subject)
