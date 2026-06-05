import os
import sys
import sqlite3
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import SessionLocal
from backend.models import Campaign, Settings
from backend.extractor.avec_client import AvecClient
from backend.engine.normalizer import Normalizer

def main():
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == 10).first()
    settings = db.query(Settings).first()
    db.close()
    
    avec_client = AvecClient(settings.avec_username, settings.avec_password)
    
    from datetime import timedelta
    target_date = datetime.now()
    start_date = target_date.strftime("%d/%m/%Y")
    end_target_date = datetime.now() + timedelta(days=30)
    end_date = end_target_date.strftime("%d/%m/%Y")
    
    raw_url = campaign.avec_report_url
    salon_id = settings.avec_salon_id or "4053"
    relatorio_id = raw_url.rstrip("/").split("/")[-1]
    visual_url = raw_url
    api_url = f"https://admin.avec.beauty/admin/relatorios/listar?relatorio={relatorio_id}&salao={salon_id}&site=&profissional_id="
    
    aadata = avec_client.fetch_report(visual_url, api_url, start_date, end_date)
    normalized_clients = Normalizer.process_report_data(
        aadata,
        include_schedule_fields=campaign.include_schedule_fields
    )
    
    # Deduplicação
    unique_clients = []
    seen_keys = set()
    for c in normalized_clients:
        phone = c["telefone"]
        date = c.get("avecreserva", "")
        key = f"{phone}_{date}"
        if key not in seen_keys:
            seen_keys.add(key)
            unique_clients.append(c)
            
    print(f"\n--- Analisando {len(unique_clients)} registros únicos ---")
    now = datetime.now()
    print(f"Momento atual do servidor: {now.strftime('%d/%m/%Y %H:%M')}")
    
    for client in unique_clients:
        if "Hideki" in client["nome"]:
            print(f"\n[HIDEKI ENCONTRADO NO BANCO DE DADOS EXTRAÍDOS]")
            print(f"Dados: {client}")
            raw_date = client.get("avecreserva", "")
            raw_time = client.get("avechorario", "")
            data_reserva = Normalizer.normalize_date_str(raw_date)
            hora_reserva = Normalizer.normalize_time_str(raw_time)
            dt = datetime.strptime(f"{data_reserva} {hora_reserva}", "%d/%m/%Y %H:%M")
            print(f"Data parsed: {dt}")
            print(f"dt < now: {dt < now}")
            
if __name__ == "__main__":
    main()
