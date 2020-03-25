import sqlite3

conn = sqlite3.connect("mediabuy.db")
cursor = conn.cursor()

# Создание таблицы
cursor.execute("""SELECT * from files;
               """)
for row in cursor.fetchall():
    print(row)
#print(cursor.fetchall())
