import requests
import time
import sqlite3

print("Triggering Dry Run via API /api/fetch-data...")
res = requests.post("http://localhost:8000/api/fetch-data")
if res.status_code == 200:
    print("Success: Extraction started.")
else:
    print(f"Error: {res.status_code} - {res.text}")
    exit(1)

# Playwright login and fetch takes around 30-40 seconds
print("Waiting 45 seconds for extraction to complete...")
time.sleep(45)

conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()

# Check last log for Campaign 10
cursor.execute("SELECT last_log FROM campaigns WHERE id = 10")
last_log = cursor.fetchone()[0]
print("\n=== Last Log of Campaign 10 ===")
print(last_log)

# Check if any new logs were created in the database (Dry run should NOT insert anything in the log table)
cursor.execute("SELECT COUNT(*) FROM logs")
log_count = cursor.fetchone()[0]
print(f"\nTotal logs in DB (should be 245): {log_count}")

conn.close()
