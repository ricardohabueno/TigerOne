import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

cursor.execute("SELECT last_log FROM campaigns WHERE id = 10")
last_log = cursor.fetchone()[0]
print("\n=== Last Log of Campaign 10 ===")
print(last_log)

conn.close()
