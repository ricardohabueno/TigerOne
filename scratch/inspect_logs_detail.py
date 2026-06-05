import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

# Get details of campaign 10 in logs
cursor.execute("SELECT id, campaign_id, client_name, client_phone, appointment_date, status, created_at FROM logs WHERE campaign_id = 10 ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()
print("Campaign 10 Logs:")
for r in rows:
    print(r)

# Get the count of logs for campaign 10 where appointment_date is null vs not null
cursor.execute("SELECT COUNT(*), COUNT(appointment_date) FROM logs WHERE campaign_id = 10")
print("Total logs for campaign 10, with appointment_date:", cursor.fetchone())

conn.close()
