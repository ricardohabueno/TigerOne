import os
import sys
import sqlite3
from datetime import datetime

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend.models import Campaign, Settings
from backend.extractor.avec_client import AvecClient
from backend.engine.normalizer import Normalizer

def main():
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == 10).first()
        settings = db.query(Settings).first()
        
        print(f"Campaign: {campaign.name}")
        avec_client = AvecClient(settings.avec_username, settings.avec_password)
        
        # Simula datas de busca (Hoje até Hoje + 30)
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
        
        print("Fetching report data from Avec...")
        aadata = avec_client.fetch_report(visual_url, api_url, start_date, end_date)
        print(f"Fetched {len(aadata)} rows.")
        
        normalized_clients = Normalizer.process_report_data(
            aadata,
            include_schedule_fields=campaign.include_schedule_fields
        )
        
        print(f"Normalized {len(normalized_clients)} clients.")
        
        now = datetime.now()
        print(f"Horário atual de referência: {now.strftime('%d/%m/%Y %H:%M')}")
        
        skipped_past = 0
        future_valid = 0
        
        for idx, client in enumerate(normalized_clients):
            raw_date = client.get("avecreserva", "")
            raw_time = client.get("avechorario", "")
            data_reserva = Normalizer.normalize_date_str(raw_date)
            hora_reserva = Normalizer.normalize_time_str(raw_time)
            
            if data_reserva and hora_reserva:
                try:
                    dt = datetime.strptime(f"{data_reserva} {hora_reserva}", "%d/%m/%Y %H:%M")
                    is_past = dt < now
                    if is_past:
                        skipped_past += 1
                        if skipped_past <= 5:
                            print(f"[PAST] Cliente: {client['nome']}, Reserva: {data_reserva} {hora_reserva} (PULARIA)")
                    else:
                        future_valid += 1
                        if future_valid <= 5:
                            print(f"[FUTURE] Cliente: {client['nome']}, Reserva: {data_reserva} {hora_reserva} (ENVIARIA)")
                except Exception as e:
                    print(f"Erro parser: {e}")
                    
        print(f"\nResumo da Simulação:")
        print(f"  Total no Passado (serão ignorados): {skipped_past}")
        print(f"  Total no Futuro (serão processados): {future_valid}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
