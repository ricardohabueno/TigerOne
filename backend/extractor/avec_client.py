import urllib.parse

class AvecClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        
    def fetch_report(self, visual_url, api_url, start_date, end_date, dias=None):
        """
        Realiza o fluxo de login e extração usando o Playwright End-to-End.
        
        visual_url: URL da tela visual amigável (ex: .../relatorio/0017)
                    Usada para navegar e garantir que o cookie PHP (ci_session) seja gerado.
        api_url:    URL da API de listagem com filtro de datas já montado
                    (ex: .../relatorios/listar?relatorio=0017&salao=4053&inicio=...&fim=...)
        dias:       Opcional. Se fornecido, usa o parâmetro 'dias' em vez de datas.
        """
        from playwright.sync_api import sync_playwright

        # Monta a URL final da API com os parâmetros correspondentes
        if dias is not None:
            params = {"dias": str(dias)}
        else:
            params = {"inicio": start_date, "fim": end_date}
            
        encoded = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        final_url = f"{api_url}&{encoded}" if "?" in api_url else f"{api_url}?{encoded}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()
            
            try:
                # 1. Login no painel React da Avec
                print("Fazendo login via Playwright...")
                page.goto("https://admin.avec.beauty/tarantino/admin")
                page.wait_for_selector('input[type="email"]', timeout=15000)
                page.fill('input[type="email"]', self.username)
                page.fill('input[type="password"]', self.password)
                page.click('button[data-testid="submit-button"]')
                
                # Aguarda o React sincronizar a sessão PHP legada
                page.wait_for_timeout(15000)
                print("Login concluído. Sincronizando sessão do sistema legado...")
                
                # 2. Navega até a tela VISUAL do relatório para gerar o cookie ci_session do PHP
                #    (ignora timeout, o cookie já é definido no início do carregamento)
                try:
                    page.goto(visual_url, wait_until='domcontentloaded', timeout=30000)
                except Exception as e:
                    print(f"Aviso: Timeout na tela visual do Avec (cookie já capturado). Detalhe: {e}")
                
                page.wait_for_timeout(3000)
                
                # 3. Busca o JSON da API usando o contexto autenticado (com os cookies já válidos)
                print(f"Buscando dados JSON na API: {final_url}")
                
                max_retries = 15
                import time
                for attempt in range(max_retries):
                    response = context.request.get(
                        final_url,
                        headers={
                            "X-Requested-With": "XMLHttpRequest",
                            "Accept": "application/json"
                        },
                        timeout=90000
                    )
                    if response.ok:
                        break
                        
                    print(f"Aviso: Tentativa {attempt + 1}/{max_retries} falhou com HTTP {response.status}. Retentando em 8s...")
                    time.sleep(8)
                
                if not response.ok:
                    raise Exception(f"Status HTTP: {response.status} - {response.status_text} (após {max_retries} tentativas)")
                    
                try:
                    json_data = response.json()
                except Exception as e:
                    print(f"Erro de parsing JSON. Resposta recebida:\n{response.text()[:500]}")
                    raise e
                
                print("Extração concluída com sucesso!")
                return json_data.get("aaData", [])
                
            except Exception as e:
                err_str = repr(e).encode('ascii', 'replace').decode('ascii')
                print(f"Erro na extração via Playwright: {err_str}")
                raise e
            finally:
                browser.close()
