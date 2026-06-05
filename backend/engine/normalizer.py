import re
from datetime import datetime

class Normalizer:
    @staticmethod
    def _is_phone(value):
        """Verifica se o valor parece um telefone brasileiro válido (10 ou 11 dígitos)."""
        cleaned = re.sub(r'\D', '', str(value))
        return len(cleaned) in (10, 11)

    @staticmethod
    def _is_name(value):
        """Verifica se o valor parece um nome de pessoa."""
        v = str(value).strip()
        if len(v) < 3:
            return False
        # Não pode ser data (DD/MM/YYYY)
        if re.match(r'^\d{2}[\/\-]\d{2}[\/\-]\d{2,4}$', v):
            return False
        # Não pode ser hora (HH:MM)
        if re.match(r'^\d{2}:\d{2}$', v):
            return False
        # Não pode ser só números
        if re.match(r'^\d+$', v):
            return False
        # Deve conter pelo menos uma letra
        if not re.search(r'[A-Za-zÀ-ÿ]', v):
            return False
        # Não pode ser e-mail
        if '@' in v:
            return False
        return True

    @staticmethod
    def _is_date(value):
        """Verifica se o valor é uma data no formato DD/MM/YYYY ou semelhante."""
        v = str(value).strip()
        return bool(re.match(r'^\d{2}[\/\-]\d{2}[\/\-]\d{2,4}$', v))

    @staticmethod
    def _is_time(value):
        """Verifica se o valor é um horário no formato HH:MM ou HH:MM:SS."""
        v = str(value).strip()
        return bool(re.match(r'^\d{2}:\d{2}(:\d{2})?$', v))

    @staticmethod
    def normalize_date_str(date_str):
        if not date_str:
            return datetime.now().strftime("%d/%m/%Y")
        
        # Remove caracteres que não sejam dígitos ou / ou -
        cleaned = re.sub(r'[^0-9/\-]', '', str(date_str)).strip()
        cleaned = cleaned.replace('-', '/')
        
        # Tenta interpretar formatos comuns
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                continue
                
        # Se contiver apenas dígitos, tenta deduzir
        digits = re.sub(r'\D', '', cleaned)
        if len(digits) == 8: # DDMMYYYY
            return f"{digits[0:2]}/{digits[2:4]}/{digits[4:8]}"
        elif len(digits) == 6: # DDMMYY
            return f"{digits[0:2]}/{digits[2:4]}/20{digits[4:6]}"
        elif len(digits) == 4: # DDMM
            return f"{digits[0:2]}/{digits[2:4]}/{datetime.now().year}"
        elif len(digits) == 2: # DD
            return f"{digits[0:2]}/{datetime.now().strftime('%m/%Y')}"
            
        # Fallback para hoje
        return datetime.now().strftime("%d/%m/%Y")

    @staticmethod
    def normalize_time_str(time_str):
        if not time_str:
            return "18:00"
            
        # Remove caracteres indesejados, mantendo dígitos, : e h
        cleaned = re.sub(r'[^0-9:hH]', '', str(time_str)).strip().lower()
        cleaned = cleaned.replace('h', ':')
        if cleaned.endswith(':'):
            cleaned = cleaned[:-1]
            
        # Tenta interpretar formatos comuns
        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.strftime("%H:%M")
            except ValueError:
                continue
                
        # Se contiver apenas dígitos, tenta deduzir
        digits = re.sub(r'\D', '', cleaned)
        if not digits:
            return "18:00"
            
        if len(digits) == 1:
            digits = "0" + digits + "00"
        elif len(digits) == 2:
            digits = digits + "00"
        elif len(digits) == 3:
            digits = "0" + digits
            
        if len(digits) >= 4:
            try:
                hh = int(digits[0:2])
                mm = int(digits[2:4])
                if hh >= 24:
                    hh = hh % 24
                if mm >= 60:
                    mm = mm % 60
                return f"{hh:02d}:{mm:02d}"
            except Exception:
                pass
            
        return "18:00"

    @staticmethod
    def normalize_aadata(aadata_row, include_schedule_fields=False):
        """
        Detecta automaticamente nome, telefone, data de reserva e horário
        varrendo todas as colunas. Funciona com qualquer relatório da Avec.
        """
        nome = None
        telefone_limpo = None
        dates_found = []   # índices e valores de todas as datas
        time_found = None
        time_index = None

        for i, col in enumerate(aadata_row):
            # Remove qualquer tag HTML que a Avec coloque dentro da coluna
            col_str = str(col)
            col_str = re.sub(r'<[^>]*>', '', col_str).strip()

            # Pula a linha inteira se o status for Cancelado
            if col_str.lower() in ("cancelado", "cancelada", "cancelados", "canceladas"):
                return None

            # Detecta hora (HH:MM)
            if time_found is None and Normalizer._is_time(col_str):
                time_found = col_str
                time_index = i
                continue

            # Detecta data (DD/MM/YYYY)
            if Normalizer._is_date(col_str):
                dates_found.append((i, col_str))
                continue

            # Detecta telefone
            if telefone_limpo is None and Normalizer._is_phone(col_str):
                telefone_limpo = re.sub(r'\D', '', col_str)
                continue

            # Detecta nome
            if nome is None and Normalizer._is_name(col_str):
                nome = col_str

        if not nome or not telefone_limpo:
            return None

        # Adiciona DDI 55 se necessário
        if len(telefone_limpo) in (10, 11):
            telefone_limpo = "55" + telefone_limpo

        result = {
            "nome": nome,
            "telefone": telefone_limpo
        }

        # Campos extras para relatório de agendamentos (0051)
        if include_schedule_fields:
            # A "Data Reserva" é a data imediatamente ANTES da coluna de hora
            # Se não houver hora, pega a última data encontrada
            avecreserva = None
            if dates_found:
                if time_index is not None:
                    # Pega a data cujo índice é mais próximo (antes) da hora
                    dates_before_time = [(i, d) for i, d in dates_found if i < time_index]
                    if dates_before_time:
                        avecreserva = dates_before_time[-1][1]  # última antes da hora
                    else:
                        avecreserva = dates_found[-1][1]
                else:
                    avecreserva = dates_found[-1][1]

            result["avecreserva"] = Normalizer.normalize_date_str(avecreserva or "")
            result["avechorario"] = Normalizer.normalize_time_str(time_found or "")

        # Extrai a origem da reserva (coluna index 9) se disponível
        if len(aadata_row) > 9:
            origem_str = str(aadata_row[9])
            origem_str = re.sub(r'<[^>]*>', '', origem_str).strip()
            result["origem"] = origem_str

        return result

    @staticmethod
    def process_report_data(aadata_list, include_schedule_fields=False, target_days=None):
        normalized_data = []
        for row in aadata_list:
            # Se target_days for definido, filtramos os clientes pela coluna de dias sem retorno (índice 4)
            if target_days is not None:
                if len(row) > 4:
                    import re
                    dias_val = str(row[4]).strip()
                    dias_val = re.sub(r'<[^>]*>', '', dias_val).strip()
                    if dias_val != str(target_days):
                        continue
                else:
                    continue

            norm = Normalizer.normalize_aadata(row, include_schedule_fields)
            if norm:
                normalized_data.append(norm)
        return normalized_data
