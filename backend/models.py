from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String) # Relacionamento, Recuperação, Marketing
    is_active = Column(Boolean, default=False)
    message_template = Column(Text, nullable=True)
    wizebot_webhook_url = Column(String, nullable=True)
    avec_report_url = Column(String, nullable=True)
    extraction_offset_days = Column(Integer, default=0)
    extraction_end_offset_days = Column(Integer, nullable=True)
    # Slots de horário que esta campanha deve rodar (ex: "08,12" ou "18" ou "08")
    schedule_slots = Column(String, default="08")
    # Se True, o payload inclui avecreserva e avechorario além de nome/telefone
    include_schedule_fields = Column(Boolean, default=False)
    test_name = Column(String, nullable=True)
    test_phone = Column(String, nullable=True)
    test_date = Column(String, nullable=True)
    test_time = Column(String, nullable=True)
    last_sent = Column(DateTime, nullable=True)
    days_condition = Column(String, nullable=True)
    last_run = Column(DateTime, nullable=True)
    last_log = Column(String, nullable=True)
    next_sent = Column(DateTime, nullable=True)
    
    logs = relationship("Log", back_populates="campaign")

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    avec_username = Column(String, nullable=True)
    avec_password = Column(String, nullable=True)
    avec_salon_id = Column(String, nullable=True)

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    client_name = Column(String)
    client_phone = Column(String)
    appointment_date = Column(String, nullable=True)
    status = Column(String) # SUCCESS / ERROR, SKIPPED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="logs")
