import sys
import os
from playwright.sync_api import sync_playwright

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import SessionLocal
from backend.models import Settings

def main():
    db = SessionLocal()
    settings = db.query(Settings).first()
    db.close()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        # Login
        page.goto("https://admin.avec.beauty/tarantino/admin")
        page.wait_for_selector('input[type="email"]')
        page.fill('input[type="email"]', settings.avec_username)
        page.fill('input[type="password"]', settings.avec_password)
        page.click('button[data-testid="submit-button"]')
        page.wait_for_timeout(10000)
        
        page.goto("https://admin.avec.beauty/admin/relatorio/0107", wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(3000)
        
        for d in [90, 30]:
            api_url = f"https://admin.avec.beauty/admin/relatorios/listar?relatorio=0107&salao=4053&dias={d}"
            response = context.request.get(
                api_url,
                headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
                timeout=60000
            )
            if response.ok:
                rows = response.json().get("aaData", [])
                days_list = []
                import re
                for row in rows:
                    if len(row) > 4:
                        val = row[4]
                        if val is not None:
                            val_str = re.sub(r'<[^>]*>', '', str(val)).strip()
                            if val_str.isdigit():
                                days_list.append(int(val_str))
                if days_list:
                    print(f"Com dias={d}: Total rows={len(rows)}, Min={min(days_list)}, Max={max(days_list)}, Unique values count={len(set(days_list))}")
                else:
                    print(f"Com dias={d}: Nenhum dia válido encontrado.")
            else:
                print(f"Falhou para dias={d}")
                
        browser.close()

if __name__ == "__main__":
    main()
