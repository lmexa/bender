import os.path
import pickle
import sqlite3

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from bender.sql_utils import set_state, make_files_dict, insert_to_files_table
from bender.drive_utils import get_files_list, handle_message, return_new_tree


class DriveUpdater:
    def __init__(self, config):
        self.scopes = config.scopes
        self.credentials = config.credentials
        self.token_file = config.token_file
        self.service = self.build_service()
        self.state = set_state()
        # need to insert full tree
        if config.reset_state or not self.state:
            new_files = return_new_tree(self.service)
            for id, file in new_files.items():
                name = file.get('name')
                parents = file.get('parents')
                if parents:
                    parent_id = parents[0]
                else:
                    parent_id = ''
                web_view_link = file.get('webViewLink')
                web_content_link = file.get('webContentLink')
                created_time = file.get('createdTime')
                modified_time = file.get('modifiedTime')
                last_user = file.get('lastModifyingUser').get('emailAddress') if file.get('lastModifyingUser') else 'Somebody'
                full_path = file.get('full_path')
                insert_to_files_table(id, name, parent_id, full_path, web_content_link,
                                      web_view_link, created_time, modified_time, False, last_user)
                self.state = set_state()

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
        query = "SELECT id, name, parent_id, full_path FROM files WHERE trashed=0 "
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
