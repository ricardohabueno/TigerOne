import os
import sys
import sqlite3

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.jobs.scheduler import run_campaigns

def main():
    conn = sqlite3.connect('tigerone.db')
    cursor = conn.cursor()
    
    # Salva os estados atuais de is_active das campanhas
    cursor.execute("SELECT id, is_active FROM campaigns")
    original_states = cursor.fetchall()
    
    print("Salvou os estados originais das campanhas.")
    
    # Ativa apenas a campanha 5 (Lembrete de 30 dias) e desativa as outras
    cursor.execute("UPDATE campaigns SET is_active = 0")
    cursor.execute("UPDATE campaigns SET is_active = 1 WHERE id = 5")
    conn.commit()
    print("Campanha 5 ativada temporariamente. Outras desativadas.")
    
    try:
        print("\n--- Executando run_campaigns(is_dry_run=True) ---")
        run_campaigns(is_dry_run=True)
        print("Execução concluída.")
        
        # Busca o log da campanha 5
        cursor.execute("SELECT last_log FROM campaigns WHERE id = 5")
        last_log = cursor.fetchone()[0]
        print("\n=== LOG DA CAMPANHA 5 NO BANCO ===")
        print(last_log)
        
    finally:
        # Restaura os estados originais
        for cid, state in original_states:
            cursor.execute("UPDATE campaigns SET is_active = ? WHERE id = ?", (state, cid))
        conn.commit()
        conn.close()
        print("\nEstados originais das campanhas restaurados.")

if __name__ == "__main__":
    main()
