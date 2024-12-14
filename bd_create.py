import sqlite3

# Создаем базу данных и таблицу
conn = sqlite3.connect('school_data.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    grade TEXT
)
''')

conn.commit()
conn.close()
