import os
import sys
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
        
        visual_url = "https://admin.avec.beauty/admin/relatorio/0051"
        api_url = f"https://admin.avec.beauty/admin/relatorios/listar?relatorio=0051&salao=4053&site=&profissional_id=&inicio=28%2F05%2F2026&fim=29%2F05%2F2026"
        
        page.goto(visual_url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(3000)
        
        response = context.request.get(api_url, headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}, timeout=60000)
        if response.ok:
            rows = response.json().get("aaData", [])
            print(f"Total rows: {len(rows)}")
            import re
            for idx, row in enumerate(rows[:30]):
                clean_row = [re.sub(r'<[^>]*>', '', str(val)).strip() if val is not None else None for val in row]
                print(f"Row {idx}: {clean_row}")
        else:
            print("Failed to fetch")
        browser.close()

if __name__ == "__main__":
    main()
