import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(logs)")
columns = cursor.fetchall()
print("Logs columns:")
for col in columns:
    print(col)

cursor.execute("PRAGMA table_info(campaigns)")
columns = cursor.fetchall()
print("\nCampaigns columns:")
for col in columns:
    print(col)

conn.close()
