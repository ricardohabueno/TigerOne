import requests
import json

DRY_RUN = False # Disparo real habilitado

class WebhookSender:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_client(self, client_data):
        if not self.webhook_url:
            return False, "Webhook URL not configured"
            
        if DRY_RUN:
            print(f"[DRY RUN] Simulando envio POST para {self.webhook_url}")
            print(f"[DRY RUN] Payload: {json.dumps(client_data, indent=2, ensure_ascii=False)}")
            return True, "DRY_RUN_SUCCESS"

        try:
            response = requests.post(
                self.webhook_url,
                json=client_data,
                timeout=10
            )
            if response.status_code in [200, 201, 204]:
                return True, "SUCCESS"
            else:
                return False, f"Failed with status: {response.status_code}"
        except Exception as e:
            return False, str(e)
