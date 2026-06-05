import os
import sys

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend.models import Campaign, Settings, Log
from backend.extractor.avec_client import AvecClient
from backend.engine.normalizer import Normalizer
from datetime import datetime, timedelta
import re

db = SessionLocal()
try:
    campaign = db.query(Campaign).filter(Campaign.id == 10).first()
    settings = db.query(Settings).first()
    
    print(f"Campaign: {campaign.name}")
    print(f"include_schedule_fields: {campaign.include_schedule_fields}")
    print(f"test_date: {campaign.test_date}")
    print(f"test_time: {campaign.test_time}")
    
    avec_client = AvecClient(settings.avec_username, settings.avec_password)
    
    target_date = datetime.now() + timedelta(days=campaign.extraction_offset_days)
    start_date = target_date.strftime("%d/%m/%Y")
    end_target_date = datetime.now() + timedelta(days=campaign.extraction_end_offset_days)
    end_date = end_target_date.strftime("%d/%m/%Y")
    
    raw_url = campaign.avec_report_url
    salon_id = settings.avec_salon_id or "4053"
    
    if "/admin/relatorio/" in raw_url and "listar?" not in raw_url:
        relatorio_id = raw_url.rstrip("/").split("/")[-1]
        visual_url = raw_url
        api_url = f"https://admin.avec.beauty/admin/relatorios/listar?relatorio={relatorio_id}&salao={salon_id}"
        if relatorio_id == "0051":
            api_url += "&site=&profissional_id="
            
    print(f"Fetching report between {start_date} and {end_date}...")
    aadata = avec_client.fetch_report(visual_url, api_url, start_date, end_date)
    print(f"Rows fetched: {len(aadata)}")
    
    normalized_clients = Normalizer.process_report_data(
        aadata,
        include_schedule_fields=campaign.include_schedule_fields
    )
    
    print(f"Normalized clients: {len(normalized_clients)}")
    
    # Check first 5 clients
    for idx, client in enumerate(normalized_clients[:5]):
        print(f"\nClient {idx}:")
        print(f"  Raw client: {client}")
        
        telefone_real = client["telefone"]
        data_reserva_check = client.get("avecreserva", "") if campaign.include_schedule_fields else None
        print(f"  data_reserva_check: {data_reserva_check}")
        
        # Override de teste
        nome_completo = campaign.test_name if campaign.test_name else client["nome"]
        nome_final = nome_completo.split()[0] if nome_completo else ""
        telefone_final = campaign.test_phone if campaign.test_phone else telefone_real
        
        payload = {
            "nome": nome_final,
            "telefone": telefone_final
        }
        
        if campaign.include_schedule_fields:
            raw_date = campaign.test_date if campaign.test_date else client.get("avecreserva", "")
            raw_time = campaign.test_time if campaign.test_time else client.get("avechorario", "")
            
            data_reserva = Normalizer.normalize_date_str(raw_date)
            hora_reserva = Normalizer.normalize_time_str(raw_time)
            
            payload["avecreserva"] = data_reserva
            payload["avechorario"] = hora_reserva
            
        print(f"  Payload to send: {payload}")

finally:
    db.close()
