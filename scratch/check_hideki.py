import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

print("--- Log entries for Hideki Suekawa ---")
cursor.execute("SELECT * FROM logs WHERE client_name LIKE '%Hideki%' OR client_phone LIKE '%5511989959672%'")
for row in cursor.fetchall():
    print(row)

print("\n--- Last log for Campaign 10 ---")
cursor.execute("SELECT last_log FROM campaigns WHERE id = 10")
print(cursor.fetchone()[0])

conn.close()
