from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.models import Campaign, Settings, Log
from backend.extractor.avec_client import AvecClient
from backend.engine.normalizer import Normalizer
from backend.engine.webhook import WebhookSender
import re as _re
import urllib.parse

scheduler = BackgroundScheduler()

def already_notified_for_appointment(db, campaign_id, client_phone, appointment_date=None):
    """Verifica se o cliente já foi notificado para esta campanha e data de reserva específica."""
    query = db.query(Log).filter(
        Log.campaign_id == campaign_id,
        Log.client_phone == client_phone,
        Log.status == "SUCCESS"
    )
    
    if appointment_date:
        # Se tiver data de agendamento (ex: Confirmação de Reserva), verifica se JÁ FOI ENVIADO ALGUMA VEZ pra essa reserva
        query = query.filter(Log.appointment_date == appointment_date)
    else:
        # Se for campanha diária sem data específica (ex: Aniversariantes), verifica se já enviou HOJE
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Log.created_at >= today_start)
        
    return query.first() is not None

def run_campaigns(slot_hour=None, is_dry_run=False):
    """
    Executa as campanhas ativas.
    slot_hour: hora atual (int) para filtrar campanhas pelo schedule_slots.
               Se None, roda todas as campanhas ativas.
    is_dry_run: se True, roda modo simulação sem enviar webhook ou salvar no DB.
    """
    print(f"[{datetime.now()}] Iniciando verificação de campanhas (slot={slot_hour}h)...")
    db = SessionLocal()
    try:
        settings = db.query(Settings).first()
        if not settings or not settings.avec_username or not settings.avec_password:
            print("Credenciais da Avec não preenchidas. Abortando.")
            return

        avec_client = AvecClient(settings.avec_username, settings.avec_password)
        active_campaigns = db.query(Campaign).filter(Campaign.is_active == True).all()

        for campaign in active_campaigns:
            # Filtra pelo slot de horário configurado da campanha
            if slot_hour is not None:
                slots = [int(s.strip()) for s in (campaign.schedule_slots or "08").split(",")]
                if int(slot_hour) not in slots:
                    continue

            log_messages = []
            try:
                msg_iniciando = f"Processando campanha: {campaign.name}" + (" (SIMULAÇÃO/DRY RUN)" if is_dry_run else "")
                print(msg_iniciando)
                log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando campanha: {campaign.name}" + (" [MODO SIMULAÇÃO]" if is_dry_run else ""))

                if not campaign.avec_report_url:
                    log_messages.append("Erro: URL do relatório da Avec não configurada.")
                    campaign.last_log = "\n".join(log_messages)
                    db.commit()
                    continue
                    
                if not is_dry_run and not campaign.wizebot_webhook_url:
                    log_messages.append("Erro: URL do Webhook não configurada para disparo real.")
                    campaign.last_log = "\n".join(log_messages)
                    db.commit()
                    continue

                target_date = datetime.now() + timedelta(days=campaign.extraction_offset_days)
                start_date = target_date.strftime("%d/%m/%Y")
                
                if getattr(campaign, 'extraction_end_offset_days', None) is not None:
                    end_target_date = datetime.now() + timedelta(days=campaign.extraction_end_offset_days)
                    end_date = end_target_date.strftime("%d/%m/%Y")
                    date_str = f"{start_date} até {end_date}"
                else:
                    end_date = start_date
                    date_str = start_date
                    
                log_messages.append(f"Data base do filtro: {date_str}")

                # Monta URL visual e URL de API separadas
                raw_url = campaign.avec_report_url
                salon_id = settings.avec_salon_id or "4053"

                if "/admin/relatorio/" in raw_url and "listar?" not in raw_url:
                    relatorio_id = raw_url.rstrip("/").split("/")[-1]
                    visual_url = raw_url
                    api_url = f"https://admin.avec.beauty/admin/relatorios/listar?relatorio={relatorio_id}&salao={salon_id}"
                    
                    # Hack para relatórios exigentes: O 0051 precisa desses parâmetros vazios para não retornar erro/vazio
                    if relatorio_id == "0051":
                        api_url += "&site=&profissional_id="
                else:
                    m = _re.search(r'relatorio=(\w+)', raw_url)
                    relatorio_id = m.group(1) if m else ""
                    visual_url = f"https://admin.avec.beauty/admin/relatorio/{relatorio_id}"
                    api_url = raw_url

                dias_val = None
                target_days = None
                if relatorio_id == "0107":
                    dias_val = max(90, abs(campaign.extraction_offset_days))
                    target_days = abs(campaign.extraction_offset_days)

                aadata = avec_client.fetch_report(visual_url, api_url, start_date, end_date, dias=dias_val)

                if not aadata:
                    log_messages.append(f"Nenhum dado retornado da Avec para a data {date_str} (sem registros ou URL inválida).")
                    campaign.last_log = "\n".join(log_messages)
                    db.commit()
                    continue

                # Normaliza detectando nome, telefone, e opcionalmente data/hora de reserva
                normalized_clients = Normalizer.process_report_data(
                    aadata,
                    include_schedule_fields=campaign.include_schedule_fields,
                    target_days=target_days
                )

                # Deduplicação: manter apenas 1 registro por Cliente + Data de Reserva
                unique_clients = []
                seen_keys = set()
                for c in normalized_clients:
                    phone = c["telefone"]
                    date = c.get("avecreserva", "")
                    key = f"{phone}_{date}"
                    if key not in seen_keys:
                        seen_keys.add(key)
                        unique_clients.append(c)
                
                normalized_clients = unique_clients

                log_messages.append(f"Extraídos {len(normalized_clients)} registros únicos da Avec.")

                webhook_sender = WebhookSender(campaign.wizebot_webhook_url)
                sent_count = 0
                skipped_count = 0
                detalhes_linhas = []

                for client in normalized_clients:
                    telefone_real = client["telefone"]
                    data_reserva_check = client.get("avecreserva", "") if campaign.include_schedule_fields else None
                    
                    # ✅ Anti-duplicata: pula se já foi notificado (para a reserva ou hoje)
                    if already_notified_for_appointment(db, campaign.id, telefone_real, data_reserva_check):
                        skipped_count += 1
                        detalhes_linhas.append(f"  - {client['nome']} ({telefone_real}) [PULADO: Já notificado]")
                        continue

                    # Pula se o agendamento for anterior ao momento atual (passado)
                    if campaign.include_schedule_fields:
                        raw_date = client.get("avecreserva", "")
                        raw_time = client.get("avechorario", "")
                        data_reserva = Normalizer.normalize_date_str(raw_date)
                        hora_reserva = Normalizer.normalize_time_str(raw_time)
                        if data_reserva and hora_reserva:
                            try:
                                dt = datetime.strptime(f"{data_reserva} {hora_reserva}", "%d/%m/%Y %H:%M")
                                if dt < datetime.now():
                                    skipped_count += 1
                                    detalhes_linhas.append(f"  - {client['nome']} ({telefone_real}) [PULADO: Horário passado - {data_reserva} {hora_reserva}]")
                                    continue
                            except Exception as e:
                                print(f"Erro ao verificar se agendamento e no passado: {repr(e)}")

                    # Pula se a origem for Aplicativo Avec ou Aplicativo Personalizado (apenas na Confirmação de Reserva)
                    if campaign.id == 10 or campaign.name == "Confirmação de Reserva":
                        origem = client.get("origem", "").strip().lower()
                        if "aplicativo avec" in origem or "aplicativo personalizado" in origem:
                            skipped_count += 1
                            detalhes_linhas.append(f"  - {client['nome']} ({telefone_real}) [PULADO: Origem {client.get('origem')}]")
                            continue

                    # No job scheduler / disparo em lote, sempre usamos os dados do cliente real.
                    # Os campos de teste são exclusivos para o botão "TESTAR" do painel.
                    nome_completo = client["nome"]
                    nome_final = nome_completo.split()[0] if nome_completo else ""
                    telefone_final = telefone_real

                    # Monta payload base
                    payload = {
                        "nome": nome_final,
                        "telefone": telefone_final
                    }

                    # Campos extras de agendamento (relatório 0051)
                    if campaign.include_schedule_fields:
                        raw_date = client.get("avecreserva", "")
                        raw_time = client.get("avechorario", "")
                        
                        data_reserva = Normalizer.normalize_date_str(raw_date)
                        hora_reserva = Normalizer.normalize_time_str(raw_time)
                        
                        payload["avecreserva"] = data_reserva
                        payload["avechorario"] = hora_reserva
                        
                        if data_reserva and hora_reserva:
                            try:
                                dt = datetime.strptime(f"{data_reserva} {hora_reserva}", "%d/%m/%Y %H:%M")
                            except Exception:
                                # Fallback robusto caso ocorra algum erro inesperado de parsing
                                dt = datetime.strptime(f"{datetime.now().strftime('%d/%m/%Y')} 18:00", "%d/%m/%Y %H:%M")
                                data_reserva = dt.strftime("%d/%m/%Y")
                                hora_reserva = dt.strftime("%H:%M")
                                payload["avecreserva"] = data_reserva
                                payload["avechorario"] = hora_reserva
                                
                            try:
                                dt_end = dt + timedelta(hours=1)
                                fmt_start = dt.strftime("%Y%m%dT%H%M00")
                                fmt_end = dt_end.strftime("%Y%m%dT%H%M00")
                                
                                title = "Lembrete: seu horário na Barbearia Tarantino."
                                details = ""
                                location = "Barbearia Tarantino"
                                
                                params = {
                                    "action": "TEMPLATE",
                                    "text": title,
                                    "dates": f"{fmt_start}/{fmt_end}",
                                    "details": details,
                                    "location": location
                                }
                                qs = urllib.parse.urlencode(params)
                                payload["linkgoogleagenda"] = f"https://calendar.google.com/calendar/render?{qs}"
                            except Exception as e:
                                print(f"Erro ao gerar link do google agenda: {e}")

                    if is_dry_run:
                        # Modo simulação: não dispara webhook nem salva log no BD para não bloquear o envio real
                        success = True
                        msg = "Simulado com sucesso"
                    else:
                        # Envio real
                        success, msg = webhook_sender.send_client(payload)

                        # Registra no log de auditoria apenas se não for simulação
                        log = Log(
                            campaign_id=campaign.id,
                            client_name=client["nome"],
                            client_phone=telefone_real,
                            appointment_date=data_reserva_check,
                            status="SUCCESS" if success else "ERROR",
                            error_message=msg if not success else None
                        )
                        db.add(log)

                    if success:
                        sent_count += 1
                        status_label = "[SIMULADO]" if is_dry_run else "[ENVIADO]"
                        detalhes_linhas.append(f"  - {client['nome']} ({telefone_real}) {status_label}")
                    else:
                        detalhes_linhas.append(f"  - {client['nome']} ({telefone_real}) [ERRO: {msg}]")

                # Calcula próximo disparo
                slots = [int(s.strip()) for s in (campaign.schedule_slots or "08").split(",")]
                current_hour = datetime.now().hour
                next_slots = sorted([h for h in slots if h > current_hour])
                if next_slots:
                    proximo_disparo = datetime.now().replace(hour=next_slots[0], minute=0, second=0, microsecond=0)
                else:
                    proximo_disparo = (datetime.now() + timedelta(days=1)).replace(hour=slots[0], minute=0, second=0, microsecond=0)

                campaign.next_sent = proximo_disparo

                detalhes = "\n".join(detalhes_linhas)
                
                status_envio_txt = f"Simulados (Não enviados): {sent_count}" if is_dry_run else f"Enviados reais: {sent_count}"
                
                log_msg = (
                    f"[{datetime.now().strftime('%H:%M:%S')}] Campanha: {campaign.name}\n"
                    f"Data base do filtro: {date_str}\n"
                    f"Extraídos {len(normalized_clients)} registros.\n"
                    f"Lista:\n{detalhes}\n\n"
                    f"{status_envio_txt} | Ignorados (já notificados hoje): {skipped_count}\n"
                    f"Próximo disparo: {proximo_disparo.strftime('%d/%m/%Y %H:%M')}"
                )

                campaign.last_log = log_msg
                campaign.last_sent = datetime.now()
                db.commit()

            except Exception as e:
                error_msg = f"Erro no job: {repr(e)}"
                print(error_msg)
                log_messages.append(error_msg)
                campaign.last_log = "\n".join(log_messages)
                db.commit()

    except Exception as e:
        print(f"Erro geral no scheduler: {repr(e)}")
    finally:
        db.close()

def start_scheduler():
    # Roda a cada hora redonda (08:00, 09:00, ..., 22:00)
    for h in range(8, 23):
        scheduler.add_job(run_campaigns, 'cron', hour=h, minute=0, kwargs={"slot_hour": h})
        
    scheduler.start()
