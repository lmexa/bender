import sqlite3
import datetime


def get_iso_datetime():
    d = datetime.datetime.utcnow()
    return d.isoformat("T") + "Z"


def set_state():
    conn = sqlite3.connect("bender/mediabuy.db")
    cursor = conn.cursor()
    query = "SELECT MAX(modified) FROM files"
    cursor.execute(query)
    result = cursor.fetchone()
    if result[0] is None:
        return '2012-01-04T12:00:00-08:00'
    else:
        return result[0]


def update_files_table(name, parent_id, full_path, web_content_link, web_view_link, created, modified, trashed, email, id):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = '''UPDATE files
            SET name = ? ,
            parent_id = ? ,
            full_path = ? ,
            webContentLink = ? ,
            webViewLink = ? ,
            created = ? ,
            modified = ? ,
            trashed = ? ,
            email = ?
            WHERE id = ?'''
    cursor = conn.cursor()
    task = (name, parent_id, full_path, web_content_link, web_view_link, created, modified, trashed, email, id)
    cursor.execute(sql, task)
    conn.commit()


def update_tree(full_path, id):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = '''UPDATE files
                SET full_path = ?
                WHERE id = ?'''
    cursor = conn.cursor()
    task = (full_path, id)
    cursor.execute(sql, task)
    conn.commit()


def insert_to_files_table(id, name, parent_id, full_path, web_content_link,
                          web_view_link, created, modified, trashed, email):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = '''INSERT INTO files(id,name,parent_id,full_path,webContentLink,webViewLink,created,modified,trashed,email)
                VALUES(?,?,?,?,?,?,?,?,?,?)'''
    cursor = conn.cursor()
    task = (id, name, parent_id, full_path, web_content_link, web_view_link, created, modified, trashed, email)
    cursor.execute(sql, task)
    conn.commit()


def get_folders_from_paths(paths):
    folders = []
    for path in paths:
        # костыль для определения директорий :(
        if len(path.split('/')[-1].split('.')) <= 2 and len(path.split('/')[-1].split('.')[-1]) != 3:
            folders.append(path)
    return folders


def select_folders_from_files_table():
    conn = sqlite3.connect("bender/mediabuy.db")
    cursor = conn.cursor()
    cursor.execute('SELECT full_path from files WHERE trashed=0;')
    all_paths = [x[0] for x in cursor.fetchall()]
    conn.commit()
    folders = get_folders_from_paths(all_paths)
    return folders


def select_folders_from_users_table(chat_id):
    conn = sqlite3.connect("bender/mediabuy.db")
    cursor = conn.cursor()
    cursor.execute('SELECT paths from users WHERE chat_id=?;', (chat_id,))
    paths = cursor.fetchone()
    paths_text = paths[0] if paths else ''
    return paths_text


def insert_to_users_table(email, telegram_nick, paths, chat_id):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = '''INSERT INTO users (email,telegram_nick,paths,chat_id)
                    VALUES(?,?,?,?)'''
    cursor = conn.cursor()
    task = (email, telegram_nick, paths, chat_id)
    cursor.execute(sql, task)
    conn.commit()


def update_users_table(paths, chat_id):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = '''UPDATE users
            SET paths = ?
            WHERE chat_id = ?'''
    cursor = conn.cursor()
    task = (paths, chat_id)
    cursor.execute(sql, task)
    conn.commit()


def delete_user_sql(chat_id):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = ''' DELETE FROM users WHERE chat_id = ?;
    '''
    cursor = conn.cursor()
    task = (chat_id,)
    cursor.execute(sql, task)
    conn.commit()


def select_ids_from_user_table():
    conn = sqlite3.connect("bender/mediabuy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, paths from users;")
    rows = cursor.fetchall()
    known_ids = [row[0] for row in rows]
    known_paths = [row[1] for row in rows]
    return known_ids, known_paths


def select_file_path_by_id(id):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = ''' SELECT full_path from files WHERE id = ?;
    '''
    cursor = conn.cursor()
    task = (id,)
    cursor.execute(sql, task)
    path = cursor.fetchone()
    return path


def select_view_link(full_path):
    conn = sqlite3.connect("bender/mediabuy.db")
    sql = ''' SELECT webViewLink from files WHERE full_path = ?;
        '''
    cursor = conn.cursor()
    task = (full_path,)
    cursor.execute(sql, task)
    link = cursor.fetchone()
    return link


def make_files_dict(files):
    total_dict = {}
    for file in files:
        file_dict = {}
        id = file[0]
        file_dict['name'] = file[1]
        file_dict['parent_id'] = file[2]
        file_dict['full_path'] = file[3]
        total_dict[id] = file_dict
    return total_dict


def is_path_child(path, dir):
    splitted_path = path.split('/')
    splitted_dir = dir.split('/')
    if splitted_path[:len(splitted_dir)] == splitted_dir:
        return True
    else:
        return False
