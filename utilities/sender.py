# File: utilities/sender.py
import requests

# === Webhooks por categoría ===
DISCORD_WEBHOOK_URL_INVESTING = "https://discord.com/api/webhooks/1428423347296796688/a6rfCu8z_tFrAYvpR-KfBfQ1BXbE7OEWIsYCNUSZNN4cGplTRE7XKvShwedk9ib3O-gJ"
DISCORD_WEBHOOK_URL_HOME = "https://discord.com/api/webhooks/1428426560188186664/fXHKNfrK1Ph6d4uknPPWSZ5T9tMho6h_03AEjU7TG6PaAEUxwt2qmLi5WTTHFgA06WtP"

def send_discord_message(webhook_url: str, content: str, send: bool = True):
    data = {"content": content}

    try:
        response = requests.post(webhook_url, json=data)
        """
        if response.status_code not in (200, 204):
            print(f"❌ Error al enviar mensaje ({response.status_code}): {response.text}")
        else:
            print("✅ Mensaje enviado a Discord correctamente.")
        """    
    except Exception as e:
        print(f"❌ Excepción al enviar mensaje: {e}")
