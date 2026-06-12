from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import re
import threading

from backend import models
from backend.database import engine, get_db
from backend.jobs.scheduler import start_scheduler, run_campaigns
from backend.engine.webhook import WebhookSender

models.Base.metadata.create_all(bind=engine)

# Database migrations for new columns
def run_migrations():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    try:
        columns = [col['name'] for col in inspector.get_columns('logs')]
        with engine.begin() as conn:
            if 'conversion_status' not in columns:
                conn.execute(text("ALTER TABLE logs ADD COLUMN conversion_status VARCHAR DEFAULT 'PENDING'"))
            if 'converted_at' not in columns:
                conn.execute(text("ALTER TABLE logs ADD COLUMN converted_at DATETIME"))
            if 'conversion_appointment_date' not in columns:
                conn.execute(text("ALTER TABLE logs ADD COLUMN conversion_appointment_date VARCHAR"))
            if 'conversion_value' not in columns:
                conn.execute(text("ALTER TABLE logs ADD COLUMN conversion_value FLOAT"))
            print("Database migrations applied successfully.")
    except Exception as e:
        print(f"Error checking or running database migrations: {e}")

run_migrations()

app = FastAPI(title="TigerOne Campanhas Inteligentes API")

@app.on_event("startup")
def startup_event():
    start_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class CampaignTestPayload(BaseModel):
    nome: str
    telefone: str
    avecreserva: str = None
    avechorario: str = None

class CampaignToggle(BaseModel):
    is_active: bool

class CampaignConfig(BaseModel):
    wizebot_webhook_url: str
    avec_report_url: str

class TestDataUpdate(BaseModel):
    test_name: str
    test_phone: str
    test_date: str = None
    test_time: str = None

class SettingsUpdate(BaseModel):
    avec_username: str
    avec_password: str
    avec_salon_id: str

# API Endpoints
@app.get("/api/campaigns")
def get_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(models.Campaign).all()
    result = []
    for c in campaigns:
        # Campanhas elegíveis para conversão
        track_conversions = c.id in (1, 5, 6, 7, 8, 9)
        
        sent_count = db.query(models.Log).filter(
            models.Log.campaign_id == c.id,
            models.Log.status == "SUCCESS"
        ).count()
        
        converted_count = db.query(models.Log).filter(
            models.Log.campaign_id == c.id,
            models.Log.conversion_status == "CONVERTED"
        ).count()
        
        conversion_rate = round((converted_count / sent_count * 100), 1) if sent_count > 0 else 0.0
        
        from sqlalchemy import func
        revenue_recovered = db.query(func.sum(models.Log.conversion_value)).filter(
            models.Log.campaign_id == c.id,
            models.Log.conversion_status == "CONVERTED"
        ).scalar() or 0.0
        
        c_dict = {
            "id": c.id,
            "name": c.name,
            "category": c.category,
            "is_active": c.is_active,
            "message_template": c.message_template,
            "wizebot_webhook_url": c.wizebot_webhook_url,
            "avec_report_url": c.avec_report_url,
            "extraction_offset_days": c.extraction_offset_days,
            "extraction_end_offset_days": c.extraction_end_offset_days,
            "schedule_slots": c.schedule_slots,
            "include_schedule_fields": c.include_schedule_fields,
            "test_name": c.test_name,
            "test_phone": c.test_phone,
            "test_date": c.test_date,
            "test_time": c.test_time,
            "last_sent": c.last_sent,
            "days_condition": c.days_condition,
            "last_run": c.last_run,
            "last_log": c.last_log,
            "next_sent": c.next_sent,
            "track_conversions": track_conversions,
            "sent_count": sent_count,
            "converted_count": converted_count,
            "conversion_rate": conversion_rate,
            "revenue_recovered": revenue_recovered
        }
        result.append(c_dict)
    return result

@app.post("/api/campaigns/{campaign_id}/toggle")
def toggle_campaign(campaign_id: int, toggle: CampaignToggle, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.is_active = toggle.is_active
    db.commit()
    return {"status": "success", "is_active": campaign.is_active}

@app.get("/api/campaigns/{id}/logs")
def get_campaign_logs(id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
        
    base_log = campaign.last_log or "Nenhum log disponível."
    
    # Adiciona lista de convertidos nos logs
    if id in (1, 5, 6, 7, 8, 9):
        conversions = db.query(models.Log).filter(
            models.Log.campaign_id == id,
            models.Log.conversion_status == 'CONVERTED'
        ).order_by(models.Log.converted_at.desc()).all()
        
        if conversions:
            from datetime import timezone
            from zoneinfo import ZoneInfo
            
            conv_lines = ["\n\n=== RETORNOS CONFIRMADOS (CONVERSÕES) ==="]
            for c in conversions:
                try:
                    utc_dt = c.created_at.replace(tzinfo=timezone.utc)
                    local_dt = utc_dt.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    local_dt = c.created_at.strftime("%d/%m/%Y %H:%M") if c.created_at else "N/A"
                    
                date_booked = c.conversion_appointment_date or "N/A"
                conv_lines.append(f"- {c.client_name} ({c.client_phone}): Agendou para {date_booked} (Notificado em {local_dt})")
            base_log += "\n".join(conv_lines)
            
    return {"status": "success", "log": base_log}

@app.post("/api/conversions/refresh")
def refresh_conversions(db: Session = Depends(get_db)):
    def run_check():
        from backend.jobs.scheduler import check_campaign_conversions
        check_campaign_conversions()
        
    threading.Thread(target=run_check, daemon=True).start()
    return {"message": "Atualização das conversões iniciada em background."}

@app.get("/api/campaigns/{campaign_id}/conversions")
def get_campaign_conversions(campaign_id: int, db: Session = Depends(get_db)):
    conversions = db.query(models.Log).filter(
        models.Log.campaign_id == campaign_id,
        models.Log.conversion_status == 'CONVERTED'
    ).order_by(models.Log.converted_at.desc()).all()
    
    return [
        {
            "client_name": c.client_name,
            "client_phone": c.client_phone,
            "created_at": c.created_at,
            "converted_at": c.converted_at,
            "conversion_appointment_date": c.conversion_appointment_date,
            "conversion_value": c.conversion_value
        } for c in conversions
    ]

@app.post("/api/campaigns/{campaign_id}/config")
def config_campaign(campaign_id: int, config: CampaignConfig, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.wizebot_webhook_url = config.wizebot_webhook_url
    campaign.avec_report_url = config.avec_report_url
    db.commit()
    return {"status": "success"}

@app.post("/api/campaigns/{campaign_id}/test-data")
def update_test_data(campaign_id: int, config: TestDataUpdate, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.test_name = config.test_name
    campaign.test_phone = config.test_phone
    campaign.test_date = config.test_date
    campaign.test_time = config.test_time
    db.commit()
    return {"status": "success"}

@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(models.Settings).first()
    if not settings:
        settings = models.Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.post("/api/settings")
def update_settings(settings_update: SettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(models.Settings).first()
    if not settings:
        settings = models.Settings()
        db.add(settings)
    
    settings.avec_username = settings_update.avec_username
    settings.avec_password = settings_update.avec_password
    settings.avec_salon_id = settings_update.avec_salon_id
    
    db.commit()
    return {"status": "success"}

@app.post("/api/fetch-data")
def fetch_data():
    def run_all_now():
        run_campaigns(is_dry_run=True)
        
    threading.Thread(target=run_all_now, daemon=True).start()
    return {"message": "Extração simulada (Dry Run) iniciada em background."}

@app.post("/api/trigger-all")
def trigger_all():
    def run_all_now():
        run_campaigns(is_dry_run=False)
        
    threading.Thread(target=run_all_now, daemon=True).start()
    return {"message": "Disparo real iniciado em background."}

@app.post("/api/campaigns/{campaign_id}/test")
def test_campaign_manual(campaign_id: int, payload: CampaignTestPayload, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    if not campaign.wizebot_webhook_url:
        raise HTTPException(status_code=400, detail="URL do Webhook não configurada nesta campanha.")
        
    # Limpa caracteres e adiciona 55 se necessário
    phone = re.sub(r'\D', '', payload.telefone)
    if not phone.startswith('55') and len(phone) >= 10:
        phone = '55' + phone
        
    webhook_sender = WebhookSender(campaign.wizebot_webhook_url)
    nome_primeiro = payload.nome.split()[0] if payload.nome else ""
    client_data = {
        "nome": nome_primeiro,
        "telefone": phone
    }
    
    if campaign.include_schedule_fields:
        from backend.engine.normalizer import Normalizer
        raw_date = payload.avecreserva or ""
        raw_time = payload.avechorario or ""
        
        data_reserva = Normalizer.normalize_date_str(raw_date)
        hora_reserva = Normalizer.normalize_time_str(raw_time)
        
        client_data["avecreserva"] = data_reserva
        client_data["avechorario"] = hora_reserva
        
        import urllib.parse
        from datetime import datetime, timedelta
        
        try:
            dt = datetime.strptime(f"{data_reserva} {hora_reserva}", "%d/%m/%Y %H:%M")
        except Exception:
            # Fallback robusto caso ocorra algum erro inesperado de parsing
            dt = datetime.strptime(f"{datetime.now().strftime('%d/%m/%Y')} 18:00", "%d/%m/%Y %H:%M")
            data_reserva = dt.strftime("%d/%m/%Y")
            hora_reserva = dt.strftime("%H:%M")
            client_data["avecreserva"] = data_reserva
            client_data["avechorario"] = hora_reserva
        
        try:
            dt_end = dt + timedelta(hours=1)
            fmt_start = dt.strftime("%Y%m%dT%H%M00")
            fmt_end = dt_end.strftime("%Y%m%dT%H%M00")
            title = "Lembrete: seu horário na Barbearia Tarantino."
            details = ""
            location = "Barbearia Tarantino"
            params = {"action": "TEMPLATE", "text": title, "dates": f"{fmt_start}/{fmt_end}", "details": details, "location": location}
            client_data["linkgoogleagenda"] = f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
        except Exception as e:
            print("Erro Google Calendar Test:", e)
                
    import json
    print(f"Payload enviado para Wizebot no teste: {json.dumps(client_data)}")
        
    success, msg = webhook_sender.send_client(client_data)
    
    if success:
        return {"status": "success", "message": "Enviado com sucesso!"}
    else:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar: {msg}")

# Serve Frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# Init default data
def init_db():
    db = next(get_db())
    if db.query(models.Campaign).count() == 0:
        default_campaigns = [
            # Relacionamento → roda às 08h
            models.Campaign(name="Clientes aniversariantes",     category="Relacionamento", message_template="Parabéns pelo seu dia!",       extraction_offset_days=7,    schedule_slots="08"),
            models.Campaign(name="Boas Vindas - Clientes novos",  category="Relacionamento", message_template="Bem-vindo ao salão!",          extraction_offset_days=0,   schedule_slots="08,09,10,11,12,13,14,15,16,17,18,19,20,21"),
            # Confirmação do dia → 08h e 12h (agenda de HOJE)
            models.Campaign(name="Confirmação de Horário - Hoje",   category="Relacionamento", message_template="Lembrete: você tem horário hoje!", extraction_offset_days=0, schedule_slots="08,12", include_schedule_fields=True),
            # Confirmação do próximo dia → 18h (agenda de AMANHÃ)
            models.Campaign(name="Confirmação de Horário - Amanhã", category="Relacionamento", message_template="Lembrete: amanhã você tem horário marcado!", extraction_offset_days=1, schedule_slots="18", include_schedule_fields=True),
            # Reserva nova → 08 às 22h (busca por período de Hoje a Hoje+30)
            models.Campaign(
                name="Confirmação de Reserva", 
                category="Relacionamento", 
                message_template="Lembrete: seu horário na Tarantino.", 
                extraction_offset_days=0, 
                extraction_end_offset_days=30,
                schedule_slots="08,09,10,11,12,13,14,15,16,17,18,19,20,21,22", 
                include_schedule_fields=True
            ),
            # Recuperação → roda às 08h
            models.Campaign(name="Lembrete de 30 dias sem ir ao salão", category="Recuperação", message_template="Sentimos sua falta!",         extraction_offset_days=-25,  schedule_slots="08"),
            models.Campaign(name="Risco - 45 dias",                    category="Recuperação", message_template="Volte logo!",                  extraction_offset_days=-45,  schedule_slots="08"),
            models.Campaign(name="Alerta - 60 dias",                   category="Recuperação", message_template="Temos uma oferta para você!",  extraction_offset_days=-60,  schedule_slots="08"),
            models.Campaign(name="Urgente - 90 dias",                  category="Recuperação", message_template="Ainda lembra de nós?",          extraction_offset_days=-90,  schedule_slots="08"),
            models.Campaign(name="Perdido - 180 dias",                 category="Recuperação", message_template="Queremos você de volta!",       extraction_offset_days=-180, schedule_slots="08"),
        ]
        db.add_all(default_campaigns)
        db.commit()

init_db()
