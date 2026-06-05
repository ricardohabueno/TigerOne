import sqlite3

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name, avec_report_url, extraction_offset_days, extraction_end_offset_days FROM campaigns WHERE ID IN (5, 6, 7, 8, 9)")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, URL: {row[2]}, Offset: {row[3]}, EndOffset: {row[4]}")

conn.close()
