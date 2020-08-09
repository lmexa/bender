from bender.sql import select_nick_by_email


GREETINGS = """
Привет! Я бот, помогающий следить за обновлениями (создание нового файла, изменение и удаление) на google-drive. 
Список моих команд:
/help - вывести список команд
/registration - зарегистрироваться пользователем бота
/add - добавить папки для отслеживания
/remove - убрать папки из отслеживаемых
/folders - показать отслеживаемые папки
/delete - удалить себя из пользователей бота
"""

INSERT_EMAIL = """
Введи свой аккаунт mail в формате 'name@gmail.com'
"""

SUCCESS_REGISTRATION = """
Отлично!
А теперь выбери папки, за которыми будешь следить. Запиши их через запятую:
"""

NOT_EMAIL = """
Это не похоже на email. Попробуй еще раз
"""

HAVE_ID_IN_BASE = """
Я тебя уже знаю! Жди сообщений
"""

HELP = """
Список моих команд:
/help - вывести список команд
/registration - зарегистрироваться пользователем бота
/add - добавить папки для отслеживания
/remove - убрать папки из отслеживаемых
/folders - показать отслеживаемые папки
/delete - удалить себя из пользователей бота
"""

DUMB_ANSWER = """ Я вас не понимаю :( \n
"""


def make_text_from_message(message):
    email = message.get('email')
    nick = select_nick_by_email(email)
    type_msg = message.get('type')
    name = message.get('name')
    old_path = message.get('old_path')
    new_path = message.get('new_path')
    link = message.get('web_view_link')
    text = f'File {name} has been {type_msg} by {email} {"@"+nick if nick else ""}\n'
    text += f'New path: {new_path}\nOld path: {old_path}\n'
    text += f'View link: {link}'
    return text


def make_text_from_grouped_message(grouped_message):
    text = ''
    for folder, updates in grouped_message.items():
        for update_type, count in updates.items():
            if update_type != 'view_link':
                text += f'In {folder} {count} files has been {update_type}\n'
        text += f'See changes by link: {updates.get("view_link")}\n\n'
    return text


def make_pretty_folders_list(folders, depth_limit):
    filtered_folders = []
    for folder in folders:
        if len(folder.split('/')) <= depth_limit:
            filtered_folders.append(folder)
    return sorted(filtered_folders)
