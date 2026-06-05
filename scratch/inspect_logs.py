import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

cursor.execute("SELECT id, campaign_id, client_name, appointment_date, created_at FROM logs ORDER BY id DESC LIMIT 15")
for row in cursor.fetchall():
    print(row)

conn.close()
