import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name, last_log FROM campaigns")
for row in cursor.fetchall():
    print(f"=== Campaign {row[0]}: {row[1]} ===")
    print(row[2])
    print("\n")

conn.close()
