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
    
    if not settings or not settings.avec_username or not settings.avec_password:
        print("Credenciais da Avec não encontradas.")
        return
        
    print("Iniciando Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        # Monitora requisições de rede
        def log_request(request):
            if "listar" in request.url or "relatorios" in request.url:
                print(f"[REQ] {request.method} {request.url}")
                if request.post_data:
                    print(f"  Post Data: {request.post_data}")
                
        def log_response(response):
            if "listar" in response.url or "relatorios" in response.url:
                print(f"[RESP] {response.status} {response.url}")
                try:
                    text = response.text()
                    print(f"  Content length: {len(text)}")
                    print(f"  Content snippet: {text[:200]}")
                except Exception as e:
                    print(f"  Error reading text: {e}")
                    
        page.on("request", log_request)
        page.on("response", log_response)
        
        print("Fazendo login no Avec...")
        page.goto("https://admin.avec.beauty/tarantino/admin")
        page.wait_for_selector('input[type="email"]', timeout=15000)
        page.fill('input[type="email"]', settings.avec_username)
        page.fill('input[type="password"]', settings.avec_password)
        page.click('button[data-testid="submit-button"]')
        page.wait_for_timeout(10000)
        
        print("Navegando para o relatório 0107...")
        # Nós usamos wait_until='networkidle' para podermos capturar a requisição ajax que carrega a tabela
        page.goto("https://admin.avec.beauty/admin/relatorio/0107", wait_until='load', timeout=60000)
        
        print("Aguardando carregamento da tabela...")
        page.wait_for_timeout(20000)
        
        browser.close()

if __name__ == "__main__":
    main()
