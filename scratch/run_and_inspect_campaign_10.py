import os
import sys
import sqlite3
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.jobs.scheduler import run_campaigns

def main():
    conn = sqlite3.connect('tigerone.db')
    cursor = conn.cursor()
    
    # Ativa temporariamente a campanha 10 e desativa as outras para o teste
    cursor.execute("SELECT id, is_active FROM campaigns")
    original_states = cursor.fetchall()
    
    cursor.execute("UPDATE campaigns SET is_active = 0")
    cursor.execute("UPDATE campaigns SET is_active = 1 WHERE id = 10")
    conn.commit()
    
    try:
        print("Executando extração para a campanha 10...")
        run_campaigns(is_dry_run=True)
        
        # Lê o log gerado
        cursor.execute("SELECT last_log FROM campaigns WHERE id = 10")
        log = cursor.fetchone()[0]
        print("\n=== NOVO LOG DA CAMPANHA 10 NO BANCO ===")
        print(log)
        
        # Verifica se Hideki Suekawa está na lista
        if "Hideki" in log:
            print("\nAVISO: Hideki Suekawa foi incluído no log!")
        else:
            print("\nSUCESSO: Hideki Suekawa NÃO está no log (foi filtrado corretamente porque o horário de 19h já passou).")
            
    finally:
        # Restaura estados
        for cid, state in original_states:
            cursor.execute("UPDATE campaigns SET is_active = ? WHERE id = ?", (state, cid))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    main()
