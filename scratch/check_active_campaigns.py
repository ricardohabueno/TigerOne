import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name, is_active, include_schedule_fields FROM campaigns")
for row in cursor.fetchall():
    print(row)

conn.close()
