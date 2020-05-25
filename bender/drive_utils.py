import logging
import time
from googleapiclient.errors import HttpError
from bender.sql_utils import update_files_table, update_tree, insert_to_files_table, \
    get_iso_datetime, select_file_path_by_id

logger = logging.getLogger(__name__)


def get_files_list(service, query, fields):
    # Return information about all files in user's Drive.
    files = []
    page_token = None
    while True:
        try:
            response = service.files().list(q=query,
                                            spaces='drive',
                                            fields=fields,
                                            pageToken=page_token).execute()
            for file in response.get('files', []):
                files.append(file)
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        except HttpError as e:
            logger.error(e)
            time.sleep(2)
    return files


def get_folder_tree(service, folder, root, total_dict):
    if root != '':
        root += '/' + folder.get('name')
    else:
        root += folder.get('name')
    folder.update({'full_path': root.lower().strip()})
    total_dict[folder.get('id')] = folder
    id = folder.get('id')
    q = f"'{id}' in parents and trashed=false"
    fields = "nextPageToken, files(id, name, parents, trashed, webViewLink, webContentLink, createdTime, " \
             "modifiedTime, lastModifyingUser) "
    files = get_files_list(service, q, fields)
    for file in files:
        get_folder_tree(service, file, root, total_dict)


def return_new_tree(service):
    # Return tree for specific drive
    parsed_dict = {}  # dict of files
    q = f'trashed=false'
    fields = "nextPageToken, files(id, name, parents, trashed, webViewLink, webContentLink, createdTime, " \
             "modifiedTime, lastModifyingUser) "
    files = get_files_list(service, q, fields)
    for file in files:
        if not file.get('parents'):
            root = ''
            file.update({'full_path': root.lower().strip()})
            parsed_dict[file.get('id')] = file
            get_folder_tree(service, file, root, parsed_dict)
    return parsed_dict


def handle_message(service, type_msg, file, db_file):
    message = {}
    id = file.get('id')
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
    last_user = file.get('lastModifyingUser').get('emailAddress')

    message['type'] = type_msg
    message['name'] = name
    if db_file:
        message['old_path'] = db_file.get('full_path')
    message['web_view_link'] = web_view_link

    if type_msg == 'trashed':
        message['new_path'] = db_file.get('full_path')
        message['email'] = 'Somebody'
        modified_time = get_iso_datetime()
        update_files_table(name, parent_id, db_file.get('full_path'),
                           web_content_link, web_view_link,
                           created_time, modified_time, True, 'Somebody', id)
    elif type_msg in ('created', 'updated'):
        message['email'] = last_user
        if type_msg == 'created':
            parent_path = select_file_path_by_id(parent_id)
            if parent_path:
                new_path = parent_path[0] + '/' + name
            else:
                # need to retrieve folders tree
                new_tree = return_new_tree(service)
                new_path = new_tree.get(id)
            new_path = new_path.lower().strip()
            message['new_path'] = new_path
            insert_to_files_table(id, name, parent_id, new_path, web_content_link,
                                  web_view_link, created_time, modified_time, False, last_user)
        else:
            new_tree = return_new_tree(service)
            new_path = new_tree.get(id).get('full_path')
            update_files_table(name, parent_id, new_path,
                               web_content_link, web_view_link,
                               created_time, modified_time, False, last_user, id)
            message['new_path'] = new_path
            for id, file in new_tree.items():
                update_tree(file.get('full_path'), id)
    return message
