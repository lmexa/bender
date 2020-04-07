from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from bender.sql_utils import insert_to_users_table, select_ids_from_user_table, update_users_table, \
    select_folders_from_files_table, select_folders_from_users_table, delete_user_sql, is_path_child, select_view_link
from bender.config import ConfigBender
from bender.updater import DriveUpdater
from bender.messages import GREETINGS, SUCCESS_REGISTRATION, HAVE_ID_IN_BASE, HELP, INSERT_EMAIL, NOT_EMAIL,\
    make_text_from_message, make_text_from_grouped_message
from _collections import defaultdict
import logging

logger = logging.getLogger('bender')
logging.captureWarnings(True)

EMAIL, ADD_FOLDERS, REMOVE_FOLDERS, ADD_NEW_FOLDERS = range(4)


def greet_user(update, context):
    chat_id = update.effective_chat.id
    known_chats, _ = select_ids_from_user_table()
    if chat_id not in known_chats:
        logger.info(f'Start greeting user {chat_id}')
        context.bot.send_message(chat_id=chat_id, text=GREETINGS)
    else:
        context.bot.send_message(chat_id=chat_id, text=HAVE_ID_IN_BASE)


def registration(update, context):
    chat_id = update.effective_chat.id
    known_chats, _ = select_ids_from_user_table()
    if chat_id not in known_chats:
        context.bot.send_message(chat_id=chat_id, text=INSERT_EMAIL)
    else:
        context.bot.send_message(chat_id=chat_id, text=HAVE_ID_IN_BASE)
    return EMAIL


def handle_user_email(update, context):
    chat_id = update.effective_chat.id
    known_chats, _ = select_ids_from_user_table()
    user_text = update.message.text
    text = user_text.lower().strip()
    if chat_id not in known_chats:
        if '@' in text:
            logger.info(f'Inserting users info: {chat_id}..')
            telegram_nick = update.message.from_user.username
            folders = select_folders_from_files_table()
            folders_text = '\n'.join(folders)
            paths = ''
            insert_to_users_table(text, telegram_nick, paths, chat_id)
            context.bot.send_message(chat_id=chat_id, text=SUCCESS_REGISTRATION + '\n' + folders_text)
            return ADD_FOLDERS
        else:
            context.bot.send_message(chat_id=chat_id, text=NOT_EMAIL)
            return EMAIL
    else:
        context.bot.send_message(chat_id=chat_id, text=HAVE_ID_IN_BASE)
        return ConversationHandler.END


def add_user_folders(update, context):
    chat_id = update.effective_chat.id
    user_folders = select_folders_from_users_table(chat_id).split(',')
    all_folders = select_folders_from_files_table()
    folders_to_choose = set(all_folders).difference(set(user_folders))
    filtered_folders_to_choose = list(filter(lambda x: len(x.split('/')) <= 2, folders_to_choose))
    folders_text = '\n'.join(filtered_folders_to_choose)
    context.bot.send_message(chat_id=chat_id,
                             text='Запиши новые папки, за которыми хотите следить, через запятую:\n' + folders_text)
    return ADD_NEW_FOLDERS


def handle_user_folder(update, context):
    chat_id = update.effective_chat.id
    known_chats, _ = select_ids_from_user_table()
    user_text = update.message.text
    paths_text = user_text.lower().strip()
    paths = list(map(lambda x: x.strip(), paths_text.split(',')))
    clean_paths = ','.join(paths)
    if chat_id not in known_chats:
        logger.info(f'Inserting folders {clean_paths} of new user: {chat_id}..')
        update_users_table(clean_paths, chat_id)
    else:
        user_folders = select_folders_from_users_table(chat_id).split(',')
        total_folders = set(paths).union(set(user_folders))
        add_folders = ','.join(total_folders)
        logger.info(f'Updating folders {clean_paths} of user: {chat_id}..')
        update_users_table(add_folders, chat_id)
    context.bot.send_message(chat_id=chat_id, text='Папки добавлены!')
    return ConversationHandler.END


def remove_user_folders(update, context):
    chat_id = update.effective_chat.id
    folders = select_folders_from_users_table(chat_id).split(',')
    folders_text = '\n'.join(folders)
    context.bot.send_message(chat_id=chat_id,
                             text='Запиши папки, за которыми больше не хотите следить, через запятую:\n' + folders_text)
    return REMOVE_FOLDERS


def handle_removing_folders(update, context):
    chat_id = update.effective_chat.id
    folders = select_folders_from_users_table(chat_id).split(',')
    user_text = update.message.text
    folders_remove = user_text.lower().strip().split(',')
    folders_remove = list(map(lambda x: x.strip(), folders_remove))
    paths = ','.join(set(folders).difference(set(folders_remove)))
    update_users_table(paths, chat_id)
    context.bot.send_message(chat_id=chat_id, text='Папки удалены!')
    return ConversationHandler.END


def delete_user(update, context):
    chat_id = update.effective_chat.id
    delete_user_sql(chat_id)
    context.bot.send_message(chat_id=chat_id, text='Вы удалены! Больше сообщений не будет')


def show_folders(update, context):
    chat_id = update.effective_chat.id
    folders_text = select_folders_from_users_table(chat_id)
    if folders_text:
        folders = folders_text.split(',')
        folders_text = '\n'.join(folders)
        text = 'Ваши папки:\n' + folders_text
    else:
        text = 'Я не нашел у вас отслеживаемых папок!'
    context.bot.send_message(chat_id=chat_id, text=text)


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Действие отменено!')
    return ConversationHandler.END


def show_help(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text=HELP)


def process_message(message, user_id, user_folders_text):
    user_folders = user_folders_text.split(',')
    new_path = message.get('new_path')
    old_path = message.get('old_path')
    # path of file changed
    if old_path and new_path != old_path:
        # need to change folder name in users table
        new_folders = []
        for user_folder in user_folders:
            if is_path_child(old_path, user_folder):
                length = len(user_folder.split('/'))
                new_folder = '/'.join(new_path.split('/')[:length])
                if new_folder != user_folder:
                    new_folders.append(new_folder)
                    need_update = True
                else:
                    new_folders.append(user_folder)
            else:
                new_folders.append(user_folder)
        if need_update:
            update_users_table(','.join(new_folders), user_id)
            update_path = old_path
    else:
        update_path = new_path
    for user_folder in user_folders:
        if is_path_child(update_path, user_folder):
            return message


def send_push(context):
    drive_object = context.job.context
    logger.info(f'Updating info...')
    messages = drive_object.get_messages()
    logger.info(f'Messages updated!') if messages else logger.info(f'No Changes in Drive!')
    known_chats, known_paths = select_ids_from_user_table()
    for user_id, user_folders_text in zip(known_chats, known_paths):
        grouped_message = defaultdict(dict)
        texts = []
        for message in messages:
            pushed_message = process_message(message, user_id, user_folders_text)
            if pushed_message:
                text = make_text_from_message(pushed_message)
                texts.append(text)
                update_path = '/'.join(message.get('new_path').split('/')[:-1])
                view_link = select_view_link(update_path)
                view_link = view_link[0] if view_link else ''
                msg_type = message.get('type')
                grouped_message[update_path]['view_link'] = view_link
                if grouped_message[update_path].get(msg_type) is not None:
                    grouped_message[update_path][msg_type] += 1
                else:
                    grouped_message[update_path][msg_type] = 0
        if len(texts) >= 3:
            text = make_text_from_grouped_message(grouped_message)
            logger.info(f'Sending grouped message: {text} to {user_id}')
            context.bot.send_message(chat_id=str(user_id), text=text)
        else:
            for text in texts:
                logger.info(f'Sending message: {text} to {user_id}')
                context.bot.send_message(chat_id=str(user_id), text=text)


def main():
    config = ConfigBender.load('bender/config.yaml')
    logging.basicConfig(**config.log.to_dict())
    drive = DriveUpdater(config)
    bender_bot = Updater(token=config.token, request_kwargs=config.proxy, use_context=True)
    j = bender_bot.job_queue
    job_message = j.run_repeating(send_push, interval=config.job_interval, first=0, context=drive)
    conv_handler_register = ConversationHandler(
        entry_points=[CommandHandler('registration', registration)],
        states={
            EMAIL: [MessageHandler(Filters.text, handle_user_email)],
            ADD_FOLDERS: [MessageHandler(Filters.text, handle_user_folder)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=100
    )
    conv_handler_remove = ConversationHandler(
        entry_points=[CommandHandler('remove', remove_user_folders)],
        states={
            REMOVE_FOLDERS: [MessageHandler(Filters.text, handle_removing_folders)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=100
    )
    conv_handler_add = ConversationHandler(
        entry_points=[CommandHandler('add', add_user_folders)],
        states={
            ADD_NEW_FOLDERS: [MessageHandler(Filters.text, handle_user_folder)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=100
    )
    dp = bender_bot.dispatcher
    dp.add_handler(CommandHandler('start', greet_user))
    dp.add_handler(conv_handler_register)
    dp.add_handler(conv_handler_remove)
    dp.add_handler(conv_handler_add)
    dp.add_handler(CommandHandler('delete', delete_user))
    dp.add_handler(CommandHandler('folders', show_folders))
    dp.add_handler(CommandHandler('help', show_help))
    bender_bot.start_polling()
    bender_bot.idle()


if __name__ == '__main__':
    main()
