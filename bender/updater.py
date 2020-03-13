import os.path
import pickle
import sqlite3

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from bender.sql_utils import set_state, make_files_dict
from bender.drive_utils import get_files_list, handle_message


class DriveUpdater:
    def __init__(self, config):
        self.scopes = config.scopes
        self.credentials = config.credentials
        self.token_file = config.token_file
        self.service = self.build_service()
        if config.reset_state:
            self.state = '2012-01-04T12:00:00-08:00'
        else:
            self.state = set_state()
        self.get_messages()

    def build_service(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials, self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
        return service

    def get_messages(self):
        q = f"modifiedTime > '{self.state}' or trashed=true"
        messages = []
        fields = "nextPageToken, files(id, name, parents, trashed, webViewLink, webContentLink, createdTime, " \
                 "modifiedTime, lastModifyingUser) "
        files = get_files_list(self.service, q, fields)
        conn = sqlite3.connect("bender/mediabuy.db")
        cursor = conn.cursor()
        query = "SELECT id, name, parent_id, full_path FROM files WHERE trashed=False "
        cursor.execute(query)
        table_files = make_files_dict(cursor.fetchall())
        for file in files:
            db_file = table_files.get(file.get('id'))
            if db_file and file.get('trashed') is not True:
                type_msg = 'updated'
                message = handle_message(self.service, type_msg, file, db_file)
                messages.append(message)
            elif db_file and file.get('trashed') is True:
                type_msg = 'trashed'
                message = handle_message(self.service, type_msg, file, db_file)
                messages.append(message)
            elif not db_file and file.get('trashed') is not True:
                type_msg = 'created'
                message = handle_message(self.service, type_msg, file, db_file)
                messages.append(message)
            self.state = set_state()
        return messages
