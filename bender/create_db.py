import sqlite3

conn = sqlite3.connect("mediabuy.db")
cursor = conn.cursor()

# Create files table
cursor.execute("""CREATE TABLE files
                  (id,name,parent_id,full_path,webContentLink,webViewLink,created,modified,trashed,email)
               """)

# Сreate users table
cursor.execute("""CREATE TABLE users
                  (email,telegram_nick,paths,chat_id)
               """)
