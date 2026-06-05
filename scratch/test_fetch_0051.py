import os
import sys

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.extractor.avec_client import AvecClient
from backend.engine.normalizer import Normalizer
import sqlite3

# Busca credenciais e URL
conn = sqlite3.connect('tigerone.db')
cursor = conn.cursor()
cursor.execute("SELECT avec_username, avec_password, avec_salon_id FROM settings WHERE id = 1")
creds = cursor.fetchone()
cursor.execute("SELECT avec_report_url FROM campaigns WHERE id = 10")
report_url = cursor.fetchone()[0]
conn.close()

username, password, salon_id = creds
print(f"Username: {username}, Salon ID: {salon_id}, Report URL: {report_url}")

client = AvecClient(username, password)

# Monta URL visual e API
raw_url = report_url
if "/admin/relatorio/" in raw_url and "listar?" not in raw_url:
    relatorio_id = raw_url.rstrip("/").split("/")[-1]
    visual_url = raw_url
    api_url = f"https://admin.avec.beauty/admin/relatorios/listar?relatorio={relatorio_id}&salao={salon_id}"
    if relatorio_id == "0051":
        api_url += "&site=&profissional_id="
else:
    import re
    m = re.search(r'relatorio=(\w+)', raw_url)
    relatorio_id = m.group(1) if m else ""
    visual_url = f"https://admin.avec.beauty/admin/relatorio/{relatorio_id}"
    api_url = raw_url

# Roda extração para hoje até daqui a 30 dias
from datetime import datetime, timedelta
start_date = datetime.now().strftime("%d/%m/%Y")
end_date = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

print(f"Fetching report from {start_date} to {end_date}...")
aadata = client.fetch_report(visual_url, api_url, start_date, end_date)

print(f"Total rows fetched: {len(aadata)}")
if len(aadata) > 0:
    print("First 3 raw rows:")
    for i in range(min(3, len(aadata))):
        print(f"Row {i}: {aadata[i]}")
        
    print("\nNormalization test on first 3 rows:")
    for i in range(min(3, len(aadata))):
        norm = Normalizer.normalize_aadata(aadata[i], include_schedule_fields=True)
        print(f"Row {i} normalized: {norm}")
else:
    print("No rows returned.")
