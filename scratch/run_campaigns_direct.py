import os
import sys

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.jobs.scheduler import run_campaigns
import sqlite3

print("Running run_campaigns(is_dry_run=True)...")
try:
    run_campaigns(is_dry_run=True)
    print("Done executing run_campaigns.")
    
    # Print campaign 10 last log
    conn = sqlite3.connect('tigerone.db')
    cursor = conn.cursor()
    cursor.execute("SELECT last_log FROM campaigns WHERE id = 10")
    print("\n=== Campaign 10 last_log in DB after execution ===")
    print(cursor.fetchone()[0])
    conn.close()
except Exception as e:
    import traceback
    traceback.print_exc()
