import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*), COUNT(appointment_date) FROM logs")
print("Total logs, logs with appointment_date:", cursor.fetchone())

cursor.execute("SELECT id, campaign_id, client_name, appointment_date, status, created_at FROM logs WHERE appointment_date IS NOT NULL ORDER BY id DESC LIMIT 10")
rows = cursor.fetchall()
print(f"Logs with appointment_date (count={len(rows)}):")
for r in rows:
    print(r)

conn.close()
