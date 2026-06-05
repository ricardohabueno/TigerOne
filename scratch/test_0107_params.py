import sys
import os
from playwright.sync_api import sync_playwright

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import SessionLocal
from backend.models import Settings

def test_api_with_days(dias_val):
    db = SessionLocal()
    settings = db.query(Settings).first()
    db.close()
    
    if not settings:
        print("Settings not found.")
        return
        
    print(f"\n--- Testando 0107 com dias={dias_val} ---")
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
        
        # Navigate to visual page to set cookies
        try:
            page.goto("https://admin.avec.beauty/admin/relatorio/0107", wait_until='load', timeout=60000)
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Erro na navegação visual: {e}")
            
        # Call the API directly using context.request
        api_url = f"https://admin.avec.beauty/admin/relatorios/listar?relatorio=0107&salao={settings.avec_salon_id or '4053'}&dias={dias_val}"
        print(f"Fazendo request API: {api_url}")
        
        response = context.request.get(
            api_url,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json"
            },
            timeout=30000
        )
        print(f"Status da resposta: {response.status}")
        if response.ok:
            try:
                data = response.json()
                rows = data.get("aaData", [])
                print(f"Sucesso! Retornou {len(rows)} linhas.")
                if rows:
                    print(f"Exemplo de linha: {rows[0]}")
            except Exception as e:
                print(f"Erro parseando JSON: {e}")
                print(f"Snippet: {response.text()[:200]}")
        else:
            print(f"Falhou! Status: {response.status} {response.status_text}")
            print(f"Resposta: {response.text()[:500]}")
            
        browser.close()

if __name__ == "__main__":
    test_api_with_days(90)
    test_api_with_days(30)
    test_api_with_days(25)
