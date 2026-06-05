import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

print("--- CAMPAIGNS ---")
cursor.execute("SELECT id, name, test_name, test_phone, test_date, test_time, include_schedule_fields FROM campaigns")
for row in cursor.fetchall():
    print(row)

print("\n--- SETTINGS ---")
cursor.execute("SELECT * FROM settings")
for row in cursor.fetchall():
    print(row)

print("\n--- LOGS ---")
cursor.execute("SELECT id, campaign_id, client_name, client_phone, appointment_date, status, error_message FROM logs ORDER BY id DESC LIMIT 10")
for row in cursor.fetchall():
    print(row)

conn.close()
