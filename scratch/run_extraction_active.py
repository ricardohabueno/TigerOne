import os
import sys

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend.models import Campaign
from backend.jobs.scheduler import run_campaigns
import sqlite3

db = SessionLocal()
try:
    print("Activating Campaign 10...")
    campaign = db.query(Campaign).filter(Campaign.id == 10).first()
    original_active = campaign.is_active
    campaign.is_active = True
    db.commit()
    
    print("Running run_campaigns(is_dry_run=True) synchronously...")
    run_campaigns(is_dry_run=True)
    print("Done run_campaigns.")
    
    # Restore original active status
    campaign.is_active = original_active
    db.commit()
    
    # Check campaign 10 last log
    conn = sqlite3.connect('tigerone.db')
    cursor = conn.cursor()
    cursor.execute("SELECT last_log FROM campaigns WHERE id = 10")
    print("\n=== Campaign 10 last_log in DB after execution ===")
    print(cursor.fetchone()[0])
    conn.close()
    
finally:
    db.close()
